"""
AP3 — Query Trajectory Synthetic Dataset Generator
===================================================
Generates labeled query session traces simulating both benign analytical
workloads and adversarial inference attacks:
1. BENIGN: Standard business intelligence and exploratory queries
2. TRIANGULATION: Progressive subpopulation narrowing attacks
3. DIFFERENCING: Complementary pair probes isolating individual records
4. TRACKER: Quasi-identifier correlation and tracker queries

Used to train and validate the AP3 machine learning risk model.
"""

import os
import sys
import json
import random
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.trajectory_extractor import extract_trajectory_features, FEATURE_NAMES

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_CSV = os.path.join(DATA_DIR, "query_attack_dataset.csv")

TABLES = ["employees", "salaries", "departments", "projects", "medical_records", "attendance"]
COLUMNS_BY_TABLE = {
    "employees": ["id", "name", "salary", "department", "age", "role", "experience", "gender", "zipcode"],
    "salaries": ["emp_id", "base_salary", "bonus", "tax_bracket", "effective_date"],
    "departments": ["dept_id", "dept_name", "budget", "headcount", "location"],
    "projects": ["project_id", "project_name", "budget", "team_size", "deadline"],
    "medical_records": ["emp_id", "diagnosis", "visit_date", "claim_amount", "insurance_tier"],
    "attendance": ["emp_id", "days_present", "leaves_taken", "overtime_hours"],
}

DEPTS = ["Engineering", "Sales", "Marketing", "Human Resources", "Finance", "Legal", "Operations"]
ROLES = ["Junior", "Mid", "Senior", "Lead", "Director", "VP", "Associate"]
GENDERS = ["M", "F", "Other"]
AGGREGATES = ["COUNT", "AVG", "SUM", "MIN", "MAX"]


def generate_benign_session(session_id: int) -> list[dict]:
    """Generate a realistic sequence of benign BI queries."""
    session_length = random.randint(3, 8)
    queries = []
    base_time = 1700000000.0 + session_id * 5000.0
    curr_time = base_time

    history: list[dict] = []
    for step in range(session_length):
        # Vary tables and columns
        table = random.choice(["employees", "departments", "salaries", "projects"])
        cols = random.sample(COLUMNS_BY_TABLE[table], random.randint(1, 3))
        has_where = random.random() > 0.3
        preds = []
        if has_where:
            if table == "employees":
                if random.random() > 0.5:
                    preds.append(f"department = '{random.choice(DEPTS)}'")
                if random.random() > 0.6:
                    preds.append(f"role = '{random.choice(ROLES)}'")
            elif table == "departments":
                preds.append(f"location = '{random.choice(['NY', 'SF', 'London', 'Berlin'])}'")
            elif table == "projects":
                preds.append(f"team_size > {random.randint(5, 20)}")

        agg = [random.choice(AGGREGATES)]
        dt = random.uniform(30.0, 300.0)
        curr_time += dt

        vec, feat_dict = extract_trajectory_features(
            curr_tables=[table],
            curr_columns=cols,
            curr_predicates=preds,
            curr_has_where=has_where,
            curr_aggregates=agg,
            history_queries=history,
            current_timestamp=curr_time,
        )

        record = {
            "session_id": f"benign_{session_id}",
            "step": step,
            "attack_type": "BENIGN",
            "attack_label": 0,
            "ground_truth_risk": round(random.uniform(0.01, 0.20), 4),
            **feat_dict,
        }
        queries.append(record)

        history.append({
            "tables": [table],
            "columns": cols,
            "predicates": preds,
            "has_where": has_where,
            "timestamp": curr_time,
        })

    return queries


def generate_triangulation_session(session_id: int) -> list[dict]:
    """Generate a sequence of successive narrowing queries targeting an individual."""
    queries = []
    base_time = 1700000000.0 + session_id * 5000.0
    curr_time = base_time

    target_dept = random.choice(DEPTS)
    target_role = random.choice(ROLES)
    target_age = random.randint(28, 55)

    stages = [
        # Stage 0: Broad
        ([], False, 0.05),
        # Stage 1: Department
        ([f"department = '{target_dept}'"], True, 0.25),
        # Stage 2: Dept + Role
        ([f"department = '{target_dept}'", f"role = '{target_role}'"], True, 0.50),
        # Stage 3: Dept + Role + Age range
        ([f"department = '{target_dept}'", f"role = '{target_role}'", f"age >= {target_age - 2}"], True, 0.72),
        # Stage 4: Exact isolate
        ([f"department = '{target_dept}'", f"role = '{target_role}'", f"age = {target_age}"], True, 0.88),
        # Stage 5: Target name probe
        ([f"department = '{target_dept}'", f"role = '{target_role}'", f"age = {target_age}", "name LIKE 'A%'"], True, 0.96),
    ]

    history: list[dict] = []
    for step, (preds, has_where, risk_val) in enumerate(stages):
        table = "employees"
        cols = ["salary", "department"]
        agg = ["AVG"]

        # Fast succession: 2 to 12 seconds between queries
        dt = random.uniform(2.0, 12.0)
        curr_time += dt

        vec, feat_dict = extract_trajectory_features(
            curr_tables=[table],
            curr_columns=cols,
            curr_predicates=preds,
            curr_has_where=has_where,
            curr_aggregates=agg,
            history_queries=history,
            current_timestamp=curr_time,
        )

        label = 0 if step == 0 else 1
        record = {
            "session_id": f"triang_{session_id}",
            "step": step,
            "attack_type": "BENIGN" if step == 0 else "TRIANGULATION",
            "attack_label": label,
            "ground_truth_risk": round(risk_val, 4),
            **feat_dict,
        }
        queries.append(record)

        history.append({
            "tables": [table],
            "columns": cols,
            "predicates": preds,
            "has_where": has_where,
            "timestamp": curr_time,
        })

    return queries


def generate_differencing_session(session_id: int) -> list[dict]:
    """Generate differencing attack pairs/triplets: Q1 (set) and Q2 (set excluding target)."""
    queries = []
    base_time = 1700000000.0 + session_id * 5000.0
    curr_time = base_time

    dept = random.choice(DEPTS)
    target_id = random.randint(1001, 1099)

    stages = [
        # Q1: Broad group
        ([f"department = '{dept}'"], True, 0.20, "BENIGN", 0),
        # Q2: Same group minus target record (Differencing probe!)
        ([f"department = '{dept}'", f"emp_id != {target_id}"], True, 0.85, "DIFFERENCING", 2),
        # Q3: Target record isolated directly
        ([f"emp_id = {target_id}"], True, 0.95, "DIFFERENCING", 2),
    ]

    history: list[dict] = []
    for step, (preds, has_where, risk_val, atype, alabel) in enumerate(stages):
        table = "employees"
        cols = ["salary"]
        agg = ["SUM"]

        dt = random.uniform(1.5, 8.0)
        curr_time += dt

        vec, feat_dict = extract_trajectory_features(
            curr_tables=[table],
            curr_columns=cols,
            curr_predicates=preds,
            curr_has_where=has_where,
            curr_aggregates=agg,
            history_queries=history,
            current_timestamp=curr_time,
        )

        record = {
            "session_id": f"diff_{session_id}",
            "step": step,
            "attack_type": atype,
            "attack_label": alabel,
            "ground_truth_risk": round(risk_val, 4),
            **feat_dict,
        }
        queries.append(record)

        history.append({
            "tables": [table],
            "columns": cols,
            "predicates": preds,
            "has_where": has_where,
            "timestamp": curr_time,
        })

    return queries


def generate_tracker_session(session_id: int) -> list[dict]:
    """Generate quasi-identifier tracker queries cross-referencing auxiliary attributes."""
    queries = []
    base_time = 1700000000.0 + session_id * 5000.0
    curr_time = base_time

    target_zip = random.choice(["94016", "94107", "10001", "02138"])
    target_gender = random.choice(GENDERS)
    target_age = random.randint(30, 50)

    stages = [
        # Query 1: Count in zipcode + gender (checking tracker cardinality)
        ([f"zipcode = '{target_zip}'", f"gender = '{target_gender}'"], ["zipcode", "gender"], ["COUNT"], 0.35, "TRACKER", 3),
        # Query 2: Narrow tracker by age
        ([f"zipcode = '{target_zip}'", f"gender = '{target_gender}'", f"age = {target_age}"], ["zipcode", "age"], ["COUNT"], 0.75, "TRACKER", 3),
        # Query 3: Sensitive attribute query using tracker predicate
        ([f"zipcode = '{target_zip}'", f"gender = '{target_gender}'", f"age = {target_age}"], ["salary"], ["AVG"], 0.92, "TRACKER", 3),
    ]

    history: list[dict] = []
    for step, (preds, cols, agg, risk_val, atype, alabel) in enumerate(stages):
        table = "employees"
        dt = random.uniform(3.0, 15.0)
        curr_time += dt

        vec, feat_dict = extract_trajectory_features(
            curr_tables=[table],
            curr_columns=cols,
            curr_predicates=preds,
            curr_has_where=True,
            curr_aggregates=agg,
            history_queries=history,
            current_timestamp=curr_time,
        )

        record = {
            "session_id": f"tracker_{session_id}",
            "step": step,
            "attack_type": atype,
            "attack_label": alabel,
            "ground_truth_risk": round(risk_val, 4),
            **feat_dict,
        }
        queries.append(record)

        history.append({
            "tables": [table],
            "columns": cols,
            "predicates": preds,
            "has_where": True,
            "timestamp": curr_time,
        })

    return queries


def build_dataset(num_sessions: int = 500) -> None:
    """Generate and write full synthetic query dataset."""
    random.seed(42)
    all_rows = []

    print(f"Generating synthetic query attack dataset with {num_sessions} sessions per category...")
    for s in range(num_sessions):
        all_rows.extend(generate_benign_session(s))
        all_rows.extend(generate_triangulation_session(s))
        all_rows.extend(generate_differencing_session(s))
        all_rows.extend(generate_tracker_session(s))

    fieldnames = [
        "session_id",
        "step",
        "attack_type",
        "attack_label",
        "ground_truth_risk",
    ] + FEATURE_NAMES

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Dataset successfully generated: {OUTPUT_CSV}")
    print(f"Total query instances: {len(all_rows)}")
    # Class breakdown
    counts = {}
    for r in all_rows:
        t = r["attack_type"]
        counts[t] = counts.get(t, 0) + 1
    for k, v in counts.items():
        print(f"  - {k:<15}: {v} queries ({v/len(all_rows)*100:.1f}%)")


if __name__ == "__main__":
    build_dataset(num_sessions=350)
