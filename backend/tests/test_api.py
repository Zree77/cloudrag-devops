
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.llm import generate_answer


client = TestClient(app)


# --------------------------------------------------
# General API tests
# --------------------------------------------------

def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to CloudRAG"
    assert response.json()["docs"] == "/docs"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["application"] == "cloudrag"


# --------------------------------------------------
# Database readiness tests
# --------------------------------------------------

@patch("app.main.check_database_connection", return_value=True)
def test_readiness_endpoint(mock_database):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["application"] == "cloudrag"
    assert response.json()["database"] == "connected"


@patch("app.main.check_database_connection", return_value=False)
def test_readiness_endpoint_database_unavailable(mock_database):
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unavailable"


# --------------------------------------------------
# Chat input validation tests
# --------------------------------------------------

def test_chat_rejects_empty_question():
    response = client.post(
        "/chat/ask",
        json={"question": "   ", "limit": 4},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty."


def test_chat_rejects_missing_question():
    response = client.post(
        "/chat/ask",
        json={"limit": 4},
    )

    assert response.status_code == 422


# --------------------------------------------------
# RAG retrieval and answer generation tests
# --------------------------------------------------

@patch("app.llm.search_documents")
def test_generate_answer_returns_fallback_when_no_results(
    mock_search,
):
    mock_search.return_value = {
        "query": "What is the company's revenue?",
        "results": [],
    }

    result = generate_answer(
        question="What is the company's revenue?",
        limit=4,
    )

    assert result["question"] == "What is the company's revenue?"
    assert "couldn't find" in result["answer"].lower()
    assert result["sources"] == []
    assert result["model"] == "qwen3.5:2b"


@patch("app.llm.search_documents")
def test_generate_answer_filters_low_similarity_results(
    mock_search,
):
    mock_search.return_value = {
        "query": "What AWS services are mentioned?",
        "results": [
            {
                "filename": "resume.pdf",
                "chunk_index": 0,
                "content": "AWS EC2 and Amazon S3 are mentioned.",
                "similarity": 0.70,
            },
            {
                "filename": "resume.pdf",
                "chunk_index": 1,
                "content": "Unrelated content.",
                "similarity": 0.20,
            },
        ],
    }

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "message": {
            "content": "The resume mentions AWS EC2 and Amazon S3."
        }
    }

    with patch("app.llm.httpx.post", return_value=mock_response) as mock_post:
        result = generate_answer(
            question="What AWS services are mentioned?",
            limit=4,
        )

    assert result["answer"] == (
        "The resume mentions AWS EC2 and Amazon S3."
    )

    assert len(result["sources"]) == 1
    assert result["sources"][0]["chunk_index"] == 0
    assert result["sources"][0]["similarity"] == 0.70

    # Verify that the low-similarity passage was not sent to Ollama.
    payload = mock_post.call_args.kwargs["json"]
    user_message = payload["messages"][1]["content"]

    assert "AWS EC2 and Amazon S3 are mentioned." in user_message
    assert "Unrelated content." not in user_message


@patch("app.llm.search_documents")
def test_generate_answer_returns_fallback_when_all_results_are_weak(
    mock_search,
):
    mock_search.return_value = {
        "query": "What is the company's revenue?",
        "results": [
            {
                "filename": "resume.pdf",
                "chunk_index": 0,
                "content": "The candidate has AWS experience.",
                "similarity": 0.20,
            },
            {
                "filename": "resume.pdf",
                "chunk_index": 1,
                "content": "The candidate used Docker.",
                "similarity": 0.30,
            },
        ],
    }

    with patch("app.llm.httpx.post") as mock_post:
        result = generate_answer(
            question="What is the company's revenue?",
            limit=4,
        )

    assert "couldn't find" in result["answer"].lower()
    assert result["sources"] == []

    # Ollama should not be called when all passages are filtered out.
    mock_post.assert_not_called()


@patch("app.llm.search_documents")
def test_generate_answer_returns_sources(mock_search):
    mock_search.return_value = {
        "query": "What AWS services are mentioned?",
        "results": [
            {
                "filename": "resume.pdf",
                "chunk_index": 2,
                "content": "The project uses AWS EC2 and EKS.",
                "similarity": 0.65,
            },
        ],
    }

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "message": {
            "content": "The project uses AWS EC2 and EKS."
        }
    }

    with patch("app.llm.httpx.post", return_value=mock_response):
        result = generate_answer(
            question="What AWS services are mentioned?",
            limit=4,
        )

    assert result["answer"] == "The project uses AWS EC2 and EKS."
    assert result["model"] == "qwen3.5:2b"
    assert len(result["sources"]) == 1

    source = result["sources"][0]

    assert source["filename"] == "resume.pdf"
    assert source["chunk_index"] == 2
    assert source["similarity"] == 0.65


@patch("app.llm.search_documents")
def test_generate_answer_handles_ollama_failure(mock_search):
    mock_search.return_value = {
        "query": "What AWS services are mentioned?",
        "results": [
            {
                "filename": "resume.pdf",
                "chunk_index": 0,
                "content": "The project uses AWS EC2.",
                "similarity": 0.70,
            },
        ],
    }

    with patch(
        "app.llm.httpx.post",
        side_effect=Exception("Unexpected test failure"),
    ):
        with pytest.raises(Exception):
            generate_answer(
                question="What AWS services are mentioned?",
                limit=4,
            )


# --------------------------------------------------
# Chat endpoint integration tests
# --------------------------------------------------

@patch("app.main.generate_answer")
def test_chat_endpoint_returns_answer_and_sources(mock_generate):
    mock_generate.return_value = {
        "question": "What AWS services are mentioned?",
        "answer": "AWS EC2 and EKS are mentioned.",
        "model": "qwen3.5:2b",
        "sources": [
            {
                "filename": "resume.pdf",
                "chunk_index": 0,
                "similarity": 0.70,
            }
        ],
    }

    response = client.post(
        "/chat/ask",
        json={
            "question": "What AWS services are mentioned?",
            "limit": 4,
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == (
        "AWS EC2 and EKS are mentioned."
    )
    assert response.json()["model"] == "qwen3.5:2b"
    assert len(response.json()["sources"]) == 1

    mock_generate.assert_called_once_with(
        question="What AWS services are mentioned?",
        limit=4,
    )


@patch(
    "app.main.generate_answer",
    side_effect=RuntimeError("Ollama unavailable"),
)
def test_chat_endpoint_handles_generation_failure(mock_generate):
    response = client.post(
        "/chat/ask",
        json={
            "question": "What AWS services are mentioned?",
            "limit": 4,
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Could not generate an answer. Check the application logs."
    )
