"""
AP3 — User Model
=================
Pydantic model for a proxy user with role-based privacy budgets.
"""

from pydantic import BaseModel
from enum import Enum


class UserRole(str, Enum):
    """Supported ABAC roles. Each role maps to a default epsilon budget."""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    GUEST = "guest"


class User(BaseModel):
    """
    Represents a proxy user.

    Attributes
    ----------
    username : str
        Unique identifier for the user.
    role : UserRole
        ABAC role that determines the initial privacy budget.
    epsilon_remaining : float
        Remaining differential-privacy budget (ε). Decreases with every query.
    """
    username: str
    role: UserRole
    epsilon_remaining: float

    class Config:
        use_enum_values = True
