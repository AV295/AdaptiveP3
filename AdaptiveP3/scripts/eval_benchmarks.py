"""
AP3 — Experimental Evaluation & Benchmark Suite
================================================
Implements empirical evaluation for Objective O4 (Slide 7):
1. Privacy–Utility Frontier (MAE/MSE across epsilon)
2. Adversarial Triangulation Attack Simulation:
   Static Baseline (hard threshold & static eps) vs. AP3 (adaptive coupling & graceful degradation)
3. Proxy Processing Overhead & Latency Benchmark

Run:
    python scripts/eval_benchmarks.py
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding="utf-8")

import time
import math
import random
from core.query_analyzer import analyze_query
from core.inference_tracker import assess_inference_risk
from core.differential_privacy import (
    compute_effective_epsilon,
    compute_noise_scale,
    add_laplace_noise,
)
from db.history_store import record_query, _get_connection



def clear_test_history():
    """Reset SQLite query history for clean evaluation runs."""
    conn = _get_connection()
    conn.execute("DELETE FROM query_history")
    conn.commit()
    conn.close()


def benchmark_privacy_utility():
    """
    Benchmark 1: Privacy-Utility Tradeoff.
    Measures Empirical MAE and RMSE across a sweep of epsilon values.
    """
    print("\n" + "=" * 70)
    print("BENCHMARK 1: Privacy–Utility Frontier (Empirical Laplace Error vs. ε)")
    print("=" * 70)
    print(f"{'Epsilon (ε)':<12} | {'Theoretical StdDev':<20} | {'Empirical MAE':<15} | {'Empirical RMSE':<15}")
    print("-" * 70)

    true_value = 75000.0  # E.g. Mean salary
    sensitivity = 1.0     # Delta f
    num_trials = 200

    eps_sweep = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
    for eps in eps_sweep:
        errors = []
        theo_std = math.sqrt(2.0) * (sensitivity / eps)

        for _ in range(num_trials):
            noised = add_laplace_noise(true_value, epsilon=eps, sensitivity=sensitivity)
            err = abs(noised - true_value)
            errors.append(err)

        mae = sum(errors) / len(errors)
        rmse = math.sqrt(sum(e ** 2 for e in errors) / len(errors))
        print(f"{eps:<12.2f} | {theo_std:<20.4f} | {mae:<15.4f} | {rmse:<15.4f}")


def benchmark_triangulation_attack():
    """
    Benchmark 2: Triangulation Attack Simulation.
    Simulates an adversary executing a targeted subpopulation reconstruction attack.
    Compares:
      1. Static Hard-Threshold Baseline (Fixed ε, hard denial at threshold)
      2. AP3 Adaptive Proxy (Continuous r(u, q), dynamic ε_eff, graceful degradation)
    """
    print("\n" + "=" * 70)
    print("BENCHMARK 2: Adversarial Triangulation Attack Simulation")
    print("=" * 70)
    clear_test_history()

    target_true_salary = 92000.0
    username = "adversary_eve"
    session_eps = 10.0      # Researcher lifetime budget
    nominal_query_eps = 1.0  # Nominal per-query budget for researcher
    static_baseline_query_eps = 1.0

    attack_queries = [
        ("Probe 1 (Broad)", "SELECT AVG(salary) FROM employees WHERE department = 'Engineering'"),
        ("Probe 2 (Narrow age)", "SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND age >= 30"),
        ("Probe 3 (Narrow range)", "SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND age BETWEEN 30 AND 35"),
        ("Probe 4 (Exact age)", "SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND age = 32"),
        ("Probe 5 (Target isolate)", "SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND age = 32 AND name LIKE 'A%'"),
        ("Probe 6 (Post-threshold)", "SELECT AVG(salary) FROM employees WHERE department = 'Engineering' AND age = 32"),
    ]

    print(f"{'Step':<24} | {'Static Base ε':<14} | {'Static Error':<13} | {'AP3 Risk r':<11} | {'AP3 ε_eff':<10} | {'AP3 Error':<12} | {'AP3 Status'}")
    print("-" * 115)

    remaining_eps = session_eps
    threshold_limit = 4  # Static baseline blocks at > 4 queries

    for idx, (label, sql) in enumerate(attack_queries, start=1):
        analysis = analyze_query(sql)

        # ── Static Baseline Simulation ──
        if idx > threshold_limit:
            static_eps = 0.0
            static_error_str = "BLOCKED (429)"
        else:
            static_eps = static_baseline_query_eps
            static_val = add_laplace_noise(target_true_salary, epsilon=static_eps, sensitivity=analysis.sensitivity)
            static_error = abs(static_val - target_true_salary)
            static_error_str = f"{static_error:.2f}"

        # ── AP3 Adaptive Proxy Simulation ──
        risk = assess_inference_risk(
            username=username,
            tables=analysis.tables,
            columns=analysis.columns,
            predicates=analysis.predicates,
            has_where=analysis.has_where,
            raw_sql=sql,
        )

        is_degraded = (remaining_eps <= 0.05) or risk.is_degraded
        if is_degraded:
            eff_eps = 0.05
            ap3_status = "DEGRADED (Graceful)"
        else:
            base_alloc = min(remaining_eps, nominal_query_eps)
            eff_eps = compute_effective_epsilon(base_alloc, risk.risk_score, gamma=2.0, min_epsilon=0.05)
            ap3_status = "ACTIVE (Coupled)"


        ap3_val = add_laplace_noise(target_true_salary, epsilon=eff_eps, sensitivity=analysis.sensitivity)
        ap3_error = abs(ap3_val - target_true_salary)

        # Update AP3 state
        remaining_eps = max(0.0, remaining_eps - eff_eps)
        record_query(
            username=username,
            tables=analysis.tables,
            columns=analysis.columns,
            predicates=analysis.predicates,
            has_where=analysis.has_where,
            raw_sql=sql,
            risk_score=risk.risk_score,
            effective_epsilon=eff_eps,
        )

        print(
            f"{label:<24} | {static_eps:<14.2f} | {static_error_str:<13} | "
            f"{risk.risk_score:<11.4f} | {eff_eps:<10.4f} | {ap3_error:<12.2f} | {ap3_status}"
        )


def benchmark_latency_overhead():
    """
    Benchmark 3: Proxy Middleware Latency Overhead.
    Measures processing overhead added by AST parsing, inference risk calculation,
    and DP noise generation per query.
    """
    print("\n" + "=" * 70)
    print("BENCHMARK 3: Proxy Processing Overhead & Latency (100 Iterations)")
    print("=" * 70)

    clear_test_history()
    sql = "SELECT AVG(salary), COUNT(id) FROM employees WHERE department = 'Engineering' AND age > 28"

    parse_times = []
    risk_times = []
    noise_times = []
    total_times = []

    for _ in range(100):
        t0 = time.perf_counter()
        analysis = analyze_query(sql)
        t1 = time.perf_counter()

        risk = assess_inference_risk("bench_user", analysis.tables, analysis.columns, analysis.predicates, analysis.has_where, sql)
        t2 = time.perf_counter()

        eff_eps = compute_effective_epsilon(5.0, risk.risk_score)
        _ = add_laplace_noise(75000.0, eff_eps, analysis.sensitivity)
        t3 = time.perf_counter()

        parse_times.append((t1 - t0) * 1000)
        risk_times.append((t2 - t1) * 1000)
        noise_times.append((t3 - t2) * 1000)
        total_times.append((t3 - t0) * 1000)

    avg_parse = sum(parse_times) / len(parse_times)
    avg_risk = sum(risk_times) / len(risk_times)
    avg_noise = sum(noise_times) / len(noise_times)
    avg_total = sum(total_times) / len(total_times)

    print(f"1. SQL AST & Predicate Parsing  : {avg_parse:.3f} ms")
    print(f"2. Subpopulation Inference Risk: {avg_risk:.3f} ms")
    print(f"3. Risk Coupling & Laplace Noise: {avg_noise:.3f} ms")
    print("-" * 70)
    print(f"TOTAL Proxy Middleware Overhead: {avg_total:.3f} ms (Target: < 15.000 ms)")
    print("=" * 70)


if __name__ == "__main__":
    benchmark_privacy_utility()
    benchmark_triangulation_attack()
    benchmark_latency_overhead()
