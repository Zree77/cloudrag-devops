
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.database import check_database_connection
from app.ingestion import ingest_pdf
from app.search import search_documents
from app.llm import generate_answer


app = FastAPI(
    title="CloudRAG API",
    description=(
        "A Retrieval-Augmented Generation (RAG) application "
        "with AWS DevOps automation."
    ),
    version="0.2.0",
)


# --------------------------------------------------
# Request and response models
# --------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    application: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=4, ge=1, le=10)


# --------------------------------------------------
# General endpoints
# --------------------------------------------------

@app.get("/", tags=["General"])
def root():
    return {
        "message": "Welcome to CloudRAG",
        "docs": "/docs",
        "version": app.version,
    }


# --------------------------------------------------
# Health and readiness endpoints
# --------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
)
def health():
    """Check whether the API process is responding."""

    return HealthResponse(
        status="healthy",
        application="cloudrag",
    )


@app.get("/ready", tags=["Health"])
def readiness():
    """Check whether the API can access PostgreSQL."""

    if not check_database_connection():
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        )

    return {
        "status": "ready",
        "application": "cloudrag",
        "database": "connected",
    }


# --------------------------------------------------
# Document upload and ingestion
# --------------------------------------------------

@app.post("/documents/upload", tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, extract its text, generate embeddings,
    and store the document and chunks in PostgreSQL.
    """

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    try:
        file_bytes = await file.read()

        result = ingest_pdf(
            filename=file.filename,
            content_type=file.content_type or "application/pdf",
            file_bytes=file_bytes,
        )

        return {
            "message": "Document processed successfully.",
            **result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print(
            f"Document ingestion failed: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Document processing failed. "
                "Check the application logs."
            ),
        ) from exc

    finally:
        await file.close()


# --------------------------------------------------
# Semantic document search
# --------------------------------------------------

@app.post("/documents/search", tags=["Documents"])
def search_uploaded_documents(request: SearchRequest):
    """
    Search uploaded documents using vector similarity.
    Returns the most relevant text chunks.
    """

    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    try:
        return search_documents(
            query=request.query,
            limit=request.limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print(
            f"Document search failed: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Document search failed. "
                "Check the application logs."
            ),
        ) from exc

@app.post("/chat/ask", tags=["Chat"])
def ask_question(request: AskRequest):
    """
    Answer a question using uploaded documents and local Ollama.
    """

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        return generate_answer(
            question=request.question,
            limit=request.limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print(
            f"Answer generation failed: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not generate an answer. "
                "Check the application logs."
            ),
        ) from exc