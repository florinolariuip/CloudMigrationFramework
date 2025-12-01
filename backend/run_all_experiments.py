"""
Run all experiments: baselines, NSGA-II, MOEA/D, oracle, etc.
Aggregates results and saves to backend/results/ for figure/table generation.
"""
import os
from engines.baselines import run_all_baselines
from engines.pymoo_runners import run_nsga2, run_moead
from services.pricing import COMPONENTS, get_service_options, get_service_costs, get_service_latency, get_cost_for_service, get_latency_for_service
from engines.experiment_harness import run_with_time_budget, aggregate_metrics
# from engines.oracle import run_oracle_exhaustive  # To be implemented

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

import os
from models import Constraints
# Dynamic constraints and parameters (read from environment variables for API integration)
def get_env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return default
def get_env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except Exception:
        return default
def get_env_str(name, default):
    v = os.environ.get(name, default)
    return v if v else default

search_strategy = get_env_str('SEARCH_STRATEGY', 'heuristic')

from config import CSP_CONFIG
CSP_CONFIG['search_strategy'] = search_strategy

constraints = Constraints(
    maxBudget=get_env_int('MAX_BUDGET', 20000),
    maxLatency=get_env_float('MAX_LATENCY', 100),
    maxProviders=get_env_int('MAX_PROVIDERS', 10)
)

# Baselines
baseline_results = run_all_baselines(constraints)


# Prepare components and objectives for evolutionary algorithms
service_options = get_service_options()
components = [
    {'name': comp, 'options': service_options[comp]} for comp in COMPONENTS
]
costs = get_service_costs()
latencies = get_service_latency()
def cost_objective(config):
    return sum(get_cost_for_service(service) for service in config.values())
def latency_objective(config):
    return sum(get_latency_for_service(service) for service in config.values()) / len(config) if config else 0.0
objectives = {'cost': cost_objective, 'latency': latency_objective}


pop_size = get_env_int('POP_SIZE', 20)
n_gen = get_env_int('N_GEN', 10)

# NSGA-II
nsga2_result = run_with_time_budget(run_nsga2, {
    'components': components,
    'constraints': constraints,
    'objectives': objectives,
    'pop_size': pop_size,
    'n_gen': n_gen,
    'seed': 42
}, time_budget_sec=30)
if nsga2_result.get('success') and nsga2_result.get('result') is not None:
    res = nsga2_result['result']
    print(f"[DEBUG] NSGA-II result F shape: {getattr(res, 'F', None).shape if hasattr(res, 'F') and res.F is not None else 'None'}")
else:
    print(f"[DEBUG] NSGA-II failed: {nsga2_result}")

moead_result = run_with_time_budget(run_moead, {
    'components': components,
    'constraints': constraints,
    'objectives': objectives,
    'pop_size': pop_size,
    'n_gen': n_gen,
    'seed': 42
}, time_budget_sec=30)
if moead_result.get('success') and moead_result.get('result') is not None:
    res = moead_result['result']
    print(f"[DEBUG] MOEA/D result F shape: {getattr(res, 'F', None).shape if hasattr(res, 'F') and res.F is not None else 'None'}")
else:
    print(f"[DEBUG] MOEA/D failed: {moead_result}")

# Oracle exhaustive (placeholder)
# oracle_result = run_with_time_budget(run_oracle_exhaustive, {...}, time_budget_sec=600)

# Aggregate and save results

# Save experiment results as CSV for figure/table generation
import pandas as pd
if hasattr(baseline_results["Random"], "solution") and baseline_results["Random"].solution:
    baselines_df = pd.DataFrame([
        {
            "algorithm": r.algorithm,
            "cost": r.solution.cost if r.solution else None,
            "latency": r.solution.latency if r.solution else None,
            "hypervolume": None,  # Fill with real metric if available
            "success": r.success,
            "iterations": r.iterations,
            "reason": r.reason
        }
        for r in baseline_results.values()
    ])
    baselines_df.to_csv(os.path.join(RESULTS_DIR, "baselines_results.csv"), index=False)

# Save NSGA-II and MOEA/D results as CSV (dummy example, replace with real extraction)
import numpy as np
def extract_pareto_to_df(res, algo_name):
    if not hasattr(res, 'F') or res.F is None:
        return None
    # Calculate hypervolume for the whole set
    try:
        from pymoo.performance_indicator.hv import Hypervolume
        # Reference point: set high enough to cover all possible solutions
        max_cost = float(np.max(res.F[:,0]))
        max_latency = float(np.max(res.F[:,1]))
        ref_point = [max_cost + abs(max_cost)*0.5 + 100, max_latency + abs(max_latency)*0.5 + 10]
        hv = Hypervolume(ref_point=ref_point)
        # If all solutions are identical, hypervolume is zero
        if len(np.unique(res.F, axis=0)) == 1:
            hypervolume_value = 0.0
        else:
            hypervolume_value = hv.do(res.F)
    except Exception as e:
        hypervolume_value = np.nan
    # Assign the same hypervolume to all rows (summary value)
    return pd.DataFrame({
        "algorithm": [algo_name]*len(res.F),
        "cost": res.F[:,0],
        "latency": res.F[:,1],
        "hypervolume": [hypervolume_value]*len(res.F)
    })
if nsga2_result.get('success') and nsga2_result.get('result') is not None and hasattr(nsga2_result['result'], 'F') and nsga2_result['result'].F is not None:
    nsga2_df = extract_pareto_to_df(nsga2_result['result'], "NSGA-II")
    if nsga2_df is not None:
        nsga2_df.to_csv(os.path.join(RESULTS_DIR, "nsga2_results.csv"), index=False)
if moead_result.get('success') and moead_result.get('result') is not None and hasattr(moead_result['result'], 'F') and moead_result['result'].F is not None:
    moead_df = extract_pareto_to_df(moead_result['result'], "MOEA/D")
    if moead_df is not None:
        moead_df.to_csv(os.path.join(RESULTS_DIR, "moead_results.csv"), index=False)

# Automatically generate figures and tables

# Save last run timestamp
from datetime import datetime
with open(os.path.join(RESULTS_DIR, "last_run.txt"), "w") as f:
    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Automatically generate figures and tables
import subprocess
subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "generate_figures_tables.py")], check=False)
