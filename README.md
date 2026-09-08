# AP3 — Adaptive Privacy-Preserving Proxy

> A risk-adaptive differential-privacy SQL middleware proxy that couples live inference-risk tracking to differential-privacy budget consumption, replacing static per-role budgets with a risk-adaptive control loop so query answers degrade gracefully under rising triangulation risk instead of being denied outright.

---

## Core Security & Privacy Innovations (SCOPE Review 1)

| # | Concept | Formulation & Implementation |
|---|---------|-------------------------------|
| 1 | **Formalized Triangulation Signal $r(u, q)$** | Continuous risk signal $r(u, q) \in [0, 1)$ computed across query history via subpopulation overlap (table match, column Jaccard, predicate overlap) and exponential time decay: $e^{-\lambda \Delta t}$. |
| 2 | **Risk-to-$\varepsilon$ Dynamic Coupling** | Dynamically scales effective noise budget per query: $\varepsilon_{\text{eff}}(u, q) = \max\left(\varepsilon_{\min}, \, \varepsilon_{\text{role}} \cdot (1 - r(u, q))^\gamma\right)$. |
| 3 | **Graceful Degradation vs. Denial** | Non-leaking graceful degradation: when budget is low or triangulation risk spikes, answers are perturbed with monotonically increasing noise ($\varepsilon \to \varepsilon_{\min}$) rather than leaking state through hard HTTP 403/429 denial. |
| 4 | **Sequential Privacy Composition** | Deducts actual composed privacy loss ($\varepsilon_{\text{eff}}$) per query from the user's role budget session. |
| 5 | **SQL Injection Guard** | AST multi-statement blocking and injection fingerprint detection via `sqlparse`. |

---

## Project Structure

```
AdaptiveP3/
├── README.md
├── Requirements.txt
├── config.py                # Centralized settings (gamma, lambda decay, role budgets)
├── main.py                  # FastAPI entry point & API routes
├── models/
│   ├── __init__.py
│   └── user.py              # Pydantic User model + UserRole enum
├── core/
│   ├── __init__.py
│   ├── abac.py              # Budget deduction & graceful degradation checks
│   ├── differential_privacy.py  # Risk-to-ε coupling & Laplace noise engine
│   ├── inference_tracker.py     # Continuous triangulation risk signal r(u, q)
│   └── query_analyzer.py       # SQL AST, subpopulation predicates, and sensitivity
├── db/
│   ├── __init__.py
│   ├── postgres.py          # PostgreSQL query executor
│   └── history_store.py     # SQLite history store with predicate & risk persistence
├── middleware/
│   ├── __init__.py
│   └── proxy.py             # Full unified risk-adaptive security pipeline
├── scripts/
│   ├── 01-create-db.sql     # PostgreSQL database initialization
│   ├── 02-seed.sql          # Sample data seed script
│   └── eval_benchmarks.py   # Privacy-utility, attack simulation & latency benchmarks
└── tests/
    └── test_api_guards.py   # Security guard integration tests
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r Requirements.txt

# 2. Set PostgreSQL connection (or use defaults in config.py)
export POSTGRES_HOST=localhost
export POSTGRES_DB=ap3_db
export POSTGRES_USER=ap3_user
export POSTGRES_PASSWORD=ap3_password

# 3. Run the proxy
uvicorn main:app --reload --port 8000
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | Service identity & health status |
| `GET`  | `/health` | Lightweight health check |
| `POST` | `/register` | Register user and allocate initial role privacy budget |
| `GET`  | `/budget/{username}` | Query remaining $\varepsilon$ privacy budget |
| `POST` | `/query` | **Main proxy** — submit SQL for adaptive inspection and DP execution |

### Sample Response (`POST /query`)

```json
{
  "status": "success",
  "user": {
    "username": "alice",
    "role": "researcher",
    "epsilon_remaining": 9.3874
  },
  "query_analysis": {
    "tables": ["employees"],
    "columns": ["age", "department", "salary"],
    "predicates": ["department='engineering'", "age>30"],
    "aggregates": ["avg"],
    "sensitivity": 3.75,
    "is_aggregate": true
  },
  "privacy_metrics": {
    "risk_score": 0.2173,
    "raw_risk": 0.6997,
    "effective_epsilon": 0.6126,
    "noise_scale": 6.1214,
    "degraded_mode": false,
    "degradation_reason": null,
    "inference_overlap_count": 2,
    "subpopulation_overlap": {
      "max_single_overlap": 0.7000,
      "accumulated_risk": 0.6997,
      "overlap_count": 2
    }
  },
  "results": [
    {
      "avg": 84210.4512
    }
  ],
  "privacy_note": "Laplace noise applied with effective epsilon=0.6126 (noise scale b=6.1214)."
}
```

---

## Running Evaluation Benchmarks (Objective O4)

Run the automated evaluation benchmark suite:

```bash
python scripts/eval_benchmarks.py
```

This script evaluates and prints:
1. **Privacy–Utility Frontier:** Empirical MAE and RMSE against theoretical Laplace standard deviation: $\sigma = \sqrt{2} \cdot \frac{\Delta f}{\varepsilon}$.
2. **Triangulation Attack Simulation:** Direct comparison between the **Static Baseline** (which leaks through hard denial at threshold) vs. **AP3 Adaptive Proxy** (which smoothly decreases $\varepsilon_{\text{eff}}$ as predicates narrow, blinding reconstruction).
3. **Proxy Middleware Overhead:** Millisecond latency breakdown (AST parsing, subpopulation risk evaluation, and Laplace noise generation; Target $< 15\text{ ms}$, Achieved $\sim 2.5\text{ ms}$).
