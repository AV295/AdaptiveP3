# AP3 — Adaptive Privacy-Preserving Proxy

> A FastAPI middleware that sits between clients and a PostgreSQL database,
> enforcing **Differential Privacy**, **Attribute-Based Access Control (ABAC)**,
> and **Inference Attack Prevention** on every query.

---

## Core Security Concepts

| # | Concept | Implementation |
|---|---------|----------------|
| 1 | **ABAC** | Role-based privacy budgets (ε): Admin = 10, Researcher = 5, Guest = 1 |
| 2 | **Differential Privacy** | Laplace Mechanism via `diffprivlib` applied to aggregate results |
| 3 | **Inference Prevention** | SQLite query-history tracking; blocks after repeated overlapping queries |
| 4 | **SQL Injection Guard** | Heuristic pattern detection + multi-statement blocking via `sqlparse` |

## Project Structure

```
AdaptiveP3/
├── README.md
├── Requirements.txt
├── main.py                  # FastAPI entry point
├── config.py                # Centralised settings
├── models/
│   ├── __init__.py
│   └── user.py              # Pydantic User model + UserRole enum
├── core/
│   ├── __init__.py
│   ├── abac.py              # Budget checks & deduction
│   ├── differential_privacy.py  # Laplace noise engine
│   ├── inference_tracker.py     # Triangulation detection
│   └── query_analyzer.py       # SQL parsing & sensitivity scoring
├── db/
│   ├── __init__.py
│   ├── postgres.py          # psycopg2 query executor
│   └── history_store.py     # SQLite history for inference tracking
└── middleware/
    ├── __init__.py
    └── proxy.py             # Full security pipeline orchestration
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r Requirements.txt

# 2. Set PostgreSQL connection (or use defaults in config.py)
export POSTGRES_HOST=localhost
export POSTGRES_DB=ap3_db
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# 3. Run the proxy
uvicorn main:app --reload --port 8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | Service identity |
| `GET`  | `/health` | Health probe |
| `POST` | `/register` | Register a user with a role |
| `GET`  | `/budget/{username}` | Check remaining ε budget |
| `POST` | `/query` | **Main proxy** — submit SQL for execution |

### Example Usage

```bash
# Register a guest user (ε = 1.0)
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "role": "guest"}'

# Submit an aggregate query (Laplace noise will be applied)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "sql": "SELECT COUNT(*) FROM employees"}'

# Check remaining budget
curl http://localhost:8000/budget/alice
```

## How the Pipeline Works

```
Client → POST /query
           │
           ├─ 1. Parse SQL (sqlparse)
           ├─ 2. Injection detection
           ├─ 3. Role-based statement restriction
           ├─ 4. Inference risk assessment (SQLite history)
           ├─ 5. ABAC budget check (ε ≥ query cost?)
           ├─ 6. Execute on PostgreSQL
           ├─ 7. Apply Laplace noise to aggregates
           └─ 8. Deduct ε budget → return results
```