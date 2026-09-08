"""
AP3 — SQLite Query History Store
==================================
Persists every executed query with its attributes, extracted predicates,
risk score, and consumed epsilon so the inference tracker can compute
formal subpopulation overlap and data triangulation risk.
"""

import sqlite3
import json
import time
from config import HISTORY_DB_PATH


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite history database, creating/updating tables if needed."""
    conn = sqlite3.connect(HISTORY_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            username           TEXT    NOT NULL,
            tables             TEXT    NOT NULL,
            columns            TEXT    NOT NULL,
            predicates         TEXT    DEFAULT '[]',
            has_where          INTEGER NOT NULL,
            raw_sql            TEXT    NOT NULL,
            risk_score         REAL    DEFAULT 0.0,
            effective_epsilon  REAL    DEFAULT 0.0,
            timestamp          REAL    NOT NULL
        )
    """)
    # Ensure backward compatibility if database already existed with older schema
    cursor = conn.execute("PRAGMA table_info(query_history)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if "predicates" not in existing_cols:
        conn.execute("ALTER TABLE query_history ADD COLUMN predicates TEXT DEFAULT '[]'")
    if "risk_score" not in existing_cols:
        conn.execute("ALTER TABLE query_history ADD COLUMN risk_score REAL DEFAULT 0.0")
    if "effective_epsilon" not in existing_cols:
        conn.execute("ALTER TABLE query_history ADD COLUMN effective_epsilon REAL DEFAULT 0.0")
    conn.commit()
    return conn


def record_query(
    username: str,
    tables: list[str],
    columns: list[str],
    predicates: list[str],
    has_where: bool,
    raw_sql: str,
    risk_score: float = 0.0,
    effective_epsilon: float = 0.0,
) -> None:
    """Persist a detailed query record for continuous inference-risk analysis."""
    conn = _get_connection()
    conn.execute(
        "INSERT INTO query_history "
        "(username, tables, columns, predicates, has_where, raw_sql, risk_score, effective_epsilon, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            username,
            json.dumps(tables),
            json.dumps(columns),
            json.dumps(predicates or []),
            int(has_where),
            raw_sql,
            float(risk_score),
            float(effective_epsilon),
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
        "SELECT tables, columns, predicates, has_where, raw_sql, risk_score, effective_epsilon, timestamp "
        "FROM query_history "
        "WHERE username = ? AND timestamp >= ? "
        "ORDER BY timestamp DESC",
        (username, cutoff),
    )

    results: list[dict] = []
    target_set = set(tables)

    for row in cursor.fetchall():
        stored_tables = set(json.loads(row[0]))
        if stored_tables & target_set:  # any table overlap
            pred_raw = row[2]
            try:
                preds = json.loads(pred_raw) if pred_raw else []
            except Exception:
                preds = []
            results.append({
                "tables": json.loads(row[0]),
                "columns": json.loads(row[1]),
                "predicates": preds,
                "has_where": bool(row[3]),
                "raw_sql": row[4],
                "risk_score": float(row[5]) if row[5] is not None else 0.0,
                "effective_epsilon": float(row[6]) if row[6] is not None else 0.0,
                "timestamp": float(row[7]),
            })

    conn.close()
    return results


def get_user_history(username: str, limit: int = 25) -> list[dict]:
    """Retrieve recent query history for audit and visualization."""
    conn = _get_connection()
    cursor = conn.execute(
        "SELECT id, tables, columns, predicates, has_where, raw_sql, risk_score, effective_epsilon, timestamp "
        "FROM query_history "
        "WHERE username = ? "
        "ORDER BY timestamp DESC LIMIT ?",
        (username, limit),
    )

    results: list[dict] = []
    for row in cursor.fetchall():
        pred_raw = row[3]
        try:
            preds = json.loads(pred_raw) if pred_raw else []
        except Exception:
            preds = []
        results.append({
            "id": row[0],
            "tables": json.loads(row[1]),
            "columns": json.loads(row[2]),
            "predicates": preds,
            "has_where": bool(row[4]),
            "raw_sql": row[5],
            "risk_score": float(row[6]) if row[6] is not None else 0.0,
            "effective_epsilon": float(row[7]) if row[7] is not None else 0.0,
            "timestamp": float(row[8]),
        })

    conn.close()
    return results

