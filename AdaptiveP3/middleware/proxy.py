"""
AP3 — Adaptive Proxy Pipeline
==============================
Orchestrates the unified query-time privacy and security pipeline:

1. **Parse & Analyse** SQL syntax, extract columns and predicates (query_analyzer)
2. **Block** SQL injection attempts and unsafe statements
3. **Restrict** non-SELECT queries for non-admin roles
4. **Evaluate** live continuous triangulation risk r(u, q) from history (inference_tracker)
5. **Coupling & Degradation**: Compute dynamic eps_eff = eps * (1 - r)^gamma;
   engage graceful degradation schedule instead of hard denial (differential_privacy)
6. **Execute** query against PostgreSQL
7. **Apply** calibrated Laplace noise to aggregate results
8. **Deduct** composed privacy loss and persist query audit in SQLite history store
"""

from fastapi import HTTPException
from core.query_analyzer import analyze_query, QueryAnalysis
from core.abac import deduct_budget
from core.differential_privacy import (
    compute_effective_epsilon,
    compute_noise_scale,
    add_noise_to_resultset,
)
from core.inference_tracker import assess_inference_risk
from db.postgres import execute_query
from db.history_store import record_query
from models.user import User
from config import GAMMA, EPSILON_MIN, DEGRADATION_RISK_THRESHOLD, ROLE_QUERY_EPSILON

import logging

logger = logging.getLogger("ap3.proxy")


def process_query(user: User, raw_sql: str) -> dict:
    """
    Execute raw_sql through the risk-adaptive privacy pipeline and return
    differentially private results with comprehensive transparency metrics.

    Raises
    ------
    HTTPException
        On SQL injection or unauthorized non-SELECT queries.
    """

    # ── 1. Analyse AST & Predicates ──────────────────────────────────
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
            detail=f"Query blocked by SQL Injection Guard: {analysis.danger_reason}",
        )

    # ── 3. Role-based statement restriction ──────────────────────────
    if not analysis.is_select and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access Denied: Only SELECT queries are permitted for your role.",
        )

    # ── 4. Live Triangulation Risk Signal r(u, q) ────────────────────
    risk = assess_inference_risk(
        username=user.username,
        tables=analysis.tables,
        columns=analysis.columns,
        predicates=analysis.predicates,
        has_where=analysis.has_where,
        raw_sql=raw_sql,
    )

    # ── 5. Dynamic Risk-to-Epsilon Coupling & Degradation Schedule ──
    # Objective O1: eps_eff = eps_remaining * (1 - r(u, q))^gamma
    # Objective O2: Graceful degradation replaces query denial
    is_budget_depleted = user.epsilon_remaining <= 0.0
    is_high_risk = risk.is_degraded or (risk.risk_score >= DEGRADATION_RISK_THRESHOLD)
    is_degraded_mode = is_budget_depleted or is_high_risk

    if analysis.is_aggregate:
        if is_degraded_mode:
            # Monotonically increasing noise schedule (eps -> eps_min)
            eff_eps = EPSILON_MIN
        else:
            role_key = user.role.value if hasattr(user.role, "value") else str(user.role)
            nominal_role_eps = ROLE_QUERY_EPSILON.get(role_key, 1.0)
            base_alloc = min(user.epsilon_remaining, nominal_role_eps)
            eff_eps = compute_effective_epsilon(
                base_epsilon=base_alloc,
                risk_score=risk.risk_score,
                gamma=GAMMA,
                min_epsilon=EPSILON_MIN,
            )
        noise_scale = compute_noise_scale(analysis.sensitivity, eff_eps)

    else:
        # Non-aggregate query
        eff_eps = user.epsilon_remaining
        noise_scale = 0.0

    # ── 6. Execute Against PostgreSQL ────────────────────────────────
    try:
        rows = execute_query(raw_sql)
    except Exception as exc:
        logger.error("PostgreSQL execution error: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Database execution error: {str(exc)}")

    # ── 7. Apply Calibrated Laplace Mechanism ────────────────────────
    if analysis.is_aggregate and rows:
        noised_rows = add_noise_to_resultset(
            rows,
            epsilon=eff_eps,
            sensitivity=analysis.sensitivity,
        )
    else:
        noised_rows = rows

    # ── 8. Sequential Composition & Audit Logging ────────────────────
    # Deduct actual privacy loss consumed (eps_eff)
    consumed_budget = eff_eps if analysis.is_aggregate else 0.0
    updated_user, was_budget_degraded = deduct_budget(user, consumed_budget)

    # Record detailed query audit in SQLite history
    record_query(
        username=user.username,
        tables=analysis.tables,
        columns=analysis.columns,
        predicates=analysis.predicates,
        has_where=analysis.has_where,
        raw_sql=raw_sql,
        risk_score=risk.risk_score,
        effective_epsilon=eff_eps,
    )

    degradation_reason = None
    if is_degraded_mode:
        if is_budget_depleted:
            degradation_reason = "Privacy budget exhausted. Query answered under graceful degradation (maximum noise floor)."
        else:
            degradation_reason = risk.reason

    privacy_note = (
        f"Laplace noise applied with effective epsilon={eff_eps:.4f} (noise scale b={noise_scale:.4f})."
        if analysis.is_aggregate
        else "Non-aggregate query — returned without DP perturbation."
    )

    return {
        "status": "success",
        "user": updated_user.model_dump(),
        "query_analysis": {
            "tables": analysis.tables,
            "columns": analysis.columns,
            "predicates": analysis.predicates,
            "aggregates": analysis.aggregates,
            "sensitivity": analysis.sensitivity,
            "is_aggregate": analysis.is_aggregate,
        },
        "privacy_metrics": {
            "risk_score": risk.risk_score,
            "raw_risk": risk.raw_risk,
            "effective_epsilon": eff_eps,
            "noise_scale": noise_scale,
            "degraded_mode": is_degraded_mode,
            "degradation_reason": degradation_reason,
            "inference_overlap_count": risk.overlap_count,
            "subpopulation_overlap": risk.details,
        },
        "results": noised_rows,
        "privacy_note": privacy_note,
    }
