"""
Netflix Multi-Cloud Migration Scenario — CMO Runner
===================================================
Runs the Netflix 13-component architecture through CMO's full pipeline:
CSP -> Expert Rules -> Pareto Analysis -> Explainability
"""

import sys, os, collections, collections.abc, time, json

# Monkey-patch for Python 3.10 + Python 3.13 compiled packages
for _n in ("Mapping", "MutableMapping", "Sequence", "Callable"):
    if not hasattr(collections, _n):
        setattr(collections, _n, getattr(collections.abc, _n))

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.models import Constraints, Preferences
from backend.services.pricing import get_service_options, get_service_costs, get_service_latency
from backend.engines.constraints import generate_feasible_solutions
from backend.engines.rules import evaluate_solutions_normalized
from backend.engines.pareto import calculate_pareto_frontier, calculate_pareto_metrics, get_extreme_solutions
from backend.engines.explainability import generate_constraint_proof, generate_rule_trace, generate_decision_path
from backend.engines.sankey import generate_sankey_data, generate_latency_sankey

# -----------------------------------------------------------------------
# Netflix scenario: 13 components mapped to CMO's existing catalog
# -----------------------------------------------------------------------
# Mapping:
#   api_gateway        -> Netflix: Zuul 2 / ELB
#   identity_management-> Netflix: internal auth / Cognito
#   analytics          -> Netflix: recommendation engine / ML inference
#   database           -> Netflix: MySQL (billing, subscriptions)
#   application_server -> Netflix: streaming + microservices (EC2 fleet)
#   storage            -> Netflix: S3 (metadata, logs, model artefacts)
#   cache              -> Netflix: EVCache / ElastiCache
#   event_streaming    -> Netflix: Kafka / Kinesis
#   cdn                -> Netflix: Open Connect / CloudFront
#   load_balancer      -> Netflix: ELB / ALB
#   monitoring         -> Netflix: Atlas / CloudWatch
#   containers         -> Netflix: Titus / EKS
#   nosql_database     -> Netflix: Cassandra / DynamoDB (watch history)

NETFLIX_COMPONENTS = [
    "api_gateway",
    "identity_management",
    "analytics",
    "database",
    "application_server",
    "storage",
    "cache",
    "event_streaming",
    "cdn",
    "load_balancer",
    "monitoring",
    "containers",
    "nosql_database",
]

BUDGET     = 5_000   # $/month (consistent with paper's 15-component experiments)
LATENCY    = 100     # ms
PROVIDERS  = 3

print("=" * 65)
print("  Netflix Multi-Cloud Migration — CMO Analysis")
print("=" * 65)
print(f"  Components : {len(NETFLIX_COMPONENTS)}")
print(f"  Budget cap : ${BUDGET:,}/month")
print(f"  Latency cap: {LATENCY} ms")
print(f"  Max providers: {PROVIDERS}")
print("=" * 65)

# -----------------------------------------------------------------------
# Step 1: Show available service options and search space
# -----------------------------------------------------------------------
options = get_service_options()
costs   = get_service_costs()
latencies = get_service_latency()

total_combinations = 1
for c in NETFLIX_COMPONENTS:
    total_combinations *= len(options.get(c, []))

print(f"\n[1] Search Space")
print(f"    Total configurations: {total_combinations:,}")
for c in NETFLIX_COMPONENTS:
    opts = options.get(c, [])
    print(f"    {c:25s}: {opts}")

# -----------------------------------------------------------------------
# Step 2: CSP — generate feasible solutions
# -----------------------------------------------------------------------
print(f"\n[2] CSP Constraint Satisfaction Engine")
constraints = Constraints(
    maxBudget=BUDGET,
    maxLatency=LATENCY,
    maxProviders=PROVIDERS,
    selected_components=NETFLIX_COMPONENTS,
)
setattr(constraints, "performanceMetric", "avg_latency")

t0 = time.time()
feasible = generate_feasible_solutions(constraints)
csp_ms = (time.time() - t0) * 1000

pruning_rate = (1 - len(feasible) / total_combinations) * 100
print(f"    Feasible solutions  : {len(feasible)}")
print(f"    Pruning rate        : {pruning_rate:.1f}%")
print(f"    CSP runtime         : {csp_ms:.1f} ms")

if not feasible:
    print("    ERROR: No feasible solutions found. Check constraints.")
    sys.exit(1)

# -----------------------------------------------------------------------
# Step 3: Expert Rule System + MCDA scoring
# -----------------------------------------------------------------------
print(f"\n[3] Expert Rule System + MCDA Scoring")
prefs = Preferences()
# Default MCDA weights (30% cost, 20% latency, 20% reliability, 15% security, 10% vendor risk, 5% scalability)
mcda_weights = {"cost": 0.30, "latency": 0.20, "reliability": 0.20, "security": 0.15, "vendor_risk": 0.10, "scalability": 0.05}
t1 = time.time()
scored_result = evaluate_solutions_normalized(feasible, mcda_weights)
scored = scored_result[0] if isinstance(scored_result, tuple) else scored_result
rules_ms = (time.time() - t1) * 1000
print(f"    Scored solutions    : {len(scored)}")
print(f"    Rules runtime       : {rules_ms:.1f} ms")

# -----------------------------------------------------------------------
# Step 4: Pareto Frontier
# -----------------------------------------------------------------------
print(f"\n[4] Pareto Frontier")
t2 = time.time()
pareto = calculate_pareto_frontier(scored)
pareto_ms = (time.time() - t2) * 1000
metrics = calculate_pareto_metrics(scored, pareto)
extremes = get_extreme_solutions(pareto)

print(f"    Pareto size         : {len(pareto)}")
print(f"    Hypervolume         : {metrics.get('hypervolume', 0):.2f}")
print(f"    Spacing             : {metrics.get('spacing', 0):.4f}")
print(f"    Pareto runtime      : {pareto_ms:.1f} ms")

# -----------------------------------------------------------------------
# Step 5: Print Pareto solutions table
# -----------------------------------------------------------------------
print(f"\n[5] Pareto Solutions (sorted by cost)")
print(f"    {'#':<4} {'Cost ($)':<12} {'Latency (ms)':<15} {'Providers':<12} {'Score':<8} {'Configuration'}")
print(f"    {'-'*4} {'-'*12} {'-'*15} {'-'*12} {'-'*8} {'-'*40}")

sorted_pareto = sorted(pareto, key=lambda s: s.cost)
for i, sol in enumerate(sorted_pareto):
    conf_str = ", ".join(f"{k}={v}" for k, v in list(sol.configuration.items())[:3]) + "..."
    score_str = f"{sol.score:.1f}" if sol.score is not None else "N/A"
    print(f"    {i+1:<4} ${sol.cost:<11.2f} {sol.latency:<15.2f} {sol.providers:<12} {score_str:<8} {conf_str}")

# -----------------------------------------------------------------------
# Step 6: Extreme and balanced solutions detail
# -----------------------------------------------------------------------
print(f"\n[6] Key Solutions Detail")

def print_solution(label, sol):
    if sol is None:
        print(f"  {label}: Not found")
        return
    print(f"\n  {label}:")
    print(f"    Cost     : ${sol.cost:.2f}/month")
    print(f"    Latency  : {sol.latency:.2f} ms")
    print(f"    Providers: {sol.providers} ({sol.providerDistribution})")
    print(f"    Score    : {sol.score:.2f}" if sol.score else "    Score    : N/A")
    print(f"    Configuration:")
    for comp, svc in sol.configuration.items():
        print(f"      {comp:25s} -> {svc}")

min_cost_sol   = extremes.get("min_cost")
min_lat_sol    = extremes.get("min_latency")
# Balanced = closest to ideal point
if pareto:
    max_cost = max(s.cost for s in pareto)
    min_cost = min(s.cost for s in pareto)
    max_lat  = max(s.latency for s in pareto)
    min_lat  = min(s.latency for s in pareto)
    def norm(val, lo, hi): return (val - lo) / (hi - lo) if hi > lo else 0
    balanced_sol = min(pareto, key=lambda s: (norm(s.cost, min_cost, max_cost)**2 + norm(s.latency, min_lat, max_lat)**2)**0.5)
else:
    balanced_sol = None

print_solution("Min-Cost", min_cost_sol)
print_solution("Balanced", balanced_sol)
print_solution("Min-Latency", min_lat_sol)

# -----------------------------------------------------------------------
# Step 7: Explainability for the balanced solution
# -----------------------------------------------------------------------
if balanced_sol:
    print(f"\n[7] Explainability — Balanced Solution")

    proof = generate_constraint_proof(balanced_sol, constraints)
    print(f"\n  Constraint Proof:")
    for p in proof:
        satisfied = p.satisfied if hasattr(p, 'satisfied') else p.get("satisfied", False)
        name      = p.constraint_name if hasattr(p, 'constraint_name') else p.get('constraint', '?')
        actual    = p.actual_value if hasattr(p, 'actual_value') else p.get('actual', '?')
        required  = p.required_value if hasattr(p, 'required_value') else p.get('limit', '?')
        status    = "PASS" if satisfied else "FAIL"
        print(f"    [{status}]  {name}: {actual} (required: {required})")

    from backend.config import EXPERT_RULES_CONFIG, SCORING_WEIGHTS
    trace = generate_rule_trace(balanced_sol, prefs, SCORING_WEIGHTS, constraints) if balanced_sol else []
    print(f"\n  Rule Trace ({len(trace)} rules fired):")
    for r in trace[:8]:
        if hasattr(r, 'weight'):
            delta = getattr(r, 'weight', 0)
            name  = getattr(r, 'rule_name', getattr(r, 'name', '?'))
            reason= getattr(r, 'reasoning', getattr(r, 'evidence', ''))
        else:
            delta = r.get("score_contribution", r.get("weight", 0))
            name  = r.get('rule', r.get('name', '?'))
            reason= r.get('reasoning', r.get('reason', r.get('evidence', '')))
        sign = "+" if delta >= 0 else ""
        print(f"    [{sign}{delta:+.0f}] {name}: {str(reason)[:70]}")
    if len(trace) > 8:
        print(f"    ... and {len(trace)-8} more rules")

    decision = generate_decision_path(constraints, prefs, csp_ms, rules_ms, pareto_ms,
                                       len(feasible), len(pareto), balanced_sol)
    print(f"\n  Decision Path Steps: {len(decision)}")
    for step in decision:
        if hasattr(step, 'step_number'):
            print(f"    Step {step.step_number}: {getattr(step, 'description', '')[:80]}")
        elif hasattr(step, 'step'):
            print(f"    Step {step.step}: {getattr(step, 'description', '')[:80]}")
        else:
            print(f"    Step {step.get('step','?')}: {step.get('description', step.get('action',''))[:80]}")

# -----------------------------------------------------------------------
# Step 8: Sankey data (cost flow)
# -----------------------------------------------------------------------
if balanced_sol:
    print(f"\n[8] Sankey Cost Flow — Balanced Solution")
    from backend.services.pricing import service_cache
    services_data = service_cache.get_service_data()
    sankey = generate_sankey_data(balanced_sol, services_data)
    nodes  = sankey.get("nodes", [])
    links  = sankey.get("links", [])
    print(f"    Sankey nodes: {len(nodes)}, links: {len(links)}")
    provider_flows = {}
    for lnk in links:
        src = lnk.get("source", "")
        val = lnk.get("value", 0)
        for node in nodes:
            if node.get("id") == src or node.get("name") == src:
                pname = node.get("name", src)
                provider_flows[pname] = provider_flows.get(pname, 0) + val
    for prov, val in sorted(provider_flows.items(), key=lambda x: -x[1]):
        print(f"    {prov:30s}: ${val:.2f}/month")

# -----------------------------------------------------------------------
# Step 9: Total pipeline runtime
# -----------------------------------------------------------------------
total_ms = csp_ms + rules_ms + pareto_ms
print(f"\n[9] Pipeline Timing")
print(f"    CSP            : {csp_ms:.1f} ms")
print(f"    Expert Rules   : {rules_ms:.1f} ms")
print(f"    Pareto         : {pareto_ms:.1f} ms")
print(f"    TOTAL          : {total_ms:.1f} ms")

# -----------------------------------------------------------------------
# Step 10: Save summary JSON for case study
# -----------------------------------------------------------------------
def sol_to_dict(sol):
    if sol is None: return None
    return {
        "cost": round(sol.cost, 2),
        "latency": round(sol.latency, 2),
        "providers": sol.providers,
        "provider_distribution": sol.providerDistribution,
        "score": round(sol.score, 2) if sol.score else None,
        "configuration": sol.configuration,
    }

summary = {
    "scenario": "Netflix Multi-Cloud Migration (13-component)",
    "constraints": {"budget": BUDGET, "latency_ms": LATENCY, "max_providers": PROVIDERS},
    "search_space": total_combinations,
    "feasible_count": len(feasible),
    "pruning_rate_pct": round(pruning_rate, 1),
    "pareto_size": len(pareto),
    "hypervolume": round(metrics.get("hypervolume", 0), 2),
    "spacing": round(metrics.get("spacing", 0), 4),
    "timing_ms": {"csp": round(csp_ms, 1), "rules": round(rules_ms, 1), "pareto": round(pareto_ms, 1), "total": round(total_ms, 1)},
    "solutions": {
        "min_cost": sol_to_dict(min_cost_sol),
        "balanced": sol_to_dict(balanced_sol),
        "min_latency": sol_to_dict(min_lat_sol),
    },
    "all_pareto": [sol_to_dict(s) for s in sorted_pareto],
}

out_path = "/sessions/compassionate-intelligent-sagan/mnt/outputs/netflix_cmo_results.json"
with open(out_path, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\n    Results saved to: {out_path}")
print("\n" + "=" * 65)
print("  Netflix CMO Analysis Complete")
print("=" * 65)
