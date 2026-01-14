"""Smoke tests for the multi-run baseline + CMOv4 experiment.

These tests validate that the `experiments/multi_run_experiment.py` harness
can be executed in a lightweight configuration and produces the expected
CSV outputs used by the documentation (e.g., BASELINE_IMPLEMENTATION.md).

They intentionally do not assert specific numeric values, only structural
properties (files exist, non-empty, contain all algorithms).
"""

import os
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"


def test_multi_run_experiment_smoke(monkeypatch):
    """Run the multi-run experiment with a small number of runs.

    We call `run_multi_experiment(n_runs=3)` directly to keep runtime
    manageable, and then check that:
    - `multi_run_results.csv` and `multi_run_statistics.csv` exist.
    - They are non-empty.
    - All expected algorithms appear in the results.
    """

    # Ensure we start from a clean state for the key outputs
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for fname in ["multi_run_results.csv", "multi_run_statistics.csv"]:
        fpath = RESULTS_DIR / fname
        if fpath.exists():
            fpath.unlink()

    # Import the experiment module with the project root on sys.path
    import sys
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from experiments import multi_run_experiment

    # Run a very small experiment to keep CI/test time low
    df, stats = multi_run_experiment.run_multi_experiment(n_runs=3)

    # Basic sanity checks on returned objects
    assert not df.empty
    assert not stats.empty

    # Check that expected algorithms are present
    expected_algorithms = {"CMOv4", "GA", "GreedyCost", "GreedyLatency", "Random", "WeightedSum"}
    assert expected_algorithms.issubset(set(df["algorithm"].unique()))

    # Now verify that the CSVs were written and are non-empty
    results_path = RESULTS_DIR / "multi_run_results.csv"
    stats_path = RESULTS_DIR / "multi_run_statistics.csv"

    assert results_path.exists(), "multi_run_results.csv was not created"
    assert stats_path.exists(), "multi_run_statistics.csv was not created"

    results_df = pd.read_csv(results_path)
    stats_df = pd.read_csv(stats_path)

    assert not results_df.empty, "multi_run_results.csv is empty"
    assert not stats_df.empty, "multi_run_statistics.csv is empty"

    # Ensure all algorithms appear in the persisted CSV as well
    assert expected_algorithms.issubset(set(results_df["algorithm"].unique()))
