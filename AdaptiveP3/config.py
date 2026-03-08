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

# ── ABAC: Privacy budget (epsilon) defaults per role ─────────────────
# Lower epsilon = more noise = stronger privacy guarantee
ROLE_PRIVACY_BUDGETS: dict[str, float] = {
    "admin": 10.0,       # High budget  — less noise, more accuracy
    "researcher": 5.0,   # Medium budget
    "guest": 1.0,        # Low budget   — heavy noise, strong privacy
}

# ── Inference Tracking ───────────────────────────────────────────────
# Max overlapping queries on the same table(s) within the time window
INFERENCE_QUERY_THRESHOLD = 5
# Time window (seconds) for overlap detection
INFERENCE_WINDOW_SECONDS = 3600.0

# ── SQLite History Store ─────────────────────────────────────────────
HISTORY_DB_PATH = os.getenv("HISTORY_DB_PATH", "query_history.db")
