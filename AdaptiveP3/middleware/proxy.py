"""
AP3 — Proxy Pipeline
=====================
Orchestrates the full security pipeline for every incoming query:

1. **Parse & Analyse** the SQL  (query_analyzer)
2. **Block** SQL injection attempts
3. **Restrict** non-SELECT queries for non-admin roles
4. **Assess** inference risk from query history
5. **Check** ABAC privacy budget (ε)
6. **Execute** the query against PostgreSQL
7. **Apply** Laplace noise to aggregate results
8. **Deduct** the privacy budget and return sanitized output
"""

from fastapi import HTTPException
from core.query_analyzer import analyze_query, QueryAnalysis
from core.abac import has_budget, deduct_budget
from core.differential_privacy import add_noise_to_resultset
from core.inference_tracker import assess_inference_risk
from db.postgres import execute_query
from models.user import User

import logging

logger = logging.getLogger("ap3.proxy")


def process_query(user: User, raw_sql: str) -> dict:
    """
    Run *raw_sql* through every security layer and return the
    (possibly noised) result set together with metadata.

    Raises
    ------
    HTTPException
        On injection, insufficient budget, inference risk, or DB errors.
    """

    # ── 1. Analyse ───────────────────────────────────────────────────
    analysis: QueryAnalysis = analyze_query(raw_sql)

    # ── 2. SQL Injection Guard ───────────────────────────────────────
    if analysis.is_dangerous:
        logger.warning(
            "BLOCKED injection attempt by '%s': %s",
            user.username,
            analysis.danger_reason,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Query blocked: {analysis.danger_reason}",
        )

    # ── 3. Role-based statement restriction ──────────────────────────
    if not analysis.is_select and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only SELECT queries are permitted for your role.",
        )

    # ── 4. Inference Risk ────────────────────────────────────────────
    risk = assess_inference_risk(
        username=user.username,
        tables=analysis.tables,
        columns=analysis.columns,
        has_where=analysis.has_where,
        raw_sql=raw_sql,
    )
    if risk.is_blocked:
        logger.warning(
            "BLOCKED inference risk for '%s': %s", user.username, risk.reason
        )
        raise HTTPException(
            status_code=429,
            detail=f"Query blocked: {risk.reason}",
        )

    # ── 5. Privacy Budget Check ──────────────────────────────────────
    query_cost = analysis.sensitivity
    if not has_budget(user, query_cost):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Insufficient privacy budget. "
                f"Remaining: {user.epsilon_remaining:.4f}, "
                f"Required: {query_cost:.4f}"
            ),
        )

    # ── 6. Execute Against PostgreSQL ────────────────────────────────
    try:
        rows = execute_query(raw_sql)
    except Exception as exc:
        logger.error("PostgreSQL error: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")

    # ── 7. Apply Differential Privacy Noise ──────────────────────────
    if analysis.is_aggregate and rows:
        noised_rows = add_noise_to_resultset(
            rows,
            epsilon=user.epsilon_remaining,
            sensitivity=analysis.sensitivity,
        )
    else:
        noised_rows = rows   # non-aggregate SELECT — no noise

    # ── 8. Deduct Budget ─────────────────────────────────────────────
    updated_user = deduct_budget(user, query_cost)

    return {
        "status": "success",
        "user": updated_user.model_dump(),
        "query_analysis": {
            "tables": analysis.tables,
            "aggregates": analysis.aggregates,
            "sensitivity": analysis.sensitivity,
            "is_aggregate": analysis.is_aggregate,
            "inference_overlap_count": risk.overlap_count,
        },
        "results": noised_rows,
        "privacy_note": (
            "Laplace noise (ε-DP) applied to aggregate results."
            if analysis.is_aggregate
            else "Non-aggregate query — results returned as-is."
        ),
    }
