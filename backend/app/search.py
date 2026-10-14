from pgvector.psycopg import register_vector

from app.database import get_db_connection
from app.ingestion import get_embedding_model


def search_documents(query: str, limit: int = 5) -> dict:
    """Retrieve the most relevant document chunks for a query."""

    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    if limit < 1 or limit > 20:
        raise ValueError("Limit must be between 1 and 20.")

    model = get_embedding_model()

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    with get_db_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    d.id AS document_id,
                    d.filename,
                    dc.chunk_index,
                    dc.content,
                    1 - (dc.embedding <=> %s) AS similarity
                FROM document_chunks AS dc
                JOIN documents AS d
                    ON d.id = dc.document_id
                WHERE dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> %s
                LIMIT %s
                """,
                (
                    query_embedding,
                    query_embedding,
                    limit,
                ),
            )

            rows = cursor.fetchall()

    results = [
        {
            "document_id": str(row["document_id"]),
            "filename": row["filename"],
            "chunk_index": row["chunk_index"],
            "content": row["content"],
            "similarity": round(float(row["similarity"]), 4),
        }
        for row in rows
    ]

    return {
        "query": query,
        "results_count": len(results),
        "results": results,
    }