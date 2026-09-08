"""
AP3 Configuration
=================
Centralized settings for the Adaptive Privacy-Preserving Proxy.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── PostgreSQL Connection ────────────────────────────────────────────
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "ap3_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "ap3_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ap3_password")

# ── ABAC: Privacy budget defaults per role ───────────────────────────
# Total session privacy budget (cumulative ceiling)
ROLE_PRIVACY_BUDGETS: dict[str, float] = {
    "admin": 20.0,       # High lifetime budget
    "researcher": 10.0,   # Medium lifetime budget
    "guest": 2.0,        # Low lifetime budget
}

# Nominal per-query epsilon (eps_role in formula: eps_eff = eps_role * (1 - r)^gamma)
ROLE_QUERY_EPSILON: dict[str, float] = {
    "admin": 2.0,
    "researcher": 1.0,
    "guest": 0.5,
}


# ── Inference & Triangulation Tracking ─────────────────────────────────
# Max window (seconds) for historical query tracking
INFERENCE_WINDOW_SECONDS = 3600.0
# Exponential time decay rate (lambda) for older queries: exp(-lambda * delta_t)
LAMBDA_DECAY = 0.0005
# Overlap component weights (sum to 1.0)
RISK_WEIGHT_TABLE = 0.30
RISK_WEIGHT_COLUMN = 0.30
RISK_WEIGHT_PREDICATE = 0.40

# ── Risk-to-Epsilon Coupling & Graceful Degradation ───────────────────
# Sensitivity coupling exponent gamma in: eps_eff = eps_role * (1 - r)^gamma
GAMMA = 2.0
# Minimum epsilon floor during graceful degradation (prevents infinite noise / denial)
EPSILON_MIN = 0.05
# Risk threshold at which queries enter aggressive graceful degradation
DEGRADATION_RISK_THRESHOLD = 0.85

# ── SQLite History Store ─────────────────────────────────────────────
HISTORY_DB_PATH = os.getenv("HISTORY_DB_PATH", "query_history.db")

