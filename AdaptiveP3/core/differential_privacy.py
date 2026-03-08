"""
AP3 — Differential Privacy Engine
===================================
Applies the **Laplace Mechanism** (via IBM's *diffprivlib*) to numeric
query results so that individual records cannot be inferred from the output.

Theory refresher
----------------
For a numeric function f with global sensitivity Δf, the Laplace Mechanism
adds noise drawn from  Lap(Δf / ε)  to the true answer.

* Higher ε  →  less noise  →  less privacy.
* Lower  ε  →  more noise  →  stronger privacy guarantee.
"""

from diffprivlib.mechanisms import Laplace


def add_laplace_noise(
    value: float,
    epsilon: float,
    sensitivity: float = 1.0,
) -> float:
    """
    Apply Laplace noise to a single numeric value.

    Parameters
    ----------
    value : float
        The true aggregate value (e.g. a COUNT result).
    epsilon : float
        Privacy budget allocated for this value.
    sensitivity : float
        Query sensitivity (Δf).  Defaults to 1.0 (correct for COUNT).

    Returns
    -------
    float
        The differentially-private (noised) value.
    """
    mechanism = Laplace(epsilon=epsilon, sensitivity=sensitivity)
    noised = mechanism.randomise(value)
    return round(noised, 4)


def add_noise_to_row(
    row: dict,
    epsilon: float,
    sensitivity: float = 1.0,
) -> dict:
    """
    Add Laplace noise to every **numeric** field in a single result row.
    Non-numeric fields pass through unchanged.
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
    Apply Laplace noise across an entire result set.

    The total ε budget is split evenly across rows so that the
    *sequential composition* theorem still guarantees overall ε-DP.
    """
    if not rows:
        return rows

    per_row_epsilon = epsilon / len(rows)
    return [
        add_noise_to_row(row, per_row_epsilon, sensitivity)
        for row in rows
    ]
