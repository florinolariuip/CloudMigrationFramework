"""Smoke test for the GA convergence experiment.

This validates that `experiments/ga_convergence_experiment.py` can be
executed and produces the key artifacts used in scalability discussion:
- ga_convergence_data.csv
- ga_plateau_analysis.txt
- (optionally) ga_convergence_plot.png and ga_convergence_latency.png

The test does not assert exact convergence metrics, only that the
pipeline runs and emits non-empty outputs.
"""

import os
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"


def test_ga_convergence_experiment_smoke(monkeypatch):
    """Run the GA convergence experiment end-to-end and check outputs.

    We call `test_ga_configurations()` and the subsequent analysis/plot
    functions to ensure the full convergence pipeline executes.
    """

    # Ensure results directory exists and clean key outputs
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for fname in [
        "ga_convergence_data.csv",
        "ga_plateau_analysis.txt",
        "ga_convergence_plot.png",
        "ga_convergence_latency.png",
    ]:
        fpath = RESULTS_DIR / fname
        if fpath.exists():
            fpath.unlink()

    # Import the experiment module with the project root on sys.path
    import sys
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from experiments import ga_convergence_experiment

    # Run GA configurations to generate convergence data
    results, df = ga_convergence_experiment.test_ga_configurations()

    # Basic sanity checks on returned data
    assert df is not None
    assert not df.empty

    # Analyze plateau and generate plots
    plateau_df = ga_convergence_experiment.analyze_plateau(df)
    assert plateau_df is not None
    assert not plateau_df.empty

    ga_convergence_experiment.plot_convergence(df)

    # Now verify that the key artifacts exist and are non-empty
    data_path = RESULTS_DIR / "ga_convergence_data.csv"
    plateau_path = RESULTS_DIR / "ga_plateau_analysis.txt"

    assert data_path.exists(), "ga_convergence_data.csv was not created"
    assert plateau_path.exists(), "ga_plateau_analysis.txt was not created"

    data_df = pd.read_csv(data_path)
    assert not data_df.empty, "ga_convergence_data.csv is empty"

    plateau_text = plateau_path.read_text(encoding="utf-8").strip()
    assert plateau_text, "ga_plateau_analysis.txt is empty"

    # Plots are optional (matplotlib may be missing in some environments),
    # but if files exist, they should be non-empty.
    for plot_name in ["ga_convergence_plot.png", "ga_convergence_latency.png"]:
        plot_path = RESULTS_DIR / plot_name
        if plot_path.exists():
            assert plot_path.stat().st_size > 0, f"{plot_name} exists but is empty"
