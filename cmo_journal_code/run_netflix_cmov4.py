"""
Netflix Multi-Cloud Migration Scenario — CMOv4 Runner
=====================================================
Uses the CMOv4 pipeline (optimize_architecture) with:
  - Dependency-aware critical-path latency (graph_latency)
  - Instance counts per Netflix component
  - Full component dependency graph
"""

import sys, os, collections, collections.abc, time, json

# Monkey-patch for Python 3.10 + Python 3.13 compiled packages
for _n in ("Mapping", "MutableMapping", "Sequence", "Callable"):
    if not hasattr(collections, _n):
        setattr(collections, _n, getattr(collections.abc, _n))

sys.path.insert(0, os.path.dirname(__file__))

from backend.cmov4.optimizer import optimize_architecture

# -----------------------------------------------------------------------
# Netflix architecture: 13 components with types, instance counts,
# and dependency graph (reflecting Netflix's documented call topology)
# -----------------------------------------------------------------------
# CMOv4 component types map via COMPONENT_TYPE_MAPPING:
#   'web' / 'frontend'   -> api_gateway
#   'identity'           -> identity_management
#   'analytics'          -> analytics
#   'database'           -> database
#   'compute'            -> application_server
#   'storage'            -> storage
#   'cache'              -> cache
#   'event_streaming'    -> event_streaming
#   'cdn'                -> cdn
#   'load_balancer'      -> load_balancer
#   'monitoring'         -> monitoring
#   'containers'         -> containers
#   'nosql'              -> nosql_database

ARCH = {
    "components": [
        # Entry point — routes all external traffic
        {"name": "api_gateway",         "type": "web",            "instance_count": 1,
         "dependencies": ["identity_management", "application_server"],
         "tech_stack": {"framework": "Zuul2", "protocol": "HTTP2"}},

        # Auth service — called for every request
        {"name": "identity_management", "type": "identity",       "instance_count": 1,
         "dependencies": [],
         "tech_stack": {"framework": "OAuth2"}},

        # ML recommendation/analytics
        {"name": "analytics",           "type": "analytics",      "instance_count": 1,
         "dependencies": ["nosql_database", "storage"],
         "tech_stack": {"framework": "custom-ML", "language": "Python"}},

        # Billing/subscription relational DB
        {"name": "database",            "type": "database",       "instance_count": 1,
         "dependencies": [],
         "tech_stack": {"engine": "MySQL", "managed": True}},

        # Core streaming + microservices fleet (4 nodes)
        {"name": "application_server",  "type": "compute",        "instance_count": 4,
         "dependencies": ["database", "nosql_database", "cache", "event_streaming", "cdn"],
         "tech_stack": {"language": "Java", "framework": "Spring"}},

        # S3 / metadata / model artefacts
        {"name": "storage",             "type": "storage",        "instance_count": 1,
         "dependencies": [],
         "tech_stack": {"managed": True}},

        # EVCache / Memcached hot metadata
        {"name": "cache",               "type": "cache",          "instance_count": 1,
         "dependencies": [],
         "tech_stack": {"engine": "Redis"}},

        # Kafka / Kinesis async events
        {"name": "event_streaming",     "type": "event_streaming","instance_count": 1,
         "dependencies": ["monitoring"],
         "tech_stack": {"engine": "Kafka"}},

        # CloudFront / Open Connect video delivery
        {"name": "cdn",                 "type": "cdn",            "instance_count": 1,
         "dependencies": [],
         "tech_stack": {"managed": True}},

        # ELB / ALB
        {"name": "load_balancer",       "type": "load_balancer",  "instance_count": 1,
         "dependencies": ["application_server"],
         "tech_stack": {"managed": True}},

        # Atlas / CloudWatch observability
        {"name": "monitoring",          "type": "monitoring",     "instance_count": 1,
         "dependencies": [],
         "tech_stack": {"managed": True}},

        # Titus / EKS container orchestration
        {"name": "containers",          "type": "containers",     "instance_count": 1,
         "dependencies": ["application_server", "analytics"],
         "tech_stack": {"engine": "Kubernetes"}},

        # Cassandra / DynamoDB watch history
        {"name": "nosql_database",      "type": "nosql",          "instance_count": 1,
         "dependencies": [],
         "tech_stack": {"engine": "Cassandra", "managed": True}},
    ],
    "architecture_pattern": "microservices",
    "multi_tenancy": False,
}

CONSTRAINTS = {
    "maxBudget":          5_000,
    "maxLatency":         100,
    "maxProviders":       3,
    "performanceMetric":  "graph_latency",   # <-- CMOv4 key differentiator
    "preferences": {
        "preferredProvider":    None,
        "prioritizeCost":       False,
        "prioritizePerformance": False,
    },
}

print("=" * 65)
print("  Netflix Multi-Cloud Migration — CMOv4 Analysis")
print("=" * 65)
print(f"  Components        : {len(ARCH['components'])}")
print(f"  Budget cap        : ${CONSTRAINTS['maxBudget']:,}/month")
print(f"  Latency cap       : {CONSTRAINTS['maxLatency']} ms")
print(f"  Max providers     : {CONSTRAINTS['maxProviders']}")
print(f"  Latency model     : {CONSTRAINTS['performanceMetric']}")
print("=" * 65)

t0 = time.time()
result = optimize_architecture(ARCH, CONSTRAINTS)
total_ms = (time.time() - t0) * 1000

print(f"\n{'=' * 65}")
print(f"  CMOv4 completed in {total_ms:.1f} ms")
print(f"{'=' * 65}")

# -----------------------------------------------------------------------
# Print structured results
# -----------------------------------------------------------------------
solutions    = result.get("solutions", [])
pareto       = result.get("paretoFrontier", [])
pareto_m     = result.get("paretoMetrics", {})
suggestions  = result.get("suggestions", [])

print(f"\n[RESULTS]")
print(f"  Feasible solutions : {result.get('feasibleCount', 'N/A')}")
print(f"  Pareto size        : {len(pareto)}")
print(f"  Hypervolume        : {pareto_m.get('hypervolume', 0):.2f}")
print(f"  Total runtime      : {total_ms:.1f} ms")

# -----------------------------------------------------------------------
# Pareto frontier table
# -----------------------------------------------------------------------
print(f"\n[PARETO FRONTIER]")
print(f"  {'#':<4} {'Cost ($)':<12} {'Latency (ms)':<15} {'Providers':<12} {'Score':<8} Config (first 3)")
print(f"  {'-'*4} {'-'*12} {'-'*15} {'-'*12} {'-'*8} {'-'*35}")
pareto_sorted = sorted(pareto, key=lambda s: s.get("cost", 999999))
for i, sol in enumerate(pareto_sorted):
    cfg   = sol.get("configuration", {})
    conf3 = ", ".join(f"{k}={v}" for k, v in list(cfg.items())[:3])
    score = sol.get("score") or 0
    print(f"  {i+1:<4} ${sol.get('cost', 0):<11.2f} {sol.get('latency', 0):<15.2f} "
          f"{sol.get('providers', 0):<12} {score:<8.2f} {conf3}...")

# -----------------------------------------------------------------------
# Top-ranked solution detail
# -----------------------------------------------------------------------
if solutions:
    best = solutions[0]
    print(f"\n[TOP-RANKED SOLUTION (by MCDA score)]")
    print(f"  Cost     : ${best.get('cost', 0):.2f}/month")
    print(f"  Latency  : {best.get('latency', 0):.2f} ms  (graph_latency / critical path)")
    print(f"  Providers: {best.get('providers', 0)}  {best.get('providerDistribution', {})}")
    print(f"  Score    : {best.get('score') or 0:.2f}")
    print(f"\n  Full configuration:")
    for comp, svc in best.get("configuration", {}).items():
        print(f"    {comp:28s} -> {svc}")

# -----------------------------------------------------------------------
# Extreme solutions summary
# -----------------------------------------------------------------------
if len(pareto_sorted) >= 2:
    mc  = pareto_sorted[0]
    ml  = min(pareto_sorted, key=lambda s: s.get("latency", 999))
    print(f"\n[PARETO EXTREMES]")
    print(f"  {'Solution':<15} {'Cost ($)':<12} {'Latency (ms)':<15} {'Providers':<12}")
    print(f"  {'-'*15} {'-'*12} {'-'*15} {'-'*12}")
    print(f"  {'Min-cost':<15} ${mc.get('cost',0):<11.2f} {mc.get('latency',0):<15.2f} {mc.get('providers',0)}")
    print(f"  {'Min-latency':<15} ${ml.get('cost',0):<11.2f} {ml.get('latency',0):<15.2f} {ml.get('providers',0)}")

# -----------------------------------------------------------------------
# Explainability (constraint proof + rule trace from top solution)
# -----------------------------------------------------------------------
exp = result.get("explanation", {})
if exp:
    print(f"\n[EXPLAINABILITY]")
    proof = exp.get("constraintProof", [])
    if proof:
        print(f"\n  Constraint Proof:")
        for p in proof:
            sat    = p.get("satisfied", p.get("status") == "PASS")
            name   = p.get("constraint_name", p.get("constraint", "?"))
            actual = p.get("actual_value",    p.get("actual", "?"))
            req    = p.get("required_value",  p.get("limit",  "?"))
            print(f"    [{'PASS' if sat else 'FAIL'}]  {name}: {actual} (required: {req})")

    trace = exp.get("ruleTrace", [])
    if trace:
        print(f"\n  Rule Trace ({len(trace)} rules fired):")
        for r in trace[:8]:
            w    = r.get("weight", r.get("score_contribution", 0))
            name = r.get("rule_name", r.get("rule", r.get("name", "?")))
            ev   = r.get("evidence", r.get("reasoning", ""))
            print(f"    [{w:+.0f}] {name}: {str(ev)[:70]}")

    dp = exp.get("decisionPath", [])
    if dp:
        print(f"\n  Decision Path ({len(dp)} steps):")
        for step in dp[:6]:
            n   = step.get("step_number", step.get("step", "?"))
            desc= step.get("description", step.get("action", ""))
            print(f"    Step {n}: {str(desc)[:80]}")

if suggestions:
    print(f"\n[SUGGESTIONS]")
    for s in suggestions:
        print(f"  - {s}")

# -----------------------------------------------------------------------
# Save results
# -----------------------------------------------------------------------
out_path = "experiments/results/netflix_cmov4_results.json"
with open(out_path, "w") as f:
    json.dump({
        "scenario":        "Netflix Multi-Cloud Migration (13-component, CMOv4)",
        "latency_model":   "graph_latency (critical path)",
        "constraints":     CONSTRAINTS,
        "total_runtime_ms": round(total_ms, 1),
        "feasible_count":  result.get("feasibleCount"),
        "pareto_size":     len(pareto),
        "pareto_metrics":  pareto_m,
        "top_solution":    solutions[0] if solutions else None,
        "pareto_frontier": pareto_sorted,
    }, f, indent=2)

print(f"\n  Results saved -> {out_path}")
print("=" * 65)
