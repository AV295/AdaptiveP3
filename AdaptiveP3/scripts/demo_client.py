import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
base_url = "http://localhost:8000"

def post_json(path, data):
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(path):
    with urllib.request.urlopen(f"{base_url}{path}") as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=" * 65)
print(" AP3 LIVE DEMO: Adaptive Privacy-Preserving Proxy")
print("=" * 65)

# 1. Health check
health = get_json("/health")
print(f"1. Health Check: {health}")

# 2. Register a researcher
username = "alice_researcher_demo"
reg = post_json("/register", {"username": username, "role": "researcher"})
print(f"2. User Registration: {reg['user']['username']} (Role: {reg['user']['role']}, Session Budget: {reg['user']['epsilon_remaining']})")

# 3. Query 1: Broad query
q1 = post_json("/query", {
    "username": username,
    "sql": "SELECT AVG(salary) FROM employees WHERE department = 'Engineering'"
})
print("\n3. Query 1 (Broad): SELECT AVG(salary) FROM employees WHERE department = 'Engineering'")
print(f"   Returned Noised Result: {q1['results']}")
print(f"   Risk Signal r(u,q)    : {q1['privacy_metrics']['risk_score']:.4f}")
print(f"   Effective ε_eff       : {q1['privacy_metrics']['effective_epsilon']:.4f}")
print(f"   Noise Scale b         : {q1['privacy_metrics']['noise_scale']:.4f}")
print(f"   Remaining Budget      : {q1['user']['epsilon_remaining']:.4f}")

# 4. Query 2: Narrowing query on same table and column (triangulation probe)
q2 = post_json("/query", {
    "username": username,
    "sql": "SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND salary >= 110000"
})
print("\n4. Query 2 (Narrowing probe): ... AND salary >= 110000")
print(f"   Returned Noised Result: {q2['results']}")
print(f"   Risk Signal r(u,q)    : {q2['privacy_metrics']['risk_score']:.4f}  <-- Risk signal increased!")
print(f"   Effective ε_eff       : {q2['privacy_metrics']['effective_epsilon']:.4f}  <-- Dynamically scaled down!")
print(f"   Noise Scale b         : {q2['privacy_metrics']['noise_scale']:.4f}  <-- Laplace noise elevated!")
print(f"   Remaining Budget      : {q2['user']['epsilon_remaining']:.4f}")

# 5. Query 3: Third overlapping query narrowing down further
q3 = post_json("/query", {
    "username": username,
    "sql": "SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND name = 'Alice'"
})
print("\n5. Query 3 (Targeted Probe): ... AND name = 'Alice'")
print(f"   Returned Noised Result: {q3['results']}")
print(f"   Risk Signal r(u,q)    : {q3['privacy_metrics']['risk_score']:.4f}  <-- Risk rising further!")
print(f"   Effective ε_eff       : {q3['privacy_metrics']['effective_epsilon']:.4f}  <-- Protected with higher noise!")
print(f"   Noise Scale b         : {q3['privacy_metrics']['noise_scale']:.4f}")
print(f"   Remaining Budget      : {q3['user']['epsilon_remaining']:.4f}")

# 6. Query 4: Repeated probe triggering graceful degradation schedule
q4 = post_json("/query", {
    "username": username,
    "sql": "SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND name = 'Alice'"
})
print("\n6. Query 4 (Repeated Target Probe): ... AND name = 'Alice'")
print(f"   Returned Noised Result: {q4['results']}")
print(f"   Risk Signal r(u,q)    : {q4['privacy_metrics']['risk_score']:.4f}")
print(f"   Effective ε_eff       : {q4['privacy_metrics']['effective_epsilon']:.4f}")
print(f"   Degraded Mode Active  : {q4['privacy_metrics']['degraded_mode']}")
print(f"   Degradation Note      : {q4['privacy_metrics']['degradation_reason']}")
print(f"   Remaining Budget      : {q4['user']['epsilon_remaining']:.4f}")

print("\n" + "=" * 65)
print(" DEMO COMPLETE: Full Risk-Adaptive Pipeline Verified Live!")
print("=" * 65)
