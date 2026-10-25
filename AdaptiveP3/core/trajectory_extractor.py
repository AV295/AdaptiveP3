"""
AP3 — Query Trajectory Feature Extractor
========================================
Extracts mathematical, spatial, and temporal trajectory features from an
incoming SQL query and historical session context.

This module provides the feature-engineering foundation for patent claims
around relational AST trajectory analysis and sequential inference attack detection.
"""

import math
import time
from typing import Any, List, Dict, Tuple


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute standard Jaccard similarity index: |A ∩ B| / |A ∪ B|."""
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def encode_aggregate_type(aggregates: List[str]) -> float:
    """
    Encode SQL aggregate function sensitivity hierarchy:
    COUNT=1.0, AVG=2.0, SUM=3.0, MIN/MAX=4.0, NONE=0.0
    """
    if not aggregates:
        return 0.0
    first = aggregates[0].lower()
    if first == "count":
        return 1.0
    elif first == "avg":
        return 2.0
    elif first == "sum":
        return 3.0
    elif first in ("min", "max"):
        return 4.0
    return 0.5


FEATURE_NAMES = [
    "pred_jaccard_max",
    "pred_jaccard_mean",
    "col_jaccard_max",
    "col_jaccard_mean",
    "table_match_ratio",
    "consecutive_pred_jaccard",
    "pred_narrowing_velocity",
    "differencing_proximity",
    "time_delta_min",
    "time_delta_mean",
    "window_query_count",
    "has_where",
    "curr_pred_count",
    "aggregate_type_encoded",
    "time_decayed_overlap_sum",
]


def extract_trajectory_features(
    curr_tables: List[str],
    curr_columns: List[str],
    curr_predicates: List[str],
    curr_has_where: bool,
    curr_aggregates: List[str],
    history_queries: List[Dict[str, Any]],
    current_timestamp: float | None = None,
    lambda_decay: float = 0.005,
) -> Tuple[List[float], Dict[str, float]]:
    """
    Transforms the candidate query and query history window into a normalized
    multidimensional feature vector for attack classification and risk scoring.

    Parameters
    ----------
    curr_tables : List[str]
        Tables in current query.
    curr_columns : List[str]
        Columns in current query.
    curr_predicates : List[str]
        Predicates in current query.
    curr_has_where : bool
        Whether current query contains WHERE.
    curr_aggregates : List[str]
        Aggregates in current query.
    history_queries : List[Dict[str, Any]]
        List of historical query dicts ordered newest-to-oldest or oldest-to-newest.
    current_timestamp : float | None
        Current time (defaults to time.time()).
    lambda_decay : float
        Exponential temporal decay rate.

    Returns
    -------
    Tuple[List[float], Dict[str, float]]
        Dense feature vector (as list of floats) and dictionary of named features.
    """
    now = current_timestamp if current_timestamp is not None else time.time()
    curr_p_set = set(curr_predicates or [])
    curr_c_set = set(curr_columns or [])
    curr_t_set = set(curr_tables or [])
    curr_has_w = 1.0 if curr_has_where else 0.0
    curr_p_count = float(len(curr_p_set))
    agg_code = encode_aggregate_type(curr_aggregates)

    if not history_queries:
        # Cold start (isolated first query in session)
        feature_dict = {
            "pred_jaccard_max": 0.0,
            "pred_jaccard_mean": 0.0,
            "col_jaccard_max": 0.0,
            "col_jaccard_mean": 0.0,
            "table_match_ratio": 0.0,
            "consecutive_pred_jaccard": 0.0,
            "pred_narrowing_velocity": 0.0,
            "differencing_proximity": 0.0,
            "time_delta_min": 3600.0,
            "time_delta_mean": 3600.0,
            "window_query_count": 0.0,
            "has_where": curr_has_w,
            "curr_pred_count": curr_p_count,
            "aggregate_type_encoded": agg_code,
            "time_decayed_overlap_sum": 0.0,
        }
        return [feature_dict[name] for name in FEATURE_NAMES], feature_dict

    # Sort history chronological: oldest to newest
    sorted_hist = sorted(history_queries, key=lambda q: q.get("timestamp", 0.0))

    pred_jaccards: List[float] = []
    col_jaccards: List[float] = []
    table_matches: List[float] = []
    time_deltas: List[float] = []
    time_decayed_overlaps: List[float] = []

    for h in sorted_hist:
        h_preds = set(h.get("predicates", []))
        h_cols = set(h.get("columns", []))
        h_tables = set(h.get("tables", []))
        h_ts = float(h.get("timestamp", now))

        # 1. Predicate Jaccard
        pj = jaccard_similarity(curr_p_set, h_preds)
        pred_jaccards.append(pj)

        # 2. Column Jaccard
        cj = jaccard_similarity(curr_c_set, h_cols)
        col_jaccards.append(cj)

        # 3. Table match indicator
        tm = 1.0 if (curr_t_set & h_tables) else 0.0
        table_matches.append(tm)

        # 4. Temporal delta
        dt = max(0.001, now - h_ts)
        time_deltas.append(dt)

        # 5. Composite pairwise overlap with time decay
        pairwise_overlap = 0.3 * tm + 0.3 * cj + 0.4 * pj
        time_decay = math.exp(-lambda_decay * dt)
        time_decayed_overlaps.append(pairwise_overlap * time_decay)

    # Immediate previous query (latest in sorted history)
    prev_q = sorted_hist[-1]
    prev_preds = set(prev_q.get("predicates", []))
    prev_ts = float(prev_q.get("timestamp", now))
    dt_prev = max(0.5, now - prev_ts)

    # Consecutive predicate overlap
    consecutive_pred_j = jaccard_similarity(curr_p_set, prev_preds)

    # Predicate narrowing velocity: rate at which predicates are being added
    # (e.g. going from 1 predicate to 3 predicates in 2 seconds is high velocity)
    added_preds = len(curr_p_set) - len(prev_preds)
    pred_narrowing_velocity = max(0.0, added_preds / dt_prev)

    # Differencing attack proximity:
    # A differencing attack occurs when current query and previous query differ
    # by exactly one predicate or small filter modification on the exact same table and columns
    sym_diff = len(curr_p_set ^ prev_preds)
    col_overlap = jaccard_similarity(curr_c_set, set(prev_q.get("columns", [])))
    same_table = 1.0 if (curr_t_set & set(prev_q.get("tables", []))) else 0.0

    if same_table > 0.0 and col_overlap > 0.8 and sym_diff in (1, 2) and dt_prev < 120.0:
        # High likelihood of differencing probe (e.g. subpopulation excluding 1 target)
        differencing_proximity = 1.0
    elif same_table > 0.0 and sym_diff == 1:
        differencing_proximity = 0.7
    else:
        differencing_proximity = 0.0

    feature_dict = {
        "pred_jaccard_max": round(max(pred_jaccards) if pred_jaccards else 0.0, 4),
        "pred_jaccard_mean": round(sum(pred_jaccards) / len(pred_jaccards) if pred_jaccards else 0.0, 4),
        "col_jaccard_max": round(max(col_jaccards) if col_jaccards else 0.0, 4),
        "col_jaccard_mean": round(sum(col_jaccards) / len(col_jaccards) if col_jaccards else 0.0, 4),
        "table_match_ratio": round(sum(table_matches) / len(table_matches) if table_matches else 0.0, 4),
        "consecutive_pred_jaccard": round(consecutive_pred_j, 4),
        "pred_narrowing_velocity": round(min(5.0, pred_narrowing_velocity), 4),
        "differencing_proximity": round(differencing_proximity, 4),
        "time_delta_min": round(min(time_deltas) if time_deltas else 3600.0, 2),
        "time_delta_mean": round(sum(time_deltas) / len(time_deltas) if time_deltas else 3600.0, 2),
        "window_query_count": float(len(sorted_hist)),
        "has_where": curr_has_w,
        "curr_pred_count": curr_p_count,
        "aggregate_type_encoded": agg_code,
        "time_decayed_overlap_sum": round(sum(time_decayed_overlaps), 4),
    }

    feature_vector = [feature_dict[name] for name in FEATURE_NAMES]
    return feature_vector, feature_dict
