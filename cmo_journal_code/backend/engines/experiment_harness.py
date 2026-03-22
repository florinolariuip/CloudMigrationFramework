"""
Experiment Harness for Fair Comparison and Reproducibility

- Enforces a shared time budget for all algorithms (single-run cap)
- Sets fixed random seeds for reproducibility
- Aggregates metrics and logs all runs
- Supports baselines and pymoo runners
"""

import time
import signal
import random
import numpy as np
from typing import Callable, Dict, Any, List


def set_global_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    # Add torch, tensorflow, etc. if needed


def run_with_time_budget(runner: Callable, args: dict, time_budget_sec: float, seed: int = 42) -> Dict[str, Any]:
    """
    Run a single call to `runner(**args)` and enforce a wall-clock time cap.

    The previous implementation looped runner() until the budget expired,
    which caused deterministic algorithms to run hundreds of times and made
    runtimes incomparable across algorithms.  This version runs the algorithm
    ONCE and records whether it finished within the budget.  On POSIX systems
    a SIGALRM is used to interrupt overrunning calls; on other platforms a
    best-effort elapsed-time check is applied post-hoc.
    """
    set_global_seed(seed)
    start = time.time()
    result = None

    # --- POSIX timeout via SIGALRM ---
    def _timeout_handler(signum, frame):
        raise TimeoutError(f"Algorithm exceeded time budget of {time_budget_sec}s")

    try:
        try:
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(max(1, int(time_budget_sec)))
        except (AttributeError, OSError):
            pass  # SIGALRM not available (Windows); fall through

        result = runner(**args)

    except TimeoutError as te:
        elapsed = time.time() - start
        return {"success": False, "error": str(te), "elapsed": elapsed, "timed_out": True}
    except Exception as e:
        elapsed = time.time() - start
        return {"success": False, "error": str(e), "elapsed": elapsed, "timed_out": False}
    finally:
        try:
            signal.alarm(0)  # Cancel any pending alarm
        except (AttributeError, OSError):
            pass

    elapsed = time.time() - start
    timed_out = elapsed > time_budget_sec
    return {"success": True, "result": result, "elapsed": elapsed, "timed_out": timed_out}


def aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Aggregate cost, latency, providers, etc.
    costs = [r['result'].cost for r in results if r['success'] and hasattr(r['result'], 'cost')]
    latencies = [r['result'].latency for r in results if r['success'] and hasattr(r['result'], 'latency')]
    providers = [r['result'].providers for r in results if r['success'] and hasattr(r['result'], 'providers')]
    return {
        "cost_mean": np.mean(costs) if costs else None,
        "latency_mean": np.mean(latencies) if latencies else None,
        "providers_mean": np.mean(providers) if providers else None,
        "cost_std": np.std(costs) if costs else None,
        "latency_std": np.std(latencies) if latencies else None,
        "providers_std": np.std(providers) if providers else None,
        "runs": len(results)
    }
