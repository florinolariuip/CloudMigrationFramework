"""
MCDA Weight Sensitivity Experiment
===================================
Addresses Reviewer 2, comment 3 (TCC-2026-04-0292): how were the default MCDA
weights chosen, and how sensitive is the final ranking to changes in
stakeholder preferences?

This script reuses the exact same 18-component architecture, constraints, and
solution pool as `netflix_ga_mcda_experiment.py` (Part 3), so its results are
directly comparable to Table "mcda-baselines" in the manuscript. It then
re-scores every method's returned solution under several named weight
profiles (already referenced qualitatively in the manuscript's MCDA section:
cost-focused, performance-critical, security-first, balanced enterprise) and
reports how the ranking changes.

Run from the `cmo_journal_code` directory:
    python3 experiments/mcda_weight_sensitivity_experiment.py

Outputs:
    experiments/results/mcda_weight_sensitivity.csv
    experiments/results/mcda_weight_sensitivity.json
"""

import sys, os, collections, collections.abc, random, json, csv as csv_mod
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for _n in ("Mapping", "MutableMapping", "Sequence", "Callable"):
    if not hasattr(collections, _n):
        setattr(collections, _n, getattr(collections.abc, _n))

import numpy as np

from backend.models import Constraints, Solution
from backend.services import pricing as pricing_svc
from backend.engines.constraints import generate_feasible_solutions
from backend.engines.metrics import (
    calculate_reliability, calculate_security_score,
    calculate_vendor_lockin_risk, calculate_scalability_score
)
from backend.cmov4.optimizer import optimize_architecture
import backend.engines.baselines as bl

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

MAIN_COMPONENTS = [
    'api_gateway','application_server','database','nosql_database','cache',
    'storage','cdn','load_balancer','message_queue','event_streaming',
    'serverless_compute','monitoring','backup','encryption','containers',
    'analytics','identity_management','iot_platform'
]
MAIN_CONSTRAINTS = Constraints(maxBudget=5_000, maxLatency=150.0, maxProviders=3,
                                selected_components=MAIN_COMPONENTS)

ARCH_18 = {'components': [
    {'name':'api_gateway',         'type':'web',                'instance_count':1,  'dependencies':['application_server'],'tech_stack':{}},
    {'name':'application_server',  'type':'compute',            'instance_count':4,  'dependencies':['database','nosql_database','cache'],'tech_stack':{}},
    {'name':'database',            'type':'database',           'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'nosql_database',      'type':'nosql',              'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'cache',               'type':'cache',              'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'storage',             'type':'storage',            'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'cdn',                 'type':'cdn',                'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'load_balancer',       'type':'load_balancer',      'instance_count':1,  'dependencies':['application_server'],'tech_stack':{}},
    {'name':'message_queue',       'type':'message_queue',      'instance_count':1,  'dependencies':['application_server'],'tech_stack':{}},
    {'name':'event_streaming',     'type':'event_streaming',    'instance_count':1,  'dependencies':['monitoring'],'tech_stack':{}},
    {'name':'serverless_compute',  'type':'serverless_compute', 'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'monitoring',          'type':'monitoring',         'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'backup',              'type':'backup',             'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'encryption',          'type':'encryption',         'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'containers',          'type':'containers',         'instance_count':1,  'dependencies':['application_server'],'tech_stack':{}},
    {'name':'analytics',           'type':'analytics',          'instance_count':1,  'dependencies':['nosql_database'],'tech_stack':{}},
    {'name':'identity_management', 'type':'identity',           'instance_count':1,  'dependencies':[],'tech_stack':{}},
    {'name':'iot_platform',        'type':'iot',                'instance_count':1,  'dependencies':[],'tech_stack':{}},
], 'architecture_pattern':'microservices','multi_tenancy':False}

# ── Named weight profiles ────────────────────────────────────────────────────
# Order: cost, latency, reliability, security, vendor_risk, scalability
WEIGHT_PROFILES = {
    "Balanced (default)":     (0.30, 0.20, 0.20, 0.15, 0.10, 0.05),
    "Cost-focused":           (0.55, 0.15, 0.10, 0.10, 0.05, 0.05),
    "Performance-critical":   (0.15, 0.55, 0.10, 0.10, 0.05, 0.05),
    "Security-first":         (0.10, 0.10, 0.15, 0.45, 0.15, 0.05),
    "Vendor-risk-averse":     (0.15, 0.10, 0.10, 0.10, 0.50, 0.05),
}


def run_ga(components, constraints, seed=0, population_size=50, generations=100,
           mutation_rate=0.1, crossover_rate=0.7):
    orig, orig_bl = pricing_svc.COMPONENTS, bl.COMPONENTS
    try:
        pricing_svc.COMPONENTS = components
        bl.COMPONENTS = components
        random.seed(seed); np.random.seed(seed)
        return bl.baseline_genetic_algorithm(
            constraints, population_size=population_size, generations=generations,
            mutation_rate=mutation_rate, crossover_rate=crossover_rate)
    finally:
        pricing_svc.COMPONENTS, bl.COMPONENTS = orig, orig_bl


def run_baseline(fn, components, constraints):
    orig, orig_bl = pricing_svc.COMPONENTS, bl.COMPONENTS
    try:
        pricing_svc.COMPONENTS = components
        bl.COMPONENTS = components
        return fn(constraints)
    finally:
        pricing_svc.COMPONENTS, bl.COMPONENTS = orig, orig_bl


def mcda_score(solution, pool, weights):
    w_c, w_l, w_r, w_s, w_v, w_q = weights
    costs = np.array([s.cost for s in pool])
    lats  = np.array([s.latency for s in pool])
    rels  = np.array([calculate_reliability(s) for s in pool])
    secs  = np.array([calculate_security_score(s) for s in pool])
    vr    = np.array([calculate_vendor_lockin_risk(s) for s in pool])
    sc    = np.array([calculate_scalability_score(s) for s in pool])

    def norm(arr, idx):
        mn, mx = arr.min(), arr.max()
        return 0.5 if mx == mn else (arr[idx] - mn) / (mx - mn)

    try:
        idx = pool.index(solution)
    except ValueError:
        # Rounding during pool de-duplication can drop the exact object;
        # fall back to re-inserting it (matches netflix_ga_mcda_experiment.py).
        pool.append(solution)
        idx = len(pool) - 1
        costs = np.array([s.cost for s in pool])
        lats  = np.array([s.latency for s in pool])
        rels  = np.array([calculate_reliability(s) for s in pool])
        secs  = np.array([calculate_security_score(s) for s in pool])
        vr    = np.array([calculate_vendor_lockin_risk(s) for s in pool])
        sc    = np.array([calculate_scalability_score(s) for s in pool])

    c_n, l_n, r_n = norm(costs, idx), norm(lats, idx), norm(rels, idx)
    s_n, v_n, q_n = norm(secs, idx), norm(vr, idx), norm(sc, idx)
    return w_c*(1-c_n) + w_l*(1-l_n) + w_r*r_n + w_s*s_n + w_v*(1-v_n) + w_q*q_n


def main():
    print("Building 18-component pool (CMOv4, GA, GreedyCost, GreedyLatency, WeightedSum, Random)...")

    random.seed(0); np.random.seed(0)
    cmov4_res = optimize_architecture(ARCH_18, MAIN_CONSTRAINTS.__dict__)
    cmov4_top = None
    if cmov4_res:
        sols = cmov4_res.get('solutions', {})
        if isinstance(sols, dict):
            cmov4_top = sols.get('balanced') or sols.get('min_cost')
        elif isinstance(sols, list) and sols:
            cmov4_top = sols[0]
    if isinstance(cmov4_top, dict):
        cmov4_top = Solution(**cmov4_top)

    r_gc = run_baseline(bl.baseline_greedy_cost,    MAIN_COMPONENTS, MAIN_CONSTRAINTS)
    r_gl = run_baseline(bl.baseline_greedy_latency, MAIN_COMPONENTS, MAIN_CONSTRAINTS)
    r_ws = run_baseline(bl.baseline_weighted_sum,   MAIN_COMPONENTS, MAIN_CONSTRAINTS)
    random.seed(0); np.random.seed(0)
    r_rnd = run_baseline(bl.baseline_random, MAIN_COMPONENTS, MAIN_CONSTRAINTS)
    r_ga  = run_ga(MAIN_COMPONENTS, MAIN_CONSTRAINTS, seed=0)

    feas = generate_feasible_solutions(MAIN_CONSTRAINTS)
    pool = list(feas)
    named = {"CMOv4": cmov4_top, "GA": r_ga.solution if r_ga.success else None,
             "GreedyCost": r_gc.solution if r_gc.success else None,
             "GreedyLatency": r_gl.solution if r_gl.success else None,
             "WeightedSum": r_ws.solution if r_ws.success else None,
             "Random": r_rnd.solution if r_rnd.success else None}
    for sol in named.values():
        if sol is not None:
            pool.append(sol)
    seen, pool_dedup = set(), []
    for s in pool:
        k = (round(s.cost, 2), round(s.latency, 2))
        if k not in seen:
            seen.add(k); pool_dedup.append(s)

    print(f"Pool size: {len(pool_dedup)}\n")

    rows = []
    summary_lines = []
    for profile_name, weights in WEIGHT_PROFILES.items():
        scores = {}
        for algo, sol in named.items():
            if sol is None:
                continue
            score = mcda_score(sol, pool_dedup, weights)
            scores[algo] = score
            rows.append({"profile": profile_name, "weights": weights, "algorithm": algo,
                         "mcda_score": round(score, 4)})
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        winner = ranked[0][0]
        print(f"[{profile_name}]  weights={weights}")
        for algo, sc in ranked:
            marker = "  <-- top" if algo == winner else ""
            print(f"    {algo:15s}: {sc:.4f}{marker}")
        summary_lines.append({"profile": profile_name, "top_method": winner,
                               "top_score": round(ranked[0][1], 4)})
        print()

    with open(os.path.join(RESULTS_DIR, 'mcda_weight_sensitivity.csv'), 'w', newline='') as f:
        w = csv_mod.DictWriter(f, fieldnames=["profile", "weights", "algorithm", "mcda_score"])
        w.writeheader(); w.writerows(rows)

    with open(os.path.join(RESULTS_DIR, 'mcda_weight_sensitivity.json'), 'w') as f:
        json.dump({"per_profile_scores": rows, "top_method_by_profile": summary_lines}, f, indent=2)

    distinct_winners = {s["top_method"] for s in summary_lines}
    print("=" * 60)
    print(f"Distinct top-ranked methods across {len(WEIGHT_PROFILES)} profiles: {sorted(distinct_winners)}")
    print("=" * 60)
    print("\nSaved: experiments/results/mcda_weight_sensitivity.csv")
    print("Saved: experiments/results/mcda_weight_sensitivity.json")


if __name__ == "__main__":
    main()
