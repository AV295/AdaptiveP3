"""
AP3 — PostgreSQL Connector
============================
Thin wrapper around *psycopg2* for executing read-only queries and
returning results as a list of dicts.
"""

import psycopg2
import psycopg2.extras
from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)


def get_pg_connection():
    """Create and return a new PostgreSQL connection."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def execute_query(sql: str) -> list[dict]:
    """
    Execute a SQL query against PostgreSQL and return every row
    as a dictionary keyed by column name.
    """
    conn = get_pg_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()
