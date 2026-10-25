"""
AP3 — Machine Learning Trajectory Risk Model
=============================================
High-performance inference engine for detecting multi-query inference attacks,
differencing probes, and progressive triangulation using spatial-temporal AST trajectories.

Executes in < 0.5 ms per query, supporting real-time reverse proxy interception.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
import joblib
import numpy as np

from core.trajectory_extractor import extract_trajectory_features, FEATURE_NAMES

logger = logging.getLogger("ap3.ml_risk_model")

MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models", "query_risk_model.joblib")
)


class MLRiskAssessment:
    """Encapsulates the prediction of the ML trajectory risk model."""

    def __init__(
        self,
        ml_risk_score: float,
        attack_pattern: str,
        confidence: float,
        is_attack: bool,
        features: Dict[str, float],
        top_factors: List[str],
        latency_ms: float,
    ):
        self.ml_risk_score = round(ml_risk_score, 4)
        self.attack_pattern = attack_pattern
        self.confidence = round(confidence, 4)
        self.is_attack = is_attack
        self.features = features
        self.top_factors = top_factors
        self.latency_ms = round(latency_ms, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ml_risk_score": self.ml_risk_score,
            "attack_pattern": self.attack_pattern,
            "confidence": self.confidence,
            "is_attack": self.is_attack,
            "top_factors": self.top_factors,
            "latency_ms": self.latency_ms,
        }


class MLTrajectoryModel:
    """Singleton wrapper for the trained ensemble artifact."""

    _instance: Optional["MLTrajectoryModel"] = None

    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.classifier = None
        self.regressor = None
        self.label_mapping = {0: "BENIGN", 1: "TRIANGULATION", 2: "DIFFERENCING", 3: "TRACKER"}
        self.feature_ranking = []
        self._load_model()

    def _load_model(self) -> None:
        if not os.path.exists(self.model_path):
            logger.warning("ML model bundle not found at %s. Running in heuristic fallback mode.", self.model_path)
            return

        try:
            artifact = joblib.load(self.model_path)
            self.classifier = artifact.get("classifier")
            self.regressor = artifact.get("regressor")
            if self.classifier is not None and hasattr(self.classifier, "n_jobs"):
                self.classifier.n_jobs = 1
            if self.regressor is not None and hasattr(self.regressor, "n_jobs"):
                self.regressor.n_jobs = 1
            self.label_mapping = artifact.get("label_mapping", self.label_mapping)
            self.feature_ranking = artifact.get("feature_ranking", [])
            logger.info("AP3 ML Trajectory Risk Model loaded successfully from %s", self.model_path)
        except Exception as e:
            logger.error("Failed to load ML model artifact: %s", str(e))

    @classmethod
    def get_instance(cls) -> "MLTrajectoryModel":
        if cls._instance is None:
            cls._instance = MLTrajectoryModel()
        return cls._instance

    def predict(
        self,
        tables: List[str],
        columns: List[str],
        predicates: List[str],
        has_where: bool,
        aggregates: List[str],
        history_queries: List[Dict[str, Any]],
        current_timestamp: Optional[float] = None,
    ) -> MLRiskAssessment:
        """
        Extract trajectory features and evaluate risk using the trained ensemble.
        """
        t0 = time.perf_counter()

        vec, feat_dict = extract_trajectory_features(
            curr_tables=tables,
            curr_columns=columns,
            curr_predicates=predicates,
            curr_has_where=has_where,
            curr_aggregates=aggregates,
            history_queries=history_queries,
            current_timestamp=current_timestamp,
        )

        # Fallback if model not loaded
        if self.classifier is None or self.regressor is None:
            # Fallback heuristic calculation
            heuristic_risk = feat_dict.get("time_decayed_overlap_sum", 0.0)
            heuristic_risk = min(0.9999, max(0.0, 1.0 - np.exp(-0.35 * heuristic_risk)))
            pattern = "TRIANGULATION" if heuristic_risk > 0.6 else "BENIGN"
            t1 = time.perf_counter()
            return MLRiskAssessment(
                ml_risk_score=float(heuristic_risk),
                attack_pattern=pattern,
                confidence=0.85,
                is_attack=pattern != "BENIGN",
                features=feat_dict,
                top_factors=["heuristic_fallback"],
                latency_ms=(t1 - t0) * 1000.0,
            )

        X = np.array([vec], dtype=np.float32)

        # 1. Classification & Confidence
        pred_label = int(self.classifier.predict(X)[0])
        pred_proba = self.classifier.predict_proba(X)[0]
        confidence = float(pred_proba[pred_label])
        attack_pattern = self.label_mapping.get(pred_label, "UNKNOWN")
        is_attack = (pred_label != 0)

        # 2. Continuous Risk Regression r_ML in [0, 1)
        pred_risk = float(self.regressor.predict(X)[0])
        pred_risk = max(0.0, min(pred_risk, 0.9999))

        # 3. Explainability: Top contributing factors
        top_factors = []
        if feat_dict.get("differencing_proximity", 0.0) > 0.5:
            top_factors.append("Symmetric difference in predicate set indicates single-record differencing probe")
        if feat_dict.get("pred_narrowing_velocity", 0.0) > 0.1:
            top_factors.append("High predicate narrowing velocity (rapid restriction of subpopulation)")
        if feat_dict.get("time_delta_min", 3600.0) < 15.0:
            top_factors.append(f"Sub-minute inter-query interval (dt={feat_dict['time_delta_min']}s)")
        if feat_dict.get("pred_jaccard_max", 0.0) > 0.6:
            top_factors.append(f"High predicate overlap (Jaccard={feat_dict['pred_jaccard_max']})")
        if not top_factors:
            top_factors.append("Query distribution within expected analytical variance")

        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0

        return MLRiskAssessment(
            ml_risk_score=pred_risk,
            attack_pattern=attack_pattern,
            confidence=confidence,
            is_attack=is_attack,
            features=feat_dict,
            top_factors=top_factors,
            latency_ms=latency_ms,
        )


def evaluate_ml_risk(
    tables: List[str],
    columns: List[str],
    predicates: List[str],
    has_where: bool,
    aggregates: List[str],
    history_queries: List[Dict[str, Any]],
    current_timestamp: Optional[float] = None,
) -> MLRiskAssessment:
    """Convenience helper to evaluate trajectory risk with the singleton model."""
    return MLTrajectoryModel.get_instance().predict(
        tables=tables,
        columns=columns,
        predicates=predicates,
        has_where=has_where,
        aggregates=aggregates,
        history_queries=history_queries,
        current_timestamp=current_timestamp,
    )
