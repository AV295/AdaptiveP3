"""
AP3 — Risk-Adaptive Differential Privacy Engine
==================================================
Implements dynamic Laplace noise injection coupled to live triangulation
risk and provides a graceful degradation schedule (Slides 6 & 7 — G1, G3, O1, O2).

Mathematical Formulations:
---------------------------
1. Dynamic Coupling (O1):
   eps_eff(u, q) = max(eps_min, eps_remaining * (1 - r(u, q))^gamma)

2. Laplace Calibration:
   b = Delta_f / eps_eff
   Laplace noise ~ Lap(b) = Lap(Delta_f / eps_eff)

3. Graceful Degradation (O2):
   When remaining budget approaches zero or inference risk r(u, q) spikes,
   answers degrade gracefully with monotonically increasing noise (eps -> eps_min)
   rather than leaking state through hard query denial.
"""

import math
import random
from diffprivlib.mechanisms import Laplace
from config import GAMMA, EPSILON_MIN


def compute_effective_epsilon(
    base_epsilon: float,
    risk_score: float,
    gamma: float = GAMMA,
    min_epsilon: float = EPSILON_MIN,
) -> float:
    """
    Calculate dynamic effective epsilon coupled to live inference risk (Objective O1).

    Parameters
    ----------
    base_epsilon : float
        Remaining or role base privacy budget.
    risk_score : float
        Normalized live inference/triangulation risk r(u, q) in [0, 1).
    gamma : float
        Coupling sensitivity exponent (default from config).
    min_epsilon : float
        Lower bound floor for graceful degradation.

    Returns
    -------
    float
        Effective epsilon eps_eff >= min_epsilon.
    """
    r_clamped = max(0.0, min(float(risk_score), 0.9999))
    eff = base_epsilon * math.pow(1.0 - r_clamped, gamma)
    return round(max(eff, min_epsilon), 4)


def compute_noise_scale(sensitivity: float, effective_epsilon: float) -> float:
    """
    Calculate the Laplace scale parameter b = Delta_f / eps_eff.
    Variance of Lap(b) is 2 * b^2.
    """
    safe_eps = max(effective_epsilon, 1e-6)
    return round(sensitivity / safe_eps, 4)


def add_laplace_noise(
    value: float,
    epsilon: float,
    sensitivity: float = 1.0,
) -> float:
    """
    Apply Laplace noise to a single numeric value using diffprivlib
    with stable fallback.

    Parameters
    ----------
    value : float
        The true aggregate value (e.g. COUNT, AVG, SUM).
    epsilon : float
        Privacy budget allocated for this value.
    sensitivity : float
        Global query sensitivity (Delta_f). Defaults to 1.0.

    Returns
    -------
    float
        The differentially private noised value.
    """
    safe_eps = max(epsilon, 1e-4)
    try:
        mechanism = Laplace(epsilon=safe_eps, sensitivity=sensitivity)
        noised = mechanism.randomise(value)
        return round(float(noised), 4)
    except Exception:
        # Fallback to direct inverse-CDF Laplace sampling: Lap(b) = -b * sgn(u) * ln(1 - 2|u|)
        scale = sensitivity / safe_eps
        u = random.uniform(-0.499999, 0.499999)
        sign = 1.0 if u >= 0 else -1.0
        noise = -scale * sign * math.log(1.0 - 2.0 * abs(u))
        return round(float(value + noise), 4)


def add_noise_to_row(
    row: dict,
    epsilon: float,
    sensitivity: float = 1.0,
) -> dict:
    """
    Add Laplace noise to numeric fields in a single row.
    Non-numeric fields (e.g. category, strings) pass through untouched.
    """
    noised_row: dict = {}
    for key, val in row.items():
        if isinstance(val, (int, float)):
            noised_row[key] = add_laplace_noise(float(val), epsilon, sensitivity)
        else:
            noised_row[key] = val
    return noised_row


def add_noise_to_resultset(
    rows: list[dict],
    epsilon: float,
    sensitivity: float = 1.0,
) -> list[dict]:
    """
    Apply calibrated Laplace noise across an entire result set.
    The effective epsilon is composed evenly across rows under sequential composition.
    """
    if not rows:
        return rows

    per_row_epsilon = max(epsilon / len(rows), EPSILON_MIN)
    return [
        add_noise_to_row(row, per_row_epsilon, sensitivity)
        for row in rows
    ]
