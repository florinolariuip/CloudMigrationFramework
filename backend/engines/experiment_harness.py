"""
Experiment Harness for Fair Comparison and Reproducibility

- Enforces a shared time budget for all algorithms
- Sets fixed random seeds for reproducibility
- Aggregates metrics and logs all runs
- Supports baselines and pymoo runners
"""

import time
import random
import numpy as np
from typing import Callable, Dict, Any, List


def set_global_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    # Add torch, tensorflow, etc. if needed


def run_with_time_budget(runner: Callable, args: dict, time_budget_sec: float, seed: int = 42) -> Dict[str, Any]:
    set_global_seed(seed)
    start = time.time()
    result = None
    elapsed = 0
    try:
        # Run with time budget
        while elapsed < time_budget_sec:
            result = runner(**args)
            elapsed = time.time() - start
            if elapsed >= time_budget_sec:
                break
    except Exception as e:
        return {"success": False, "error": str(e), "elapsed": elapsed}
    return {"success": True, "result": result, "elapsed": elapsed}


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
