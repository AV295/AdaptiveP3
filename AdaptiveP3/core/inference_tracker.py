"""
AP3 — Inference Attack Tracker
================================
Monitors per-user query history to detect potential **data triangulation**
(inference attacks).  If a user repeatedly queries the same table(s) —
especially with varying WHERE filters — the proxy blocks further requests
until the time window expires.

Detection heuristic
-------------------
1. Look up recent queries by the same user that touch overlapping tables.
2. If the overlap count ≥ ``INFERENCE_QUERY_THRESHOLD``, **block** the
   current query and return a risk assessment.
3. Otherwise, record the current query and allow it through.
"""

from db.history_store import record_query, get_overlapping_queries
from config import INFERENCE_QUERY_THRESHOLD, INFERENCE_WINDOW_SECONDS


class InferenceRisk:
    """Result of an inference-risk assessment for a single query."""

    def __init__(
        self,
        is_blocked: bool,
        overlap_count: int,
        reason: str | None = None,
    ):
        self.is_blocked = is_blocked
        self.overlap_count = overlap_count
        self.reason = reason


def assess_inference_risk(
    username: str,
    tables: list[str],
    columns: list[str],
    has_where: bool,
    raw_sql: str,
) -> InferenceRisk:
    """
    Check the user's recent query history for potential data triangulation.

    Parameters
    ----------
    username : str
        The requesting user.
    tables : list[str]
        Tables referenced in the current query.
    columns : list[str]
        Columns referenced in the current query.
    has_where : bool
        Whether the query contains a WHERE clause.
    raw_sql : str
        The full SQL text (stored for auditing).

    Returns
    -------
    InferenceRisk
        Contains ``is_blocked=True`` when the threshold is breached.
    """
    overlaps = get_overlapping_queries(
        username, tables, window_seconds=INFERENCE_WINDOW_SECONDS
    )
    overlap_count = len(overlaps)

    # How many of those overlapping queries also had WHERE filters?
    where_overlaps = sum(1 for q in overlaps if q["has_where"])

    if overlap_count >= INFERENCE_QUERY_THRESHOLD:
        return InferenceRisk(
            is_blocked=True,
            overlap_count=overlap_count,
            reason=(
                f"Inference attack risk: {overlap_count} overlapping queries on "
                f"table(s) {tables} in the last "
                f"{INFERENCE_WINDOW_SECONDS / 60:.0f} min "
                f"({where_overlaps} with WHERE filters). "
                f"Threshold is {INFERENCE_QUERY_THRESHOLD}."
            ),
        )

    # Safe — record this query for future tracking
    record_query(username, tables, columns, has_where, raw_sql)

    return InferenceRisk(is_blocked=False, overlap_count=overlap_count)
