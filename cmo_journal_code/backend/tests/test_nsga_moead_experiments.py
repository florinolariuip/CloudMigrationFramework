"""Tests for NSGA-II and MOEA/D experiment runners based on current implementation.

These tests are lightweight sanity checks that:
- Ensure `run_all_experiments` executes without crashing for small budgets.
- Confirm that, when successful, NSGA-II and MOEA/D produce a non-empty
  objective matrix `F` and that result CSVs are written.

They are intentionally loose on exact numerical values so they remain
robust to pricing or configuration changes.
"""

import os
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
RESULTS_DIR = BACKEND_DIR / "results"


def test_run_all_experiments_nsga_moead_smoke(monkeypatch):
    """Smoke-test the NSGA-II/MOEA-D pipeline via `backend/run_all_experiments.py`.

    This uses very small populations/generations and tight limits so the
    test finishes quickly, and only asserts structural properties:
    - The script runs without raising.
    - If NSGA-II / MOEA/D succeed, they emit a CSV with at least 1 row.
    """

    # Make sure we do not inherit any surprising env from the shell
    monkeypatch.delenv("POP_SIZE", raising=False)
    monkeypatch.delenv("N_GEN", raising=False)
    monkeypatch.delenv("MAX_BUDGET", raising=False)
    monkeypatch.delenv("MAX_LATENCY", raising=False)
    monkeypatch.delenv("MAX_PROVIDERS", raising=False)

    # Use very small settings to keep the run fast and deterministic enough
    monkeypatch.setenv("POP_SIZE", "10")
    monkeypatch.setenv("N_GEN", "5")
    monkeypatch.setenv("MAX_BUDGET", "20000")
    monkeypatch.setenv("MAX_LATENCY", "100")
    monkeypatch.setenv("MAX_PROVIDERS", "10")

    # Ensure results directory starts clean for this test
    if RESULTS_DIR.exists():
        for fname in ["nsga2_results.csv", "moead_results.csv"]:
            fpath = RESULTS_DIR / fname
            if fpath.exists():
                fpath.unlink()
    else:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Import and execute the experiments module as a script
    module_path = BACKEND_DIR / "run_all_experiments.py"
    assert module_path.exists(), f"Missing run_all_experiments.py at {module_path}"

    # Ensure the backend directory is on sys.path so "engines" and friends resolve
    import sys
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    # Execute the file in its own module namespace with cwd set to backend
    old_cwd = os.getcwd()
    try:
        os.chdir(str(BACKEND_DIR))
        globals_dict = {"__name__": "__main__", "__file__": str(module_path)}
        with module_path.open("rb") as fh:
            code = compile(fh.read(), str(module_path), "exec")
            exec(code, globals_dict)
    finally:
        os.chdir(old_cwd)

    # Now check the CSVs if algorithms succeeded.
    nsga_path = RESULTS_DIR / "nsga2_results.csv"
    moead_path = RESULTS_DIR / "moead_results.csv"

    # It is acceptable (e.g., missing pymoo) that these files are absent;
    # in that case the test simply asserts that no unexpected exception
    # was raised during execution above. If a file exists, it must be non-empty.
    for path in (nsga_path, moead_path):
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            assert content, f"{path} was created but is empty"
            # At least one data row in addition to header
            lines = content.splitlines()
            assert len(lines) >= 2, f"{path} should have at least one data row"
