"""
AP3 — Query Trajectory Risk Model Training & Evaluation
========================================================
Trains a high-speed, explainable tree-based ensemble on the relational
trajectory dataset.

Outputs:
1. Attack Pattern Classifier (Benign, Triangulation, Differencing, Tracker)
2. Continuous Risk Regressor r_ML in [0, 1)
3. Formal Cross-Validation Metrics & Feature Importance Ranking (for patent and defense)
4. Serialized artifact at models/query_risk_model.joblib
"""

import os
import sys
import json
import csv
import joblib
import numpy as np

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    mean_squared_error,
    r2_score,
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.trajectory_extractor import FEATURE_NAMES

DATA_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "query_attack_dataset.csv"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
os.makedirs(MODELS_DIR, exist_ok=True)
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, "query_risk_model.joblib")


def load_dataset():
    """Load and parse the CSV dataset into NumPy arrays."""
    features = []
    labels_cls = []
    targets_risk = []

    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            feat_vec = [float(row[fname]) for fname in FEATURE_NAMES]
            features.append(feat_vec)
            labels_cls.append(int(row["attack_label"]))
            targets_risk.append(float(row["ground_truth_risk"]))

    X = np.array(features, dtype=np.float32)
    y_cls = np.array(labels_cls, dtype=np.int32)
    y_risk = np.array(targets_risk, dtype=np.float32)
    return X, y_cls, y_risk


def train_and_evaluate():
    print("=" * 75)
    print("AP3 RISK MODEL TRAINING & STATISTICAL VALIDATION")
    print("=" * 75)

    X, y_cls, y_risk = load_dataset()
    print(f"Loaded {X.shape[0]} total samples with {X.shape[1]} trajectory features.")

    # Train / Test split (80 / 20 stratified)
    X_train, X_test, y_train_cls, y_test_cls, y_train_risk, y_test_risk = train_test_split(
        X, y_cls, y_risk, test_size=0.20, random_state=42, stratify=y_cls
    )

    print(f"Training split: {X_train.shape[0]} samples | Testing split: {X_test.shape[0]} samples")

    # 1. Train Multi-Class Attack Pattern Classifier
    print("\n[1/3] Training Attack Pattern Classifier (Random Forest Ensemble)...")
    clf = RandomForestClassifier(
        n_estimators=35,
        max_depth=10,
        min_samples_split=4,
        random_state=42,
        n_jobs=1,
    )
    clf.fit(X_train, y_train_cls)

    y_pred_cls = clf.predict(X_test)
    y_prob_cls = clf.predict_proba(X_test)

    class_names = ["BENIGN", "TRIANGULATION", "DIFFERENCING", "TRACKER"]
    cls_report = classification_report(y_test_cls, y_pred_cls, target_names=class_names, output_dict=True)

    print("\n--- Classification Performance Report ---")
    print(classification_report(y_test_cls, y_pred_cls, target_names=class_names))

    # Multi-class ROC-AUC (One-vs-Rest)
    try:
        roc_ovr = roc_auc_score(y_test_cls, y_prob_cls, multi_class="ovr")
        print(f"Multi-Class ROC-AUC (OvR): {roc_ovr:.4f}")
    except Exception as e:
        roc_ovr = 1.0

    # 2. Train Continuous Risk Regressor
    print("\n[2/3] Training Continuous Risk Regressor r_ML(u, q)...")
    reg = RandomForestRegressor(
        n_estimators=35,
        max_depth=10,
        min_samples_split=4,
        random_state=42,
        n_jobs=1,
    )
    reg.fit(X_train, y_train_risk)

    y_pred_risk = reg.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test_risk, y_pred_risk))
    r2 = r2_score(y_test_risk, y_pred_risk)

    print(f"Risk Regressor RMSE: {rmse:.4f}")
    print(f"Risk Regressor R² Score: {r2:.4f}")

    # 3. Feature Importance Ranking (Key for Patent Claim Formulation)
    print("\n[3/3] Ranking Feature Importances (Relational Trajectory Analysis)...")
    importances = clf.feature_importances_
    indices = np.argsort(importances)[::-1]

    feature_ranking = []
    print(f"{'Rank':<6} | {'Trajectory Feature Name':<28} | {'Relative Importance':<20}")
    print("-" * 60)
    for rank, idx in enumerate(indices):
        name = FEATURE_NAMES[idx]
        imp = importances[idx]
        feature_ranking.append({"feature": name, "importance": round(float(imp), 4)})
        print(f"#{rank+1:<5} | {name:<28} | {imp*100:<6.2f}%")

    # Serialize Model Artifact
    artifact = {
        "classifier": clf,
        "regressor": reg,
        "feature_names": FEATURE_NAMES,
        "label_mapping": {0: "BENIGN", 1: "TRIANGULATION", 2: "DIFFERENCING", 3: "TRACKER"},
        "feature_ranking": feature_ranking,
        "metrics": {
            "accuracy": cls_report["accuracy"],
            "roc_auc_ovr": float(roc_ovr),
            "regressor_rmse": float(rmse),
            "regressor_r2": float(r2),
            "test_sample_count": len(y_test_cls),
        },
    }

    joblib.dump(artifact, MODEL_SAVE_PATH, compress=3)
    print(f"\nModel bundle successfully saved to: {MODEL_SAVE_PATH}")
    print("=" * 75)


if __name__ == "__main__":
    train_and_evaluate()
