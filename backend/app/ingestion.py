import io
import uuid
from functools import lru_cache
from pathlib import Path

import numpy as np
from pgvector.psycopg import register_vector
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from app.database import get_db_connection


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 250
CHUNK_OVERLAP = 40
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the embedding model once and reuse it."""
    return SentenceTransformer(MODEL_NAME)


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(io.BytesIO(file_bytes))

    extracted_pages = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            extracted_pages.append(page_text)

    return "\n".join(extracted_pages).strip()


def split_text_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()

    if not words:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size - 1")

    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]

        if not chunk_words:
            break

        chunks.append(" ".join(chunk_words))

    return chunks


def ingest_pdf(
    filename: str,
    content_type: str,
    file_bytes: bytes,
) -> dict:
    """Extract, chunk, embed, and store a PDF in PostgreSQL."""

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("The PDF exceeds the 10 MB upload limit.")

    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a valid PDF.")

    try:
        extracted_text = extract_pdf_text(file_bytes)
    except Exception as exc:
        raise ValueError(
            "The PDF could not be read. Check that it is a valid, "
            "unencrypted PDF."
        ) from exc

    if not extracted_text:
        raise ValueError(
            "No extractable text was found. Scanned PDFs require OCR, "
            "which is not implemented yet."
        )

    chunks = split_text_into_chunks(extracted_text)

    if not chunks:
        raise ValueError("The PDF did not produce any text chunks.")

    # Load the model on the first ingestion request.
    model = get_embedding_model()

    embeddings = model.encode(
        chunks,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    if embeddings.shape != (len(chunks), 384):
        raise RuntimeError(
            f"Unexpected embedding dimensions: {embeddings.shape}"
        )

    document_id = uuid.uuid4()

    # Store metadata, text chunks, and embeddings transactionally.
    with get_db_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (
                    id,
                    filename,
                    content_type
                )
                VALUES (%s, %s, %s)
                """,
                (
                    document_id,
                    Path(filename).name,
                    content_type,
                ),
            )

            for index, (chunk, embedding) in enumerate(
                zip(chunks, embeddings)
            ):
                cursor.execute(
                    """
                    INSERT INTO document_chunks (
                        document_id,
                        chunk_index,
                        content,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        document_id,
                        index,
                        chunk,
                        np.asarray(embedding, dtype=np.float32),
                    ),
                )

        # Commit only after all inserts have succeeded.
        connection.commit()

    return {
        "document_id": str(document_id),
        "filename": Path(filename).name,
        "chunks_created": len(chunks),
        "embedding_dimensions": 384,
    }