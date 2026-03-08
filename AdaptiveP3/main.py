"""
AP3 — Adaptive Privacy-Preserving Proxy
=========================================
FastAPI entry point.  Acts as a middleware proxy between clients and a
PostgreSQL database, enforcing:

* **ABAC** — role-based privacy budgets (ε)
* **Differential Privacy** — Laplace noise on aggregate results
* **Inference Prevention** — query-history tracking to block triangulation

Run
---
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models.user import User, UserRole
from core.abac import get_initial_budget
from middleware.proxy import process_query

import logging

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-16s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("ap3")

# ── FastAPI Application ──────────────────────────────────────────────
app = FastAPI(
    title="AP3 — Adaptive Privacy-Preserving Proxy",
    description=(
        "A middleware proxy that intercepts SQL queries, applies "
        "Differential Privacy (Laplace Mechanism), enforces Attribute-Based "
        "Access Control (ABAC), and prevents Inference Attacks."
    ),
    version="0.1.0",
)

# ── In-memory user store (swap for a real auth backend in production) ─
_users: dict[str, User] = {}


# ── Request / Response Schemas ───────────────────────────────────────

class RegisterRequest(BaseModel):
    """Payload for user registration."""
    username: str
    role: UserRole


class QueryRequest(BaseModel):
    """Payload for the /query proxy endpoint."""
    username: str
    sql: str


# ── Endpoints ────────────────────────────────────────────────────────

@app.get("/", tags=["status"])
def root():
    """Service identity check."""
    return {
        "service": "AP3 — Adaptive Privacy-Preserving Proxy",
        "status": "running",
    }


@app.get("/health", tags=["status"])
def health_check():
    """Lightweight health probe."""
    return {"status": "healthy"}


@app.post("/register", tags=["users"])
def register_user(req: RegisterRequest):
    """
    Register a new user and assign them the default privacy budget (ε)
    for their role.
    """
    if req.username in _users:
        raise HTTPException(status_code=409, detail="User already registered.")

    budget = get_initial_budget(req.role)
    user = User(username=req.username, role=req.role, epsilon_remaining=budget)
    _users[req.username] = user

    logger.info(
        "Registered user '%s'  role=%s  ε=%.2f",
        req.username,
        req.role,
        budget,
    )
    return {"message": "User registered.", "user": user.model_dump()}


@app.get("/budget/{username}", tags=["users"])
def get_budget(username: str):
    """Return the remaining privacy budget for *username*."""
    user = _users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "username": user.username,
        "role": user.role,
        "epsilon_remaining": user.epsilon_remaining,
    }


@app.post("/query", tags=["proxy"])
def proxy_query(req: QueryRequest):
    """
    **Main proxy endpoint.**

    Accepts a SQL query and the requesting username, then runs the full
    security pipeline:

    1. Parse & analyse the query (sensitivity, aggregates, tables).
    2. Block SQL injection attempts.
    3. Assess inference risk via query-history overlap.
    4. Check ABAC privacy budget.
    5. Execute the query against PostgreSQL.
    6. Apply Laplace noise to aggregate results.
    7. Deduct the ε budget and return sanitized results.
    """
    user = _users.get(req.username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please register first via POST /register.",
        )

    result = process_query(user, req.sql)

    # Persist the updated budget back into the in-memory store
    _users[req.username] = User(**result["user"])

    return result
