import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app, _users
from models.user import User, UserRole

client = TestClient(app)
_users["alice"] = User(username="alice", role=UserRole.RESEARCHER, epsilon_remaining=10.0)

# 1. Test SQL injection guard
r_inj = client.post("/query", json={"username": "alice", "sql": "SELECT * FROM employees WHERE 1=1"})
print("Injection guard response:", r_inj.status_code, r_inj.json())

# 2. Test non-select guard for researcher
r_non_sel = client.post("/query", json={"username": "alice", "sql": "DROP TABLE employees"})
print("Non-select guard response:", r_non_sel.status_code, r_non_sel.json())
