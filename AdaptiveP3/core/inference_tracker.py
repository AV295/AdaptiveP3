"""
AP3 — Inference Attack & Triangulation Tracker
===============================================
Computes a formalized, continuous inference risk signal r(u, q) in [0, 1)
by evaluating subpopulation overlap, attribute similarity, predicate Jaccard
distance, and exponential temporal decay across query history.

Theory (Slides 6 & 7 — G4, O1):
--------------------------------
1. Overlap(q, q_i) = w_t * S_table + w_c * J_column + w_p * J_predicate
2. Time decay factor = exp(-lambda * (t - t_i))
3. r(u, q) = 1 - exp(-alpha * sum(Overlap(q, q_i) * exp(-lambda * delta_t)))
4. Rather than hard-blocking, r(u, q) feeds directly into the risk-to-epsilon
   coupling loop: eps_eff = eps_role * (1 - r(u, q))^gamma
"""

import math
import time
from db.history_store import get_overlapping_queries
from config import (
    INFERENCE_WINDOW_SECONDS,
    LAMBDA_DECAY,
    RISK_WEIGHT_TABLE,
    RISK_WEIGHT_COLUMN,
    RISK_WEIGHT_PREDICATE,
    DEGRADATION_RISK_THRESHOLD,
)


class InferenceRisk:
    """Result of an inference-risk assessment for a single query."""

    def __init__(
        self,
        risk_score: float,
        is_blocked: bool,
        is_degraded: bool,
        overlap_count: int,
        raw_risk: float,
        reason: str | None = None,
        details: dict | None = None,
    ):
        self.risk_score = round(risk_score, 4)
        self.is_blocked = is_blocked
        self.is_degraded = is_degraded
        self.overlap_count = overlap_count
        self.raw_risk = round(raw_risk, 4)
        self.reason = reason
        self.details = details or {}


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity index: |A ∩ B| / |A ∪ B|."""
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _compute_query_overlap(
    curr_tables: list[str],
    curr_columns: list[str],
    curr_predicates: list[str],
    curr_has_where: bool,
    hist_q: dict,
) -> float:
    """
    Calculate normalized subpopulation overlap between current query q
    and a historical query q_i.
    """
    # 1. Table similarity (binary indicator or Jaccard across multi-table JOINs)
    hist_tables = set(hist_q.get("tables", []))
    curr_t_set = set(curr_tables)
    s_table = _jaccard_similarity(curr_t_set, hist_tables) if hist_tables else 0.0

    # 2. Column / Attribute Jaccard similarity
    hist_cols = set(hist_q.get("columns", []))
    curr_c_set = set(curr_columns)
    s_column = _jaccard_similarity(curr_c_set, hist_cols)

    # 3. Predicate / Subpopulation overlap
    hist_preds = set(hist_q.get("predicates", []))
    curr_p_set = set(curr_predicates)
    hist_has_where = hist_q.get("has_where", False)

    if curr_has_where and hist_has_where:
        # Both narrow a subpopulation
        s_predicate = _jaccard_similarity(curr_p_set, hist_preds)
        # If identical predicates or narrowing, high overlap
        if not s_predicate and (curr_p_set & hist_preds):
            s_predicate = 0.5
    elif curr_has_where != hist_has_where:
        # One is superset and one is filtered subset -> classic reconstruction probe
        s_predicate = 0.4
    else:
        # Neither has WHERE (both broad full-table scans)
        s_predicate = 0.1

    overlap = (
        RISK_WEIGHT_TABLE * s_table
        + RISK_WEIGHT_COLUMN * s_column
        + RISK_WEIGHT_PREDICATE * s_predicate
    )
    return max(0.0, min(overlap, 1.0))


def assess_inference_risk(
    username: str,
    tables: list[str],
    columns: list[str],
    predicates: list[str] | None = None,
    has_where: bool = False,
    raw_sql: str = "",
    alpha_scale: float = 0.35,
) -> InferenceRisk:
    """
    Calculate continuous triangulation risk r(u, q) in [0, 1) across query history.

    Parameters
    ----------
    username : str
        The requesting user identifier.
    tables : list[str]
        Tables referenced in the query.
    columns : list[str]
        Columns queried or filtered.
    predicates : list[str]
        WHERE predicates extracted from AST.
    has_where : bool
        Whether query has a filter condition.
    raw_sql : str
        The full SQL query text.
    alpha_scale : float
        Sensitivity calibration exponent for cumulative risk summation.

    Returns
    -------
    InferenceRisk
        Object containing continuous risk_score in [0, 1), degradation trigger,
        and overlap diagnostics.
    """
    predicates = predicates or []
    overlaps = get_overlapping_queries(
        username, tables, window_seconds=INFERENCE_WINDOW_SECONDS
    )
    overlap_count = len(overlaps)

    if overlap_count == 0:
        return InferenceRisk(
            risk_score=0.0,
            is_blocked=False,
            is_degraded=False,
            overlap_count=0,
            raw_risk=0.0,
            reason="No overlapping query history found.",
            details={"max_single_overlap": 0.0, "time_decay_sum": 0.0},
        )

    now = time.time()
    accumulated_risk = 0.0
    max_single_overlap = 0.0

    for q in overlaps:
        dt = max(0.0, now - q.get("timestamp", now))
        time_decay = math.exp(-LAMBDA_DECAY * dt)

        pairwise_overlap = _compute_query_overlap(
            curr_tables=tables,
            curr_columns=columns,
            curr_predicates=predicates,
            curr_has_where=has_where,
            hist_q=q,
        )

        max_single_overlap = max(max_single_overlap, pairwise_overlap)
        accumulated_risk += pairwise_overlap * time_decay

    # Continuous risk signal r(u, q) in [0, 1)
    # r = 1 - exp(-alpha * accumulated_risk)
    r_val = 1.0 - math.exp(-alpha_scale * accumulated_risk)
    r_val = max(0.0, min(r_val, 0.9999))

    is_degraded = r_val >= DEGRADATION_RISK_THRESHOLD

    reason = None
    if is_degraded:
        reason = (
            f"High triangulation risk detected (r = {r_val:.3f} >= {DEGRADATION_RISK_THRESHOLD}). "
            f"Query is routed to graceful degradation with elevated noise."
        )
    elif r_val > 0.4:
        reason = f"Moderate triangulation risk (r = {r_val:.3f}). Effective epsilon will be reduced."

    return InferenceRisk(
        risk_score=r_val,
        is_blocked=False,  # Replaced hard blocking with graceful degradation schedule (O2)
        is_degraded=is_degraded,
        overlap_count=overlap_count,
        raw_risk=accumulated_risk,
        reason=reason,
        details={
            "max_single_overlap": round(max_single_overlap, 4),
            "accumulated_risk": round(accumulated_risk, 4),
            "overlap_count": overlap_count,
        },
    )
