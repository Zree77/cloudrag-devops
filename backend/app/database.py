from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import settings


@contextmanager
def get_db_connection():
    connection = psycopg.connect(
        settings.database_url,
        row_factory=dict_row,
        connect_timeout=5,
    )

    try:
        yield connection
    finally:
        connection.close()


def check_database_connection() -> bool:
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS result")
                row = cursor.fetchone()

                return row["result"] == 1

    except psycopg.Error:
        return False