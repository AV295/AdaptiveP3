"""
AP3 — Adaptive Privacy-Preserving Proxy
=========================================
FastAPI application entry point. Acts as an intelligent middleware proxy
between database clients and PostgreSQL, enforcing:

1. Live Risk-to-Epsilon Coupling: eps_eff = eps_role * (1 - r(u, q))^gamma
2. Monotonically Increasing Graceful Degradation Schedule (replaces hard query denial)
3. Formalized Subpopulation Triangulation Signal r(u, q) in [0, 1)
4. Attribute-Based Access Control (ABAC) with Sequential Privacy Composition
5. AST-based SQL Injection & Piggyback Query Guard
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from models.user import User, UserRole
from core.abac import get_initial_budget
from middleware.proxy import process_query
from core.swagger_theme import get_custom_swagger_html
from db.history_store import get_user_history

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-16s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("ap3")

# ── Interactive OpenAPI & Swagger Descriptions ───────────────────────
API_DESCRIPTION = """
### Welcome to AP3 (Adaptive Privacy-Preserving Proxy)

AP3 replaces rigid static privacy budgets and abrupt query-denial thresholds with a **risk-adaptive control loop** evaluated in real-time on relational aggregate queries.

---

### 🚀 First-Time Explorer Walkthrough (4 Easy Steps):

1. **Register a User (`POST /register`)**:
   - Register a `researcher` (nominal budget: 10.0 $\\varepsilon$) or `guest` (nominal budget: 2.0 $\\varepsilon$).
2. **Submit Broad Aggregate (`POST /query`)**:
   - Query: `SELECT AVG(salary) FROM employees WHERE department = 'Engineering'`
   - Notice: $r(u, q) \\approx 0.0$, effective budget $\\varepsilon_{\\text{eff}} \\approx 1.0$, low noise perturbation.
3. **Simulate a Triangulation Attack (`POST /query`)**:
   - Narrow subpopulation: `SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND salary >= 110000`
   - Narrow further to isolate a target: `SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND name = 'Alice'`
   - Observe: Triangulation risk $r(u, q)$ climbs, and $\\varepsilon_{\\text{eff}} = \\varepsilon_{\\text{role}} \\cdot (1 - r)^\\gamma$ dynamically reduces, scaling up noise ($b = \\frac{\\Delta f}{\\varepsilon_{\\text{eff}}}$) to protect the target.
4. **Inspect Audit History & Degradation (`GET /audit/{username}`)**:
   - View past query predicates, risk trajectory, and graceful degradation indicators.

---

### 🔬 Core Mathematical Formulation:
- **Continuous Triangulation Risk:** $r(u, q) = 1 - \\exp\\left(-\\alpha \\sum_{i} \\text{Overlap}(q, q_i) e^{-\\lambda \\Delta t_i}\\right) \\in [0, 1)$
- **Dynamic Coupling:** $\\varepsilon_{\\text{eff}}(u, q) = \\max\\left(\\varepsilon_{\\min}, \\, \\varepsilon_{\\text{role}} \\cdot (1 - r(u, q))^\\gamma\\right)$
- **Calibrated Laplace Noise:** $b = \\frac{\\Delta f}{\\varepsilon_{\\text{eff}}}; \\quad Y \\sim \\text{Lap}(b)$
"""

# ── FastAPI Application ──────────────────────────────────────────────
app = FastAPI(
    title="AP3 — Adaptive Privacy-Preserving Proxy",
    description=API_DESCRIPTION,
    version="1.0.0",
    docs_url=None,  # Handled via custom styled /docs route
    redoc_url=None,
)

# ── In-memory user store ─────────────────────────────────────────────
_users: dict[str, User] = {}


# ── Request / Response Schemas ───────────────────────────────────────

class RegisterRequest(BaseModel):
    """Payload for user registration."""
    username: str = Field(
        ...,
        description="Unique user handle",
        examples=["alice_researcher"]
    )
    role: UserRole = Field(
        default=UserRole.RESEARCHER,
        description="Role determining privacy budget ceiling and nominal per-query epsilon",
        examples=["researcher"]
    )


class QueryRequest(BaseModel):
    """Payload for proxy query execution."""
    username: str = Field(
        ...,
        description="Registered username submitting the query",
        examples=["alice_researcher"]
    )
    sql: str = Field(
        ...,
        description="SQL aggregate or analytics query to process through the adaptive privacy pipeline",
        examples=["SELECT AVG(salary) FROM employees WHERE department = 'Engineering'"]
    )


# ── Visual UI & Custom Swagger Routes ────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["interface"])
def visual_dashboard():
    """Interactive visual dashboard & telemetry playground for AP3."""
    html_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>AP3 Proxy Running</h1><p><a href='/docs'>Go to API Docs</a></p>")


@app.get("/playground", response_class=HTMLResponse, tags=["interface"])
def playground_alias():
    """Alias for visual dashboard."""
    return visual_dashboard()


@app.get("/docs", include_in_schema=False)
def custom_swagger_docs():
    """Enhanced dark-mode Swagger UI with step-by-step guidance banner."""
    return HTMLResponse(content=get_custom_swagger_html(
        openapi_url=app.openapi_url,
        title="AP3 — Interactive Guided Explorer"
    ))


# ── API Endpoints ────────────────────────────────────────────────────

@app.get("/health", tags=["status"])
def health_check():
    """Lightweight operational health probe."""
    return {
        "status": "healthy",
        "service": "AP3 — Adaptive Privacy-Preserving Proxy",
        "version": "1.0.0"
    }


@app.post("/register", tags=["users"])
def register_user(req: RegisterRequest):
    """
    Register a new user and assign them the initial privacy budget (ε) for their role.
    
    - **admin**: 20.0 ε lifetime budget
    - **researcher**: 10.0 ε lifetime budget
    - **guest**: 2.0 ε lifetime budget
    """
    if req.username in _users:
        return {
            "message": "User already registered.",
            "user": _users[req.username].model_dump(),
        }

    budget = get_initial_budget(req.role)
    user = User(username=req.username, role=req.role, epsilon_remaining=budget)
    _users[req.username] = user

    logger.info(
        "Registered user '%s'  role=%s  ε=%.2f",
        req.username,
        req.role,
        budget,
    )
    return {"message": "User registered successfully.", "user": user.model_dump()}


@app.get("/budget/{username}", tags=["users"])
def get_budget(username: str):
    """Query remaining cumulative privacy budget for a given username."""
    user = _users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found. Please register first.")
    return {
        "username": user.username,
        "role": user.role,
        "epsilon_remaining": user.epsilon_remaining,
    }


@app.get("/audit/{username}", tags=["audit"])
def get_audit_history(username: str, limit: int = 20):
    """
    Retrieve live query history and triangulation metrics for a user.
    Shows extracted subpopulation predicates, computed risk r(u, q), and consumed ε_eff.
    """
    return get_user_history(username, limit=limit)


@app.post("/query", tags=["proxy"])
def proxy_query(req: QueryRequest):
    """
    **Main Privacy Proxy Endpoint.**
    
    Processes incoming SQL through the 8-stage risk-adaptive pipeline:
    1. AST parsing & fine-grained subpopulation predicate extraction
    2. SQL injection pattern & piggyback attack blocking
    3. Role-based statement restriction (SELECT only for non-admin)
    4. Subpopulation inference & triangulation risk scoring: $r(u, q) \\in [0, 1)$
    5. Dynamic risk-to-$\\varepsilon$ coupling & graceful degradation schedule
    6. Execution on PostgreSQL
    7. Calibrated Laplace noise injection on aggregates
    8. Composed budget deduction & SQLite audit persistence
    """
    user = _users.get(req.username)
    if not user:
        # Auto-register as researcher for frictionless first-time testing
        budget = get_initial_budget(UserRole.RESEARCHER)
        user = User(username=req.username, role=UserRole.RESEARCHER, epsilon_remaining=budget)
        _users[req.username] = user

    result = process_query(user, req.sql)

    # Persist updated budget state
    _users[req.username] = User(**result["user"])

    return result
