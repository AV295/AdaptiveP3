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
from core.ml_risk_model import evaluate_ml_risk


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
        heuristic_risk: float = 0.0,
        ml_risk: float = 0.0,
        attack_pattern: str = "BENIGN",
        ml_confidence: float = 1.0,
        top_factors: list[str] | None = None,
        ml_latency_ms: float = 0.0,
    ):
        self.risk_score = round(risk_score, 4)
        self.is_blocked = is_blocked
        self.is_degraded = is_degraded
        self.overlap_count = overlap_count
        self.raw_risk = round(raw_risk, 4)
        self.reason = reason
        self.details = details or {}
        self.heuristic_risk = round(heuristic_risk, 4)
        self.ml_risk = round(ml_risk, 4)
        self.attack_pattern = attack_pattern
        self.ml_confidence = round(ml_confidence, 4)
        self.top_factors = top_factors or []
        self.ml_latency_ms = round(ml_latency_ms, 3)


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
    aggregates: list[str] | None = None,
    alpha_scale: float = 0.35,
) -> InferenceRisk:
    """
    Calculate hybrid continuous inference risk r(u, q) in [0, 1) across query history,
    arbitrating between the deterministic AST overlap formulation and the trained
    trajectory ensemble classifier.
    """
    predicates = predicates or []
    aggregates = aggregates or []
    overlaps = get_overlapping_queries(
        username, tables, window_seconds=INFERENCE_WINDOW_SECONDS
    )
    overlap_count = len(overlaps)
    now = time.time()

    # 1. Deterministic Heuristic Risk Calculation
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

    r_heuristic = 1.0 - math.exp(-alpha_scale * accumulated_risk) if overlap_count > 0 else 0.0
    r_heuristic = max(0.0, min(r_heuristic, 0.9999))

    # 2. Machine Learning Trajectory Evaluation
    ml_eval = evaluate_ml_risk(
        tables=tables,
        columns=columns,
        predicates=predicates,
        has_where=has_where,
        aggregates=aggregates,
        history_queries=overlaps,
        current_timestamp=now,
    )

    # 3. Patentable Hybrid Arbitration: r_final = max(r_heuristic, r_ML)
    # Guarantees mathematical lower bound while catching subtle sequential attack patterns
    r_final = max(r_heuristic, ml_eval.ml_risk_score)
    r_final = max(0.0, min(r_final, 0.9999))

    is_degraded = r_final >= DEGRADATION_RISK_THRESHOLD

    reason = None
    if is_degraded:
        if ml_eval.is_attack:
            reason = (
                f"Severe {ml_eval.attack_pattern} pattern detected by ML model "
                f"(confidence={ml_eval.confidence:.2f}, r={r_final:.3f} >= {DEGRADATION_RISK_THRESHOLD}). "
                f"Routed to graceful degradation with noise floor."
            )
        else:
            reason = (
                f"High triangulation risk detected (r = {r_final:.3f} >= {DEGRADATION_RISK_THRESHOLD}). "
                f"Query is routed to graceful degradation with elevated noise."
            )
    elif ml_eval.is_attack:
        reason = (
            f"Adversarial {ml_eval.attack_pattern} probe pattern identified "
            f"(ML score={ml_eval.ml_risk_score:.3f}, confidence={ml_eval.confidence:.2f}). "
            f"Effective epsilon downscaled."
        )
    elif r_final > 0.4:
        reason = f"Moderate query correlation (r = {r_final:.3f}). Effective epsilon will be reduced."

    return InferenceRisk(
        risk_score=r_final,
        is_blocked=False,
        is_degraded=is_degraded,
        overlap_count=overlap_count,
        raw_risk=accumulated_risk,
        reason=reason,
        details={
            "max_single_overlap": round(max_single_overlap, 4),
            "accumulated_risk": round(accumulated_risk, 4),
            "overlap_count": overlap_count,
        },
        heuristic_risk=r_heuristic,
        ml_risk=ml_eval.ml_risk_score,
        attack_pattern=ml_eval.attack_pattern,
        ml_confidence=ml_eval.confidence,
        top_factors=ml_eval.top_factors,
        ml_latency_ms=ml_eval.latency_ms,
    )
