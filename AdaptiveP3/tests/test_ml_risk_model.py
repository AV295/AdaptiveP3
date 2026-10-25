"""
AP3 — Automated Test Suite for ML Trajectory Risk Model
========================================================
Validates trajectory feature extraction, ensemble classification,
hybrid arbitration, and dynamic DP coupling.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from core.trajectory_extractor import extract_trajectory_features, FEATURE_NAMES
from core.ml_risk_model import evaluate_ml_risk, MLTrajectoryModel
from core.inference_tracker import assess_inference_risk


def test_trajectory_feature_extraction():
    """Verify feature extractor generates all 15 expected normalized features."""
    vec, feat_dict = extract_trajectory_features(
        curr_tables=["employees"],
        curr_columns=["salary"],
        curr_predicates=["department = 'Engineering'"],
        curr_has_where=True,
        curr_aggregates=["AVG"],
        history_queries=[],
    )
    assert len(vec) == 15
    assert len(feat_dict) == 15
    assert set(feat_dict.keys()) == set(FEATURE_NAMES)
    assert feat_dict["has_where"] == 1.0
    assert feat_dict["curr_pred_count"] == 1.0


def test_ml_model_prediction():
    """Verify ML model singleton loads and predicts expected patterns."""
    model = MLTrajectoryModel.get_instance()
    assert model.classifier is not None
    assert model.regressor is not None

    # Test broad analytical query
    res = model.predict(
        tables=["employees"],
        columns=["salary"],
        predicates=["department = 'Engineering'"],
        has_where=True,
        aggregates=["AVG"],
        history_queries=[],
    )
    assert res.attack_pattern in ("BENIGN", "TRIANGULATION", "DIFFERENCING", "TRACKER")
    assert 0.0 <= res.ml_risk_score <= 1.0
    assert 0.0 <= res.confidence <= 1.0


def test_differencing_attack_detection():
    """Verify complementary pair triggers differencing detection."""
    from db.history_store import record_query
    record_query(
        username="diff_tester",
        tables=["employees"],
        columns=["salary"],
        predicates=["department = 'Engineering'"],
        has_where=True,
        raw_sql="SELECT SUM(salary) FROM employees WHERE department = 'Engineering'",
        risk_score=0.1,
        effective_epsilon=1.0,
    )
    risk = assess_inference_risk(
        username="diff_tester",
        tables=["employees"],
        columns=["salary"],
        predicates=["department = 'Engineering'", "id != 1002"],
        has_where=True,
        raw_sql="SELECT SUM(salary) FROM employees WHERE department = 'Engineering' AND id != 1002",
        aggregates=["SUM"],
    )
    assert risk.attack_pattern == "DIFFERENCING"
    assert risk.risk_score >= 0.70


def test_api_hybrid_metrics_returned():
    """Verify /query endpoint includes ML telemetry in privacy_metrics."""
    client = TestClient(app)
    client.post("/register", json={"username": "metric_tester", "role": "researcher"})
    resp = client.post("/query", json={
        "username": "metric_tester",
        "sql": "SELECT AVG(salary) FROM employees WHERE department = 'Engineering'",
    })
    assert resp.status_code == 200
    data = resp.json()
    metrics = data["privacy_metrics"]
    assert "ml_risk" in metrics
    assert "heuristic_risk" in metrics
    assert "attack_pattern" in metrics
    assert "ml_confidence" in metrics
    assert "top_factors" in metrics


if __name__ == "__main__":
    test_trajectory_feature_extraction()
    test_ml_model_prediction()
    test_differencing_attack_detection()
    test_api_hybrid_metrics_returned()
    print("All ML risk model unit & integration tests passed successfully!")
