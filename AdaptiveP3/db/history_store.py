"""
AP3 — SQLite Query History Store
==================================
Persists every executed query so the inference tracker can look for
patterns of data triangulation.
"""

import sqlite3
import json
import time
from config import HISTORY_DB_PATH


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite history database, creating the table if needed."""
    conn = sqlite3.connect(HISTORY_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    NOT NULL,
            tables    TEXT    NOT NULL,
            columns   TEXT    NOT NULL,
            has_where INTEGER NOT NULL,
            raw_sql   TEXT    NOT NULL,
            timestamp REAL    NOT NULL
        )
    """)
    conn.commit()
    return conn


def record_query(
    username: str,
    tables: list[str],
    columns: list[str],
    has_where: bool,
    raw_sql: str,
) -> None:
    """Persist a query record for later inference-risk analysis."""
    conn = _get_connection()
    conn.execute(
        "INSERT INTO query_history "
        "(username, tables, columns, has_where, raw_sql, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            username,
            json.dumps(tables),
            json.dumps(columns),
            int(has_where),
            raw_sql,
            time.time(),
        ),
    )
    conn.commit()
    conn.close()


def get_overlapping_queries(
    username: str,
    tables: list[str],
    window_seconds: float = 3600.0,
) -> list[dict]:
    """
    Retrieve past queries by the same user that targeted **any** of the
    same table(s) within *window_seconds*.

    Used by the inference tracker to detect triangulation attempts.
    """
    conn = _get_connection()
    cutoff = time.time() - window_seconds
    cursor = conn.execute(
        "SELECT tables, columns, has_where, raw_sql, timestamp "
        "FROM query_history "
        "WHERE username = ? AND timestamp >= ?",
        (username, cutoff),
    )

    results: list[dict] = []
    target_set = set(tables)

    for row in cursor.fetchall():
        stored_tables = set(json.loads(row[0]))
        if stored_tables & target_set:          # any overlap
            results.append({
                "tables": json.loads(row[0]),
                "columns": json.loads(row[1]),
                "has_where": bool(row[2]),
                "raw_sql": row[3],
                "timestamp": row[4],
            })

    conn.close()
    return results
