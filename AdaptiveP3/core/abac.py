"""
AP3 — Attribute-Based Access Control (ABAC)
============================================
Manages per-role privacy budgets (ε) and enforces budget constraints
before queries are executed.
"""

from models.user import User, UserRole
from config import ROLE_PRIVACY_BUDGETS


def get_initial_budget(role: UserRole) -> float:
    """Return the default privacy budget (ε) for a given role."""
    return ROLE_PRIVACY_BUDGETS.get(role, 1.0)


def has_budget(user: User, query_cost: float) -> bool:
    """
    Check whether the user's remaining ε is sufficient to cover
    the sensitivity cost of a query.
    """
    return user.epsilon_remaining >= query_cost


def deduct_budget(user: User, query_cost: float) -> User:
    """
    Return a **new** User with epsilon_remaining reduced by query_cost.

    Raises
    ------
    ValueError
        If the user does not have enough remaining budget.
    """
    if not has_budget(user, query_cost):
        raise ValueError(
            f"User '{user.username}' has insufficient privacy budget. "
            f"Remaining: {user.epsilon_remaining:.4f}, Required: {query_cost:.4f}"
        )
    return user.model_copy(
        update={"epsilon_remaining": round(user.epsilon_remaining - query_cost, 4)}
    )
