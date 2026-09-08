"""
AP3 — Attribute-Based Access Control (ABAC) & Privacy Budgeting
=================================================================
Manages role-based privacy budgets (ε), handles sequential privacy loss
composition, and enables graceful degradation when remaining budget
approaches exhaustion (Slide 7 — O1, O2, O3).
"""

from models.user import User, UserRole
from config import ROLE_PRIVACY_BUDGETS, EPSILON_MIN


def get_initial_budget(role: UserRole) -> float:
    """Return the default privacy budget (ε) for a given role."""
    return ROLE_PRIVACY_BUDGETS.get(role, 1.0)


def has_budget(user: User, cost: float = EPSILON_MIN) -> bool:
    """
    Check whether the user has positive remaining privacy budget.
    """
    return user.epsilon_remaining > 0.0 and user.epsilon_remaining >= cost


def deduct_budget(user: User, privacy_loss: float) -> tuple[User, bool]:
    """
    Deduct the actual composed privacy loss (eps_eff) from the user's budget.
    Under the graceful degradation schedule (Objective O2), if the remaining
    budget is depleted, the query is not rejected; instead, remaining budget
    is clamped at 0.0 and is_degraded is set to True.

    Parameters
    ----------
    user : User
        Current user state.
    privacy_loss : float
        The effective epsilon (eps_eff) consumed by the query.

    Returns
    -------
    tuple[User, bool]
        (Updated user copy with new epsilon_remaining, was_degraded flag)
    """
    if user.epsilon_remaining <= 0.0:
        # Budget already exhausted — degraded mode active
        return user, True

    new_budget = max(0.0, round(user.epsilon_remaining - privacy_loss, 4))
    was_degraded = new_budget <= 0.0

    updated_user = user.model_copy(
        update={"epsilon_remaining": new_budget}
    )
    return updated_user, was_degraded
