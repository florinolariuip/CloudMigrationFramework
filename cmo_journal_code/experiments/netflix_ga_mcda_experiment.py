"""
Netflix GA Baseline + MCDA Score Comparison Experiment
=======================================================
1. Runs GA on the Netflix 13-component scenario (10 seeds)
2. Computes 6-dimensional MCDA scores for CMOv4 and all baselines on
   the 18-component scenario, showing CMOv4's MCDA advantage over GA
3. Outputs JSON summary and CSVs for the paper
"""

import sys, os, collections, collections.abc, time, random, json, csv as csv_mod
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for _n in ("Mapping", "MutableMapping", "Sequence", "Callable"):
    if not hasattr(collections, _n):
        setattr(collections, _n, getattr(collections.abc, _n))

import numpy as np

from backend.models import Constraints, Solution
from backend.services import pricing as pricing_svc
from backend.engines.constraints import generate_feasible_solutions
from backend.engines.rules import evaluate_solutions_normalized
from backend.engines.pareto import calculate_pareto_frontier, get_extreme_solutions
from backend.engines.metrics import (
    calculate_reliability, calculate_security_score,
    calculate_vendor_lockin_risk, calculate_scalability_score
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

# ── Netflix 13-component subset ──────────────────────────────────────────────
NETFLIX_COMPONENTS = [
    "api_gateway", "identity_management", "analytics", "database",
    "application_server", "storage", "cache", "event_streaming",
    "cdn", "load_balancer", "monitoring", "containers", "nosql_database",
]

MAIN_COMPONENTS = [
    'api_gateway','application_server','database','nosql_database','cache',
    'storage','cdn','load_balancer','message_queue','event_streaming',
    'serverless_compute','monitoring','backup','encryption','containers',
    'analytics','identity_management','iot_platform'
]

NETFLIX_CONSTRAINTS = Constraints(maxBudget=5_000, maxLatency=100.0, maxProviders=3,
                                  selected_components=NETFLIX_COMPONENTS)
MAIN_CONSTRAINTS    = Constraints(maxBudget=5_000, maxLatency=150.0, maxProviders=3,
                                  selected_components=MAIN_COMPONENTS)


# ── MCDA helper ──────────────────────────────────────────────────────────────
def compute_mcda(solution, pool,
                 weights=(0.30, 0.20, 0.20, 0.15, 0.10, 0.05)):
    w_c, w_l, w_r, w_s, w_v, w_q = weights
    costs = np.array([s.cost    for s in pool])
    lats  = np.array([s.latency for s in pool])
    rels  = np.array([calculate_reliability(s)       for s in pool])
    secs  = np.array([calculate_security_score(s)    for s in pool])
    vr    = np.array([calculate_vendor_lockin_risk(s) for s in pool])
    sc    = np.array([calculate_scalability_score(s) for s in pool])

    def norm(arr, idx):
        mn, mx = arr.min(), arr.max()
        return 0.5 if mx == mn else (arr[idx] - mn) / (mx - mn)

    try:
        idx = pool.index(solution)
    except ValueError:
        pool.append(solution)
        idx = len(pool) - 1
        # recompute arrays
        costs = np.array([s.cost    for s in pool])
        lats  = np.array([s.latency for s in pool])
        rels  = np.array([calculate_reliability(s)       for s in pool])
        secs  = np.array([calculate_security_score(s)    for s in pool])
        vr    = np.array([calculate_vendor_lockin_risk(s) for s in pool])
        sc    = np.array([calculate_scalability_score(s) for s in pool])

    c_n = norm(costs, idx); l_n = norm(lats, idx); r_n = norm(rels, idx)
    s_n = norm(secs, idx);  v_n = norm(vr,   idx); q_n = norm(sc,   idx)
    score = w_c*(1-c_n) + w_l*(1-l_n) + w_r*r_n + w_s*s_n + w_v*(1-v_n) + w_q*q_n
    return {
        "mcda_score": round(score, 4),
        "raw_reliability":  round(float(rels[idx]), 4),
        "raw_security":     round(float(secs[idx]), 4),
        "raw_vendor_risk":  round(float(vr[idx]),   4),
        "raw_scalability":  round(float(sc[idx]),   4),
        "norm_cost":        round(c_n, 4),
        "norm_latency":     round(l_n, 4),
    }


# ── Patched GA runner ─────────────────────────────────────────────────────────
def run_ga(components, constraints, seed=0,
           population_size=50, generations=100,
           mutation_rate=0.1, crossover_rate=0.7):
    """Run GA on a specific component list by monkey-patching COMPONENTS."""
    import backend.engines.baselines as bl
    orig = pricing_svc.COMPONENTS
    orig_bl = bl.COMPONENTS
    try:
        pricing_svc.COMPONENTS = components
        bl.COMPONENTS = components
        random.seed(seed); np.random.seed(seed)
        result = bl.baseline_genetic_algorithm(
            constraints,
            population_size=population_size,
            generations=generations,
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
        )
    finally:
        pricing_svc.COMPONENTS = orig
        bl.COMPONENTS = orig_bl
    return result


def run_baseline(fn, components, constraints):
    import backend.engines.baselines as bl
    orig = pricing_svc.COMPONENTS
    orig_bl = bl.COMPONENTS
    try:
        pricing_svc.COMPONENTS = components
        bl.COMPONENTS = components
        result = fn(constraints)
    finally:
        pricing_svc.COMPONENTS = orig
        bl.COMPONENTS = orig_bl
    return result


# ═══════════════════════════════════════════════════════════════════════════
# PART 1 — GA on Netflix 13-component scenario
# ═══════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("PART 1: GA on Netflix 13-component scenario (10 seeds)")
print("=" * 60)

netflix_ga_rows = []
netflix_ga_solutions = []

for seed in range(10):
    t0 = time.time()
    result = run_ga(NETFLIX_COMPONENTS, NETFLIX_CONSTRAINTS, seed=seed)
    elapsed = (time.time() - t0) * 1000
    if result.success and result.solution:
        sol = result.solution
        n_prov = len(set(v.split()[0] for v in sol.configuration.values() if v))
        row = dict(seed=seed, algorithm="GA", scenario="Netflix-13comp",
                   cost=round(sol.cost,2), latency=round(sol.latency,2),
                   providers=n_prov, time_ms=round(elapsed,1), success=True)
        netflix_ga_solutions.append(sol)
    else:
        row = dict(seed=seed, algorithm="GA", scenario="Netflix-13comp",
                   cost=None, latency=None, providers=None,
                   time_ms=round(elapsed,1), success=False)
    netflix_ga_rows.append(row)
    status = f"${row['cost']:.2f}  {row['latency']:.2f}ms" if row['success'] else "FAIL"
    print(f"  seed {seed:2d}: {status}  ({row['time_ms']:.0f} ms)")

succ = [r for r in netflix_ga_rows if r['success']]
ga_costs = [r['cost'] for r in succ]
ga_lats  = [r['latency'] for r in succ]
ga_times = [r['time_ms'] for r in succ]
print(f"\n  GA Netflix ({len(succ)}/10 runs):")
print(f"    Cost:    ${np.mean(ga_costs):.2f} ± ${np.std(ga_costs):.2f}  "
      f"[min ${min(ga_costs):.2f}, max ${max(ga_costs):.2f}]")
print(f"    Latency: {np.mean(ga_lats):.2f} ± {np.std(ga_lats):.2f} ms")
print(f"    Runtime: {np.mean(ga_times):.1f} ± {np.std(ga_times):.1f} ms")

# Save
with open(os.path.join(RESULTS_DIR, 'netflix_ga_results.csv'), 'w', newline='') as f:
    w = csv_mod.DictWriter(f, fieldnames=netflix_ga_rows[0].keys())
    w.writeheader(); w.writerows(netflix_ga_rows)


# ═══════════════════════════════════════════════════════════════════════════
# PART 2 — MCDA scores on Netflix scenario (CMOv3 vs GA vs baselines)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 2: MCDA on Netflix scenario (CMOv3 vs GA vs greedy)")
print("=" * 60)

import backend.engines.baselines as bl

# CMOv3 pipeline on Netflix
netflix_feasible = generate_feasible_solutions(NETFLIX_CONSTRAINTS)
print(f"  Feasible Netflix solutions: {len(netflix_feasible)}")
scored_result = evaluate_solutions_normalized(netflix_feasible)
scored = scored_result[0] if isinstance(scored_result, tuple) else scored_result
pareto = calculate_pareto_frontier(scored)
extreme = get_extreme_solutions(pareto)
cmov3_sol = extreme.get('balanced') or extreme.get('min_cost')
if cmov3_sol is None and scored:
    cmov3_sol = max(scored, key=lambda s: s.score)

# Greedy baselines on Netflix
gc_nf = run_baseline(bl.baseline_greedy_cost,    NETFLIX_COMPONENTS, NETFLIX_CONSTRAINTS)
gl_nf = run_baseline(bl.baseline_greedy_latency, NETFLIX_COMPONENTS, NETFLIX_CONSTRAINTS)
ws_nf = run_baseline(bl.baseline_weighted_sum,   NETFLIX_COMPONENTS, NETFLIX_CONSTRAINTS)

# Build pool
pool_nf = list(netflix_feasible) + netflix_ga_solutions
for r in [gc_nf, gl_nf, ws_nf]:
    if r.success and r.solution:
        pool_nf.append(r.solution)
if cmov3_sol:
    pool_nf.append(cmov3_sol)
# deduplicate by (cost, latency)
seen_nf = set(); pool_nf_dedup = []
for s in pool_nf:
    k = (round(s.cost,2), round(s.latency,2))
    if k not in seen_nf: seen_nf.add(k); pool_nf_dedup.append(s)
print(f"  Pool size for MCDA normalisation: {len(pool_nf_dedup)}")

netflix_mcda_rows = []
def add_mcda(sol, algo, pool):
    m = compute_mcda(sol, pool)
    n_prov = len(set(v.split()[0] for v in sol.configuration.values() if v))
    m.update(algorithm=algo, cost=round(sol.cost,2), latency=round(sol.latency,2),
             providers=n_prov, scenario="Netflix-13comp")
    netflix_mcda_rows.append(m)
    print(f"  {algo:15s}: MCDA={m['mcda_score']:.4f}  "
          f"cost=${m['cost']:.2f}  lat={m['latency']:.2f}ms  "
          f"rel={m['raw_reliability']:.3f}  sec={m['raw_security']:.3f}  "
          f"vr={m['raw_vendor_risk']:.3f}")
    return m

if cmov3_sol:
    cmov3_mcda = add_mcda(cmov3_sol, "CMOv3", pool_nf_dedup)

for i, sol in enumerate(netflix_ga_solutions[:5]):
    add_mcda(sol, f"GA_s{i}", pool_nf_dedup)

for r, name in [(gc_nf,'GreedyCost'),(gl_nf,'GreedyLatency'),(ws_nf,'WeightedSum')]:
    if r.success and r.solution:
        add_mcda(r.solution, name, pool_nf_dedup)

ga_nf_mcda = [r['mcda_score'] for r in netflix_mcda_rows if r['algorithm'].startswith('GA')]
print(f"\n  CMOv3 MCDA:  {cmov3_mcda['mcda_score']:.4f}")
print(f"  GA MCDA avg: {np.mean(ga_nf_mcda):.4f} ± {np.std(ga_nf_mcda):.4f}")
print(f"  CMOv3 advantage: +{cmov3_mcda['mcda_score'] - np.mean(ga_nf_mcda):.4f}  "
      f"({(cmov3_mcda['mcda_score']/np.mean(ga_nf_mcda)-1)*100:.1f}% higher)")


# ═══════════════════════════════════════════════════════════════════════════
# PART 3 — MCDA scores on 18-component scenario
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 3: MCDA on 18-component scenario (CMOv4 vs all baselines)")
print("=" * 60)

# CMOv4 on 18-component (seed 0)
print("  Running CMOv4 seed 0 on 18-comp...")
import importlib as _il
from backend.cmov4.optimizer import optimize_architecture

arch_18 = { 'components': [
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

random.seed(0); np.random.seed(0)
cmov4_res = optimize_architecture(arch_18, MAIN_CONSTRAINTS.__dict__)
cmov4_top = None
if cmov4_res:
    sols = cmov4_res.get('solutions', {})
    if isinstance(sols, dict):
        cmov4_top = sols.get('balanced') or sols.get('min_cost')
    elif isinstance(sols, list) and sols:
        cmov4_top = sols[0]

# Baselines on 18-comp
print("  Running baselines on 18-comp...")
r_gc18 = run_baseline(bl.baseline_greedy_cost,    MAIN_COMPONENTS, MAIN_CONSTRAINTS)
r_gl18 = run_baseline(bl.baseline_greedy_latency, MAIN_COMPONENTS, MAIN_CONSTRAINTS)
r_ws18 = run_baseline(bl.baseline_weighted_sum,   MAIN_COMPONENTS, MAIN_CONSTRAINTS)

random.seed(0); np.random.seed(0)
r_rnd18 = run_baseline(bl.baseline_random, MAIN_COMPONENTS, MAIN_CONSTRAINTS)
r_ga18  = run_ga(MAIN_COMPONENTS, MAIN_CONSTRAINTS, seed=0)

# Feasible pool for 18-comp
print("  Generating feasible pool...")
feas_18 = generate_feasible_solutions(MAIN_CONSTRAINTS)
print(f"  Feasible: {len(feas_18)}")

pool_18 = list(feas_18)
for r in [r_gc18, r_gl18, r_ws18, r_rnd18, r_ga18]:
    if r.success and r.solution: pool_18.append(r.solution)
if cmov4_top: pool_18.append(cmov4_top)
seen18 = set(); pool_18_dedup = []
for s in pool_18:
    k = (round(s.cost,2), round(s.latency,2))
    if k not in seen18: seen18.add(k); pool_18_dedup.append(s)
print(f"  Pool size: {len(pool_18_dedup)}")

mcda_18_rows = []
def add_mcda_18(sol, algo):
    if sol is None:
        print(f"  {algo}: NO SOLUTION"); return None
    m = compute_mcda(sol, pool_18_dedup)
    n_prov = len(set(v.split()[0] for v in sol.configuration.values() if v))
    m.update(algorithm=algo, cost=round(sol.cost,2), latency=round(sol.latency,2),
             providers=n_prov, scenario="18-comp")
    mcda_18_rows.append(m)
    print(f"  {algo:15s}: MCDA={m['mcda_score']:.4f}  "
          f"cost=${m['cost']:.2f}  lat={m['latency']:.2f}ms  "
          f"rel={m['raw_reliability']:.3f}  sec={m['raw_security']:.3f}  "
          f"vr={m['raw_vendor_risk']:.3f}")
    return m

cmov4_mcda  = add_mcda_18(cmov4_top, "CMOv4")
ga18_mcda   = add_mcda_18(r_ga18.solution if r_ga18.success else None, "GA")
add_mcda_18(r_gc18.solution if r_gc18.success else None,  "GreedyCost")
add_mcda_18(r_gl18.solution if r_gl18.success else None,  "GreedyLatency")
add_mcda_18(r_ws18.solution if r_ws18.success else None,  "WeightedSum")
add_mcda_18(r_rnd18.solution if r_rnd18.success else None,"Random")

if cmov4_mcda and ga18_mcda:
    print(f"\n  CMOv4 MCDA advantage over GA: "
          f"+{cmov4_mcda['mcda_score'] - ga18_mcda['mcda_score']:.4f}  "
          f"({(cmov4_mcda['mcda_score']/ga18_mcda['mcda_score']-1)*100:.1f}% higher)")

# ── Save all results ──────────────────────────────────────────────────────────
with open(os.path.join(RESULTS_DIR,'mcda_comparison_18comp.csv'),'w',newline='') as f:
    if mcda_18_rows:
        w = csv_mod.DictWriter(f, fieldnames=mcda_18_rows[0].keys())
        w.writeheader(); w.writerows(mcda_18_rows)

with open(os.path.join(RESULTS_DIR,'mcda_comparison_netflix.csv'),'w',newline='') as f:
    if netflix_mcda_rows:
        w = csv_mod.DictWriter(f, fieldnames=netflix_mcda_rows[0].keys())
        w.writeheader(); w.writerows(netflix_mcda_rows)

summary = {
    "netflix_ga": {
        "n_success": len(succ),
        "cost_mean": round(float(np.mean(ga_costs)),2),
        "cost_std":  round(float(np.std(ga_costs)),2),
        "cost_min":  round(float(min(ga_costs)),2),
        "cost_max":  round(float(max(ga_costs)),2),
        "latency_mean": round(float(np.mean(ga_lats)),2),
        "latency_std":  round(float(np.std(ga_lats)),2),
        "runtime_mean_ms": round(float(np.mean(ga_times)),1),
    },
    "mcda_18comp": mcda_18_rows,
    "mcda_netflix": netflix_mcda_rows,
    "cmov3_vs_ga_netflix": {
        "cmov3_mcda": cmov3_mcda['mcda_score'] if cmov3_sol else None,
        "ga_mcda_mean": round(float(np.mean(ga_nf_mcda)),4) if ga_nf_mcda else None,
        "ga_mcda_std":  round(float(np.std(ga_nf_mcda)),4) if ga_nf_mcda else None,
    },
}
with open(os.path.join(RESULTS_DIR,'mcda_summary.json'),'w') as f:
    json.dump(summary, f, indent=2)

print("\n✓ All results saved:")
print("  results/netflix_ga_results.csv")
print("  results/mcda_comparison_18comp.csv")
print("  results/mcda_comparison_netflix.csv")
print("  results/mcda_summary.json")
