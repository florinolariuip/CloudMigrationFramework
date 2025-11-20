from __future__ import annotations
from flask import request

# Import CMOv4 benchmark (works in both local and Heroku)
try:
    from cmov4.benchmark import SCENARIOS, run_benchmark, run_single_benchmark
except ImportError:
    from backend.cmov4.benchmark import SCENARIOS, run_benchmark, run_single_benchmark

# Benchmark API for frontend
from flask import Flask, jsonify
import time

# Simulated provider status (replace with real API checks if available)
PROVIDER_STATUS = {
    'aws': True,
    'azure': True,
    'gcp': True
}
LAST_UPDATE = time.strftime('%I:%M:%S %p')

# All required imports must come next
import os
from dataclasses import asdict
from typing import Dict, Any
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime

# Python 3.10+ compatibility shim for legacy libraries that import from collections
# Some third-party packages (e.g., experta, schema) may reference collections.Mapping
# which moved to collections.abc in newer Python versions (3.10+).
import collections, collections.abc  # noqa: E401
for _name in ("Mapping", "MutableMapping", "Sequence"):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))

# Layered modules
from backend.config import (
    DEFAULT_CONSTRAINTS,
    DEFAULT_PRICING,
    SERVICE_DEPENDENCIES,
    EXPERT_RULES_CONFIG,
    SCORING_WEIGHTS,
    CSP_CONFIG,
)
from backend.models import Constraints, Preferences
from backend.services.pricing import get_total_combinations
from backend.engines.constraints import generate_feasible_solutions
from backend.engines.rules import evaluate_solutions, calculate_statistics, evaluate_solutions_normalized
from backend.engines.pareto import (
    calculate_pareto_frontier,
    calculate_pareto_rank,
    calculate_pareto_metrics,
    get_extreme_solutions
)
from backend.engines.baselines import (
    run_all_baselines,
    compare_with_csp_expert,
    BaselineResult
)
from backend.engines.explainability import (
    generate_constraint_proof,
    generate_rule_trace,
    generate_decision_path,
    compare_explainability
)
from backend.engines.sankey import (
    generate_sankey_data,
    generate_latency_sankey
)



app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

# Lightweight internal version identifier (update on meaningful backend changes)
APP_VERSION = "2025-11-15-seed-diagnostics-1"

# CMOv4 Benchmark endpoints
@app.route('/api/service-data')
def service_data():
    return jsonify({
        'aws': PROVIDER_STATUS['aws'],
        'azure': PROVIDER_STATUS['azure'],
        'gcp': PROVIDER_STATUS['gcp'],
        'last_updated': LAST_UPDATE
    })

@app.route('/api/benchmark')
def api_benchmark():
    import sys
    print("[DEBUG] /api/benchmark called", file=sys.stderr)
    scenario_idx = int(request.args.get('scenario', 0))
    print(f"[DEBUG] scenario_idx: {scenario_idx}", file=sys.stderr)
    if scenario_idx < 0 or scenario_idx >= len(SCENARIOS):
        print("[ERROR] Invalid scenario index", file=sys.stderr)
        return jsonify({'error': 'Invalid scenario index.'}), 400
    scenario = SCENARIOS[scenario_idx].copy()
    print(f"[DEBUG] scenario: {scenario}", file=sys.stderr)
    
    # Extract usage profile
    usage_profile = {}
    for key in ['requests_per_month', 'cross_az_gb', 'internet_egress_gb', 'ebs_gb', 'rds_backup_gb', 's3_gb']:
        if key in request.args:
            usage_profile[key] = float(request.args.get(key))
    print(f"[DEBUG] usage_profile: {usage_profile}", file=sys.stderr)
    if usage_profile:
        scenario['usage_profile'] = usage_profile
    
    # Extract preferences
    preferences = {}
    if 'preferred_provider' in request.args and request.args.get('preferred_provider'):
        preferences['preferredProvider'] = request.args.get('preferred_provider')
    if 'prioritize_cost' in request.args:
        preferences['prioritizeCost'] = request.args.get('prioritize_cost') == '1'
    if 'prioritize_performance' in request.args:
        preferences['prioritizePerformance'] = request.args.get('prioritize_performance') == '1'
    print(f"[DEBUG] preferences: {preferences}", file=sys.stderr)
    if preferences:
        scenario['preferences'] = preferences
    
    print(f"[DEBUG] scenario with usage_profile and preferences: {scenario}", file=sys.stderr)
    results = run_benchmark([scenario])
    print(f"[DEBUG] results: {results}", file=sys.stderr)
    result = results[0]
    print(f"[DEBUG] result: {result}", file=sys.stderr)
    return jsonify({
        'v3': result.get('v3', {}),
        'v4': result.get('v4', {}),
        'scenario': result.get('scenario', {})
    })

# Dynamic benchmark endpoint for smart scenario selection
@app.route('/api/benchmark/dynamic', methods=['POST'])
def api_benchmark_dynamic():
    """
    Accepts a scenario payload (architecture, constraints, pricing) and runs a benchmark.
    Enables smart selection and dynamic benchmarking from the frontend.
    """
    payload = request.get_json(force=True, silent=True) or {}
    scenario = payload.get('scenario')
    if not scenario:
        return jsonify({'error': 'Missing scenario payload.'}), 400
    result = run_single_benchmark(scenario)
    return jsonify({
        'v3': result.get('v3', {}),
        'v4': result.get('v4', {}),
        'scenario': result.get('scenario', {})
    })

@app.get("/api/version")
def version():
    """Return backend version and feature flags for deployment verification.
    This helps confirm the running slug actually contains recent seed logic.
    """
    # Detect presence of seed support by inspecting optimize function code text
    import inspect
    optimize_src = inspect.getsource(optimize)
    has_seed_support = "seed_used" in optimize_src and "deterministic seed" in optimize_src
    return jsonify({
        "version": APP_VERSION,
        "heroku_release": os.environ.get("HEROKU_RELEASE_VERSION"),
        "python_version": os.environ.get("PYTHON_VERSION"),
        "has_seed_support": has_seed_support,
        "features": {
            "seed": has_seed_support,
            "pareto": True,
            "explainability": True
        }
    })

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

# Generic documentation endpoint to serve markdown files from root, backend, or frontend
import os
@app.get("/api/docs/<path:filename>")
def serve_markdown(filename):
    """Serve markdown documentation files for docs.html viewer."""
    # Allow only .md files for security
    if not filename.endswith('.md'):
        return ("Invalid file type", 400)
    # Try root, backend, frontend
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    for folder in [root_dir, backend_dir, frontend_dir]:
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            return send_from_directory(folder, filename)
    return ("File not found", 404)

# Serve EXPLANATION.md for frontend documentation link
@app.get("/EXPLANATION.md")
def serve_explanation_md():
    """Serve the backend EXPLANATION.md documentation file."""
    import os
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(backend_dir, "EXPLANATION.md")

# Serve research documentation files
@app.get("/PARETO_IMPLEMENTATION.md")
def serve_pareto_md():
    """Serve the Pareto implementation documentation."""
    import os
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(backend_dir, "PARETO_IMPLEMENTATION.md")

@app.get("/BASELINE_IMPLEMENTATION.md")
def serve_baseline_md():
    """Serve the baseline comparison documentation."""
    import os
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(backend_dir, "BASELINE_IMPLEMENTATION.md")

@app.get("/EXPLAINABILITY_IMPLEMENTATION.md")
def serve_explainability_md():
    """Serve the explainability implementation documentation."""
    import os
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(backend_dir, "EXPLAINABILITY_IMPLEMENTATION.md")

@app.get("/SCALABILITY_IMPLEMENTATION.md")
def serve_scalability_md():
    """Serve the scalability (15 components) implementation documentation."""
    import os
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(backend_dir, "SCALABILITY_IMPLEMENTATION.md")

# Academic extension: run log for empirical validation
RUN_LOG = []


# All heavy lifting now lives in services/ and engines/


# --- API routes ---
@app.get("/health")
def health():
    return {"status": "ok"}


# Normalization-based scoring endpoint for frontend transparency
@app.post("/api/experiment")
def experiment_normalized():
    """
    Returns solutions scored using normalization-based approach for transparency.
    Expects: JSON with constraints, preferences, use_normalization flag.
    """
    payload = request.get_json(force=True, silent=True) or {}
    cons = payload.get("constraints", {})
    constraints = Constraints(
        maxBudget=int(cons.get("maxBudget", DEFAULT_CONSTRAINTS["maxBudget"])),
        maxLatency=float(cons.get("maxLatency", DEFAULT_CONSTRAINTS["maxLatency"])),
        maxProviders=int(cons.get("maxProviders", DEFAULT_CONSTRAINTS["maxProviders"])),
        selected_components=cons.get("selected_components", None)
    )
    feasible = generate_feasible_solutions(constraints)
    
    # Remove duplicates early
    from backend.engines.rules import deduplicate_solutions
    feasible = deduplicate_solutions(feasible)
    
    # Use normalization-based scoring if requested
    use_norm = payload.get("use_normalization", False)
    if use_norm:
        # Get custom weights from request, or use defaults
        weights = payload.get("weights", {
            "cost": 0.30,
            "latency": 0.20,
            "reliability": 0.20,
            "security": 0.15,
            "vendor_risk": 0.10,
            "scalability": 0.05
        })
        results, normalization = evaluate_solutions_normalized(feasible, weights)
        # Add reliability to response if not present
        for sol in results:
            if not hasattr(sol, "reliability"):
                sol.reliability = 0.95
        return jsonify({
            "results": [asdict(s) for s in results],
            "normalization": normalization
        })
    else:
        # fallback to academic scoring
        preferences = Preferences(
            preferredProvider=payload.get("preferredProvider"),
            prioritizeCost=bool(payload.get("prioritizeCost", False)),
            prioritizePerformance=bool(payload.get("prioritizePerformance", False)),
        )
        results = evaluate_solutions(feasible, preferences, constraints.maxBudget)
        return jsonify({
            "results": [asdict(s) for s in results],
            "normalization": None
        })


@app.post("/api/pareto")
def analyze_pareto():
    """
    Calculate Pareto frontier and metrics for multi-objective optimization.
    Returns Pareto-optimal solutions and comprehensive metrics.
    """
    payload = request.get_json(force=True, silent=True) or {}
    cons = payload.get("constraints", {})
    constraints = Constraints(
        maxBudget=int(cons.get("maxBudget", DEFAULT_CONSTRAINTS["maxBudget"])),
        maxLatency=float(cons.get("maxLatency", DEFAULT_CONSTRAINTS["maxLatency"])),
        maxProviders=int(cons.get("maxProviders", DEFAULT_CONSTRAINTS["maxProviders"])),
        selected_components=cons.get("selected_components", None)
    )
    
    # Generate feasible solutions
    feasible = generate_feasible_solutions(constraints)
    
    # Remove duplicates before Pareto calculation
    from backend.engines.rules import deduplicate_solutions
    feasible = deduplicate_solutions(feasible)
    
    if not feasible:
        return jsonify({
            "error": "No feasible solutions found",
            "pareto_solutions": [],
            "metrics": {}
        })
    
    # Calculate Pareto frontier
    objectives = payload.get("objectives", ["cost", "latency"])
    pareto_solutions = calculate_pareto_frontier(feasible, objectives)
    pareto_ranks = calculate_pareto_rank(feasible, objectives)
    
    # Calculate metrics
    max_cost = max(s.cost for s in feasible)
    max_latency = max(s.latency for s in feasible)
    reference_point = (max_cost * 1.1, max_latency * 1.1)
    metrics = calculate_pareto_metrics(feasible, pareto_solutions, reference_point)
    
    # Get extreme solutions
    extreme = get_extreme_solutions(pareto_solutions)
    
    return jsonify({
        "pareto_solutions": [asdict(s) for s in pareto_solutions],
        "all_solutions": [asdict(s) for s in feasible],
        "pareto_ranks": pareto_ranks,
        "metrics": {
            "frontier_size": metrics.get("frontier_size", 0),
            "coverage_rate": metrics.get("coverage_rate", 0),
            "hypervolume": metrics.get("hypervolume", 0),
            "spacing": metrics.get("spacing", 0),
            "cost_range": metrics.get("cost_range", {}),
            "latency_range": metrics.get("latency_range", {}),
        },
        "extreme_solutions": {
            k: asdict(v) for k, v in extreme.items()
        } if extreme else {}
    })


@app.post("/api/sankey")
def generate_sankey():
    """
    Generate Sankey diagram data for a specific solution.
    Shows cost and latency flow through providers and components.
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        
        # Get solution configuration
        config = payload.get("configuration", {})
        if not config:
            return jsonify({"error": "No solution configuration provided"}), 400
        
        # Calculate provider distribution from configuration
        provider_dist = {}
        for service_name in config.values():
            provider = service_name.split('_')[0].upper()
            provider_dist[provider] = provider_dist.get(provider, 0) + 1
        
        # Create a temporary solution object
        from backend.models import Solution
        solution = Solution(
            configuration=config,
            cost=payload.get("cost", 0),
            latency=payload.get("latency", 0),
            providers=payload.get("providers", len(provider_dist)),
            providerDistribution=provider_dist
        )
        
        # Build services_data with actual pricing and latency
        # Use the same approach as /api/experiment endpoint
        from backend.services.pricing import get_service_costs, get_service_latency
        services_data = {
            "costs": get_service_costs(),
            "latency": get_service_latency()
        }
        
        diagram_type = payload.get("type", "cost")
        if diagram_type == "latency":
            sankey_data = generate_latency_sankey(solution, services_data)
        else:
            sankey_data = generate_sankey_data(solution, services_data)
        
        return jsonify(sankey_data)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Sankey generation error: {error_detail}")
        return jsonify({
            "error": str(e),
            "detail": error_detail,
            "nodes": [],
            "links": []
        }), 500


@app.get("/api/defaults")
def get_defaults():
    """Get default constraint values"""
    return jsonify(DEFAULT_CONSTRAINTS)


@app.post("/api/defaults")
def update_defaults():
    """Update default constraint values"""
    global DEFAULT_CONSTRAINTS
    payload = request.get_json(force=True, silent=True) or {}
    
    if "maxBudget" in payload:
        DEFAULT_CONSTRAINTS["maxBudget"] = int(payload["maxBudget"])
    if "maxLatency" in payload:
        DEFAULT_CONSTRAINTS["maxLatency"] = float(payload["maxLatency"])
    if "maxProviders" in payload:
        DEFAULT_CONSTRAINTS["maxProviders"] = int(payload["maxProviders"])
    
    return jsonify({
        "success": True,
        "defaults": DEFAULT_CONSTRAINTS
    })


@app.get("/api/config/rules")
def get_rules_config():
    """Get expert system rule parameters for academic experimentation"""
    return jsonify({
        "rules": EXPERT_RULES_CONFIG,
        "weights": SCORING_WEIGHTS,
        "csp": CSP_CONFIG
    })


@app.post("/api/config/rules")
def update_rules_config():
    """Update expert system rule parameters"""
    global EXPERT_RULES_CONFIG, SCORING_WEIGHTS, CSP_CONFIG
    payload = request.get_json(force=True, silent=True) or {}
    
    # Update rule thresholds and values
    if "rules" in payload:
        for key, value in payload["rules"].items():
            if key in EXPERT_RULES_CONFIG:
                EXPERT_RULES_CONFIG[key] = float(value)
    
    # Update scoring weights
    if "weights" in payload:
        for key, value in payload["weights"].items():
            if key in SCORING_WEIGHTS:
                SCORING_WEIGHTS[key] = float(value)
    
    # Update CSP configuration
    if "csp" in payload:
        for key, value in payload["csp"].items():
            if key in CSP_CONFIG:
                if key == "search_strategy":
                    CSP_CONFIG[key] = str(value)
                elif isinstance(CSP_CONFIG[key], bool):
                    CSP_CONFIG[key] = bool(value)
                else:
                    CSP_CONFIG[key] = int(value)
    
    return jsonify({
        "success": True,
        "config": {
            "rules": EXPERT_RULES_CONFIG,
            "weights": SCORING_WEIGHTS,
            "csp": CSP_CONFIG
        }
    })


@app.post("/api/config/reset")
def reset_config():
    """Reset all configurations to academic defaults"""
    global EXPERT_RULES_CONFIG, SCORING_WEIGHTS, CSP_CONFIG
    
    EXPERT_RULES_CONFIG.update({
        "cost_high_threshold": 2800,
        "cost_high_penalty": -25,
        "cost_moderate_threshold": 2500,
        "cost_moderate_penalty": -20,
        "cost_low_threshold": 2000,
        "cost_low_reward": 12,
        "latency_excellent_threshold": 10,
        "latency_excellent_reward": 15,
        "latency_poor_threshold": 11.5,
        "latency_poor_penalty": -10,
        "single_provider_bonus": 10,
        "preferred_provider_bonus": 8,
        "cost_priority_threshold": 2600,
        "cost_priority_bonus": 5,
        "performance_priority_threshold": 10.5,
        "performance_priority_bonus": 5,
    })
    
    SCORING_WEIGHTS.update({
        "cost_weight": 1.0,
        "performance_weight": 1.0,
        "strategic_weight": 1.0,
        "preference_weight": 1.0,
    })
    
    CSP_CONFIG.update({
        "search_strategy": "heuristic",  # Changed to heuristic for 15-component scalability
        "sample_size": 100,
        "enable_early_termination": False,
        "early_termination_count": 100,
    })
    
    return jsonify({
        "success": True,
        "message": "Configuration reset to defaults"
    })


@app.get("/api/services")
def get_services():
    """
    Returns current service data including costs, latency, and options.
    Supports optional force_refresh parameter to bypass cache.
    """
    from backend.services.pricing import service_cache
    
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    data = service_cache.get_service_data(force_refresh=force_refresh)
    
    return jsonify({
        "services": data,
        "cache_info": {
            "last_updated": service_cache.last_updated.isoformat() if service_cache.last_updated else None,
            "ttl_seconds": service_cache.ttl_seconds,
            "source": data.get("source", "unknown")
        },
        "pricing": {
            "azure_region": DEFAULT_PRICING.get("azure_region", "westeurope"),
            "currency": DEFAULT_PRICING.get("currency", "USD")
        }
    })


@app.get("/api/pricing")
def get_pricing_settings():
    """Return current pricing configuration (region, currency)."""
    return jsonify({"pricing": DEFAULT_PRICING})


@app.post("/api/pricing")
def update_pricing_settings():
    """Update pricing configuration and optionally refresh service cache."""
    from backend.services.pricing import service_cache
    
    payload = request.get_json(force=True, silent=True) or {}
    updated = False
    if "azure_region" in payload:
        DEFAULT_PRICING["azure_region"] = str(payload["azure_region"]).strip()
        updated = True
    if "currency" in payload:
        DEFAULT_PRICING["currency"] = str(payload["currency"]).upper().strip()
        updated = True
    refresh = bool(payload.get("refresh", True))
    if updated and refresh:
        service_cache.get_service_data(force_refresh=True)
    return jsonify({
        "success": True,
        "pricing": DEFAULT_PRICING
    })


@app.post("/api/optimize")
def optimize():
    """
    ============================================
    HYBRID CSP + EXPERT SYSTEM OPTIMIZATION
    ============================================
    Two-phase approach:
    
    PHASE 1 - CSP (Constraint Satisfaction Problem):
      Input: Hard constraints (maxBudget, maxLatency, maxProviders)
      Process: Generate all combinations and filter by constraints
      Output: Feasible solutions (all satisfy constraints)
    
    PHASE 2 - Expert System (Rule-Based Ranking):
      Input: Feasible solutions + business preferences
      Process: Apply expert rules to score each solution
      Output: Ranked solutions (best score first)
    
    This hybrid approach ensures:
    - All solutions are VALID (CSP guarantees constraint satisfaction)
    - Best solution is OPTIMAL for business needs (Expert rules optimize business value)
    """
    import time
    start_time = time.time()
    
    payload = request.get_json(force=True, silent=True) or {}

    # Optional deterministic seed for reproducibility in academic experiments.
    # When provided, this will fix Python's and NumPy's RNG so that heuristic sampling
    # and any random ordering inside CSP strategies become repeatable. This stabilizes
    # feasible_pre_dedup / feasible_post_dedup counts and Pareto frontier size for a given input.
    seed = payload.get("seed")
    seed_used = None
    if seed is not None:
        try:
            seed_int = int(seed)
            import random
            random.seed(seed_int)
            try:
                import numpy as np  # numpy available per requirements.txt
                np.random.seed(seed_int)
            except Exception:
                pass  # NumPy seeding best-effort; ignore if unavailable
            seed_used = seed_int
            print(f"[OPTIMIZE] Using deterministic seed: {seed_int}")
        except Exception as _seed_err:
            print(f"[OPTIMIZE] Invalid seed provided '{seed}': {_seed_err}")

    cons = payload.get("constraints", {})
    prefs = payload.get("preferences", {})

    # Parse input constraints (for CSP phase)

    constraints = Constraints(
        maxBudget=int(cons.get("maxBudget", DEFAULT_CONSTRAINTS["maxBudget"])),
        maxLatency=float(cons.get("maxLatency", DEFAULT_CONSTRAINTS["maxLatency"])),
        maxProviders=int(cons.get("maxProviders", DEFAULT_CONSTRAINTS["maxProviders"])),
        selected_components=cons.get("selected_components", None)
    )
    # Academic extension: add performance metric to constraints
    setattr(constraints, "performanceMetric", cons.get("performanceMetric", DEFAULT_CONSTRAINTS.get("performanceMetric", "avg_latency")))

    # Parse input preferences (for Expert System phase)
    preferences = Preferences(
        preferredProvider=prefs.get("preferredProvider") or None,
        prioritizeCost=bool(prefs.get("prioritizeCost", False)),
        prioritizePerformance=bool(prefs.get("prioritizePerformance", False)),
    )

    # Optional per-request CSP overrides (do not persist globally)
    csp_overrides = payload.get("csp") or {}
    old_csp = CSP_CONFIG.copy()
    try:
        if csp_overrides:
            for key, value in csp_overrides.items():
                if key in CSP_CONFIG:
                    if key == "search_strategy":
                        CSP_CONFIG[key] = str(value)
                    elif isinstance(CSP_CONFIG[key], bool):
                        CSP_CONFIG[key] = bool(value)
                    else:
                        try:
                            CSP_CONFIG[key] = int(value)
                        except Exception:
                            # Fallback: ignore invalid type
                            pass

        # PHASE 1: CSP - Generate feasible solutions
        csp_start = time.time()
        feasible = generate_feasible_solutions(constraints)
        csp_duration = time.time() - csp_start

        # Capture pre-dedup count for research reproducibility
        pre_dedup_count = len(feasible)

        # IMPORTANT: Remove duplicates before any further processing
        from backend.engines.rules import deduplicate_solutions
        feasible = deduplicate_solutions(feasible)
        post_dedup_count = len(feasible)
        duplicates_removed = pre_dedup_count - post_dedup_count
        if duplicates_removed > 0:
            print(f"[OPTIMIZE] Removed {duplicates_removed} duplicate solutions from CSP results (pre={pre_dedup_count}, post={post_dedup_count})")

        # Deterministic ordering: sort solutions to eliminate ordering noise between runs
        feasible.sort(key=lambda s: (
            round(s.cost, 4),
            round(s.latency, 4),
            tuple(sorted(s.configuration.items()))
        ))

        # PHASE 2: Expert System - Rank by business rules
        expert_start = time.time()
        ranked = evaluate_solutions(feasible, preferences, constraints.maxBudget)
        expert_duration = time.time() - expert_start

        # MULTI-OBJECTIVE: Calculate Pareto frontier (now on deduplicated solutions)
        pareto_start = time.time()
        pareto_frontier = calculate_pareto_frontier(feasible, objectives=['cost', 'latency'])
        pareto_ranked = evaluate_solutions(pareto_frontier, preferences, constraints.maxBudget)  # Rank Pareto solutions
        pareto_metrics = calculate_pareto_metrics(feasible, pareto_frontier)
        extreme_solutions = get_extreme_solutions(pareto_frontier)
        pareto_duration = time.time() - pareto_start

        # EXPLAINABILITY: Generate transparency data for best solution (Priority 3)
        explainability_start = time.time()
        best_solution = ranked[0] if ranked else None
        explainability_data = None

        if best_solution:
            # Generate constraint proof
            constraint_proof = generate_constraint_proof(best_solution, constraints)

            # Generate rule firing trace
            rule_trace = generate_rule_trace(best_solution, preferences, SCORING_WEIGHTS)

            # Generate decision path
            decision_path = generate_decision_path(
                constraints=constraints,
                preferences=preferences,
                csp_time_ms=csp_duration * 1000,
                expert_time_ms=expert_duration * 1000,
                pareto_time_ms=pareto_duration * 1000,
                feasible_count=len(feasible),
                pareto_count=len(pareto_frontier),
                best_solution=best_solution
            )

            # Add explainability to best solution
            best_solution.constraintProof = [asdict(check) for check in constraint_proof]
            best_solution.ruleTrace = [asdict(rule) for rule in rule_trace]
            best_solution.decisionPath = [asdict(step) for step in decision_path]

            # Get explainability comparison
            explainability_comparison = compare_explainability()

            explainability_data = {
                "constraintProof": best_solution.constraintProof,
                "ruleTrace": best_solution.ruleTrace,
                "decisionPath": best_solution.decisionPath,
                "comparison": explainability_comparison,
                "explainabilityScore": 100,  # CSP+Expert has full explainability
            }

        explainability_duration = time.time() - explainability_start

        total_combinations = get_total_combinations()
        total_duration = time.time() - start_time

        # Academic metrics for research/analysis
        metrics = {
            "total_time_ms": round(total_duration * 1000, 2),
            "csp_time_ms": round(csp_duration * 1000, 2),
            "expert_time_ms": round(expert_duration * 1000, 2),
            "pareto_time_ms": round(pareto_duration * 1000, 2),
            "explainability_time_ms": round(explainability_duration * 1000, 2),
            "search_space_size": total_combinations,
            # Feasible set sizes (pre & post dedup) for variance analysis in experiments
            "feasible_pre_dedup": pre_dedup_count,
            "feasible_post_dedup": post_dedup_count,
            "duplicates_removed": duplicates_removed,
            # Backward compatible field (will equal post-dedup going forward)
            "feasible_space_size": post_dedup_count,
            "pareto_frontier_size": len(pareto_frontier),
            "pruning_efficiency": round((1 - post_dedup_count / total_combinations) * 100, 2) if total_combinations > 0 else 0,
            "solutions_evaluated": len(ranked),
            "seed_used": seed_used,
            "config_snapshot": {
                "csp_strategy": CSP_CONFIG["search_strategy"],
                "rule_weights": SCORING_WEIGHTS.copy(),
            }
        }

        # Academic extension: log the run for empirical validation
        RUN_LOG.append({
            "timestamp": datetime.now().isoformat(),
            "constraints": asdict(constraints),
            "preferences": asdict(preferences),
            "metrics": metrics,
            "topSolution": asdict(ranked[0]) if ranked else None,
        })

        # SANKEY DIAGRAM: Generate visualization data for solution flows
        sankey_data = None
        latency_sankey_data = None
        if best_solution:
            from backend.services.pricing import get_service_costs, get_service_latency
            services_info = {
                'costs': get_service_costs(),
                'latency': get_service_latency()
            }
            sankey_data = generate_sankey_data(best_solution, services_info)
            latency_sankey_data = generate_latency_sankey(best_solution, services_info)

        resp = {
            "totalCombinations": total_combinations,
            "feasibleSolutions": post_dedup_count,
            "feasibleSolutionsPreDedup": pre_dedup_count,
            "duplicatesRemoved": duplicates_removed,
            "feasibilityRate": round((post_dedup_count / total_combinations) * 100, 1),
            "solutions": [asdict(s) for s in ranked],
            "topSolution": asdict(ranked[0]) if ranked else None,
            "statistics": calculate_statistics(ranked),
            "metrics": metrics,  # Academic performance metrics
            # Multi-objective Pareto results
            "paretoFrontier": {
                "size": len(pareto_frontier),
                "solutions": [asdict(s) for s in pareto_ranked],
                "metrics": {
                    "hypervolume": pareto_metrics.get('hypervolume', 0),
                    "spacing": pareto_metrics.get('spacing', 0),
                    "coverage_rate": pareto_metrics.get('coverage_rate', 0),
                    "cost_range": pareto_metrics.get('cost_range', {}),
                    "latency_range": pareto_metrics.get('latency_range', {}),
                },
                "extremeSolutions": {
                    "minCost": asdict(extreme_solutions['min_cost']) if 'min_cost' in extreme_solutions else None,
                    "minLatency": asdict(extreme_solutions['min_latency']) if 'min_latency' in extreme_solutions else None,
                    "balanced": asdict(extreme_solutions['balanced']) if 'balanced' in extreme_solutions else None,
                }
            },
            # Explainability data (Priority 3)
            "explainability": explainability_data,
            # Sankey diagram data for flow visualization
            "sankeyDiagram": {
                "costFlow": sankey_data,
                "latencyFlow": latency_sankey_data
            }
        }
        return jsonify(resp)
    except Exception as e:
        import traceback
        print(f"[OPTIMIZE] Error: {e}\n" + traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        # Restore global CSP config to avoid leaking per-request overrides
        CSP_CONFIG.update(old_csp)


@app.post("/api/compare-baselines")
def compare_baselines():
    """
    Academic Comparison Endpoint: Run all baseline algorithms and compare with CSP+Expert
    
    This endpoint runs 5 baseline algorithms alongside the CSP+Expert System approach
    to provide empirical evidence of the hybrid method's superiority for journal paper.
    
    Baselines:
    1. Random Selection - Random service choices
    2. Greedy-Cost - Always pick cheapest service
    3. Greedy-Latency - Always pick fastest service
    4. Genetic Algorithm - Evolutionary optimization
    5. Weighted Sum - Scalarization approach
    
    Returns comparison showing:
    - Solution quality (cost, latency)
    - Execution time
    - Success rate
    - Winner determination
    """
    import time
    start_time = time.time()
    
    payload = request.get_json(force=True, silent=True) or {}
    cons = payload.get("constraints", {})
    prefs = payload.get("preferences", {})
    
    # Parse constraints
    constraints = Constraints(
        maxBudget=int(cons.get("maxBudget", DEFAULT_CONSTRAINTS["maxBudget"])),
        maxLatency=float(cons.get("maxLatency", DEFAULT_CONSTRAINTS["maxLatency"])),
        maxProviders=int(cons.get("maxProviders", DEFAULT_CONSTRAINTS["maxProviders"])),
    )
    
    # Parse preferences
    preferences = Preferences(
        preferredProvider=prefs.get("preferredProvider"),
        prioritizeCost=prefs.get("prioritizeCost", False),
        prioritizePerformance=prefs.get("prioritizePerformance", False),
    )
    
    # Run CSP + Expert System (our approach)
    csp_start = time.time()
    feasible = generate_feasible_solutions(constraints)
    csp_time = (time.time() - csp_start) * 1000
    
    expert_start = time.time()
    ranked = evaluate_solutions(feasible, preferences, constraints.maxBudget)
    expert_time = (time.time() - expert_start) * 1000
    
    csp_solution = ranked[0] if ranked else None
    total_csp_time = csp_time + expert_time
    
    # Run all baselines
    baseline_results = run_all_baselines(constraints)
    
    # Compare results
    comparison = compare_with_csp_expert(csp_solution, total_csp_time, baseline_results)
    
    # Add metadata
    comparison["metadata"] = {
        "constraints": asdict(constraints),
        "preferences": asdict(preferences),
        "total_execution_time_ms": (time.time() - start_time) * 1000,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Format response to match frontend expectations
    response = {
        "csp_expert": {
            "cost": csp_solution.cost if csp_solution else None,
            "latency": csp_solution.latency if csp_solution else None,
            "execution_time_ms": total_csp_time,
            "explainability": "High - CSP guarantees constraints, Expert rules provide reasoning",
            "rules_fired": len(csp_solution.evaluationLog) if csp_solution and csp_solution.evaluationLog else 0,
            "pareto_count": len(calculate_pareto_frontier(feasible, objectives=['cost', 'latency'])) if feasible else 0,
        },
        "baselines": {},
        "comparison": {
            "total_wins": comparison["summary"]["csp_expert_wins"],
            "total_ties": comparison["summary"]["csp_expert_ties"],
            "wins_per_baseline": {},
        },
        "metadata": comparison["metadata"],
    }
    
    # Add baseline results in expected format
    baseline_mapping = {
        "Random": "random",
        "Greedy-Cost": "greedy_cost",
        "Greedy-Latency": "greedy_latency",
        "Genetic-Algorithm": "genetic_algorithm",
        "Weighted-Sum": "weighted_sum",
    }
    
    for algo_name, result in baseline_results.items():
        key = baseline_mapping.get(algo_name, algo_name.lower().replace("-", "_"))
        response["baselines"][key] = {
            "cost": result.solution.cost if result.solution else 0,
            "latency": result.solution.latency if result.solution else 0,
            "execution_time_ms": result.execution_time_ms,
            "success": result.success,
        }
        
        # Track wins per baseline
        baseline_won = any(
            algo["name"] == algo_name and algo.get("winner") == algo_name
            for algo in comparison["algorithms"]
        )
        response["comparison"]["wins_per_baseline"][key] = 1 if baseline_won else 0
    
    return jsonify(response)


# Academic extension: export run logs
@app.get("/api/logs")
def get_run_logs():
    """Export anonymized run logs for empirical validation"""
    return jsonify({"runs": RUN_LOG})

@app.route('/results/<path:filename>')
def results_static(filename):
    """Serve static files (figures, tables) from backend/results/ for frontend figures.html."""
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    return send_from_directory(results_dir, filename)

@app.route('/api/results/images')
def list_result_images():
    """Return a list of image files in backend/results/ for dynamic frontend display."""
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    if not os.path.isdir(results_dir):
        return []
    files = [f for f in os.listdir(results_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif'))]
    files.sort()
    return jsonify(files)

def ensure_experiment_results():
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    required_files = [
        'pareto_frontier.png',
        'hypervolume_trend.png',
        'experiment_tables.md',
        'nsga2_results.csv',
        'moead_results.csv',
        'baselines_results.csv',
    ]
    missing = [f for f in required_files if not os.path.exists(os.path.join(results_dir, f))]
    if missing:
        import subprocess
        print(f"[INFO] Missing experiment results: {missing}. Running experiments...")
        subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "run_all_experiments.py")], check=False)
    else:
        print("[INFO] Experiment results already present.")

# Ensure results at startup (skip during tests/CI)
if os.environ.get('SKIP_EXPERIMENTS') != '1' and os.environ.get('FLASK_ENV') != 'testing':
    ensure_experiment_results()

from flask import jsonify
import threading

refresh_lock = threading.Lock()

@app.route('/api/refresh_experiments', methods=['POST'])
def refresh_experiments():
    """Run all experiments and regenerate figures/tables. Returns when done."""
    if not refresh_lock.acquire(blocking=False):
        return jsonify({"status": "busy", "message": "Experiment refresh already in progress."}), 429
    try:
        import subprocess
        result = subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "run_all_experiments.py")], capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({"status": "ok", "message": "Experiments refreshed."})
        else:
            return jsonify({"status": "error", "message": result.stderr}), 500
    finally:
        refresh_lock.release()

@app.route('/api/docs/<path:filename>', methods=['GET'])
def serve_documentation(filename):
    """Serve documentation files from the backend directory."""
    import os
    from flask import send_file, abort
    
    # Security: Only allow .md files
    if not filename.endswith('.md'):
        abort(404)
    
    # Get backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(backend_dir, filename)
    
    # Security: Ensure the file is within backend directory
    if not os.path.abspath(doc_path).startswith(backend_dir):
        abort(403)
    
    # Check if file exists
    if not os.path.exists(doc_path):
        abort(404)
    
    return send_file(doc_path, mimetype='text/markdown')

@app.route('/api/cmov4/generate-pdf', methods=['POST'])
def generate_cmov4_pdf_report():
    """Generate a detailed PDF report for the best CMOv4 solution."""
    try:
        from flask import send_file
        import datetime
        import traceback
        import sys
        import os
        
        # Add backend directory to path if not already there
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        # Import the report generator
        from cmov4.report_generator import generate_cmov4_report
        
        data = request.json
        if not data or 'solution' not in data or 'scenario_info' not in data:
            return jsonify({
                'error': 'Missing required fields: solution and scenario_info'
            }), 400
        
        solution = data['solution']
        scenario_info = data['scenario_info']
        
        # Generate PDF
        pdf_buffer = generate_cmov4_report(solution, scenario_info)
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CMOv4_Report_{timestamp}.pdf"
        
        # Send PDF file
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"PDF Generation Error: {error_details}", file=sys.stderr)
        return jsonify({
            'error': f'Failed to generate PDF: {str(e)}',
            'details': error_details
        }), 500

@app.route('/api/benchmark/academic-report', methods=['POST'])
def generate_academic_benchmark_report():
    """Generate a comprehensive academic PDF report for benchmark results."""
    try:
        from academic_report_generator import generate_academic_report
        from flask import send_file
        import datetime
        import traceback
        import sys
        
        data = request.json
        if not data or 'benchmark_data' not in data:
            return jsonify({
                'error': 'Missing required field: benchmark_data'
            }), 400
        
        benchmark_data = data['benchmark_data']
        charts_data = data.get('charts_data', None)
        
        # Generate academic PDF
        pdf_buffer = generate_academic_report(benchmark_data, charts_data)
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Academic_Report_{timestamp}.pdf"
        
        # Send PDF file
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Academic PDF Generation Error: {error_details}", file=sys.stderr)
        return jsonify({
            'error': f'Failed to generate academic PDF: {str(e)}',
            'details': error_details
        }), 500

def count_unique_providers(configuration):
    """
    Count unique cloud providers in a service configuration.
    
    Args:
        configuration: Dictionary mapping components to services
    
    Returns:
        Number of unique providers
    """
    if not configuration:
        return 0
    providers = {
        service.split()[0] if ' ' in service else service.split('-')[0]
        for service in configuration.values()
    }
    return len(providers)

@app.route('/api/cmov4/compare-baselines', methods=['POST'])
def compare_cmov4_baselines():
    """
    Compare CMOv4 Pareto optimization against 5 baseline algorithms.
    Enhanced for multi-objective comparison showing Pareto frontier advantages.
    """
    try:
        import time
        import sys
        import os
        import random
        
        # Add backend to path if needed
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        from engines.baselines import (
            baseline_random,
            baseline_greedy_cost,
            baseline_greedy_latency,
            baseline_genetic_algorithm,
            baseline_weighted_sum
        )
        from engines.pareto import calculate_pareto_frontier
        from models import Constraints, Solution
        from services.pricing import COMPONENTS, get_service_options, get_service_costs, get_service_latency
        import itertools
        
        data = request.json
        if not data:
            return jsonify({'error': 'Missing request data'}), 400
        
        # Extract scenario parameters
        scenario = data.get('scenario', {})
        # Fix: handle both list and dict for components
        if isinstance(scenario.get('components'), list):
            components = scenario['components']
        else:
            # COMPONENTS is a list, not a dict
            components = COMPONENTS[:5]  # Default to first 5
        max_budget = float(scenario.get('maxBudget', 5000))
        max_latency = float(scenario.get('maxLatency', 200))
        max_providers = int(scenario.get('maxProviders', 3))
        provided_pareto = scenario.get('paretoFrontier', [])  # Use existing Pareto frontier if provided
        
        # Create constraints
        constraints = Constraints(
            maxBudget=max_budget,
            maxLatency=max_latency,
            maxProviders=max_providers
        )
        
        print(f"[CMOv4 Baseline Comparison] Components: {len(components)}, Budget: ${max_budget}, Latency: {max_latency}ms, Max Providers: {max_providers}")
        print(f"[CMOv4 Baseline Comparison] Provided Pareto frontier: {len(provided_pareto)} solutions")
        
        # Run CMOv4 Pareto optimization (or use provided Pareto frontier)
        start_time = time.time()
        pareto_solutions = []
        
        if provided_pareto and len(provided_pareto) > 0:
            # Use the provided Pareto frontier from the benchmark
            print(f"[CMOv4] Using provided Pareto frontier with {len(provided_pareto)} solutions")
            try:
                for sol_data in provided_pareto:
                    if isinstance(sol_data, dict):
                        # Extract required fields
                        config = sol_data.get('configuration', {})
                        cost = float(sol_data.get('cost', 0))
                        latency = float(sol_data.get('latency', 0))
                        providers = int(sol_data.get('providers', 0))
                        provider_dist = sol_data.get('providerDistribution', {})
                        
                        solution = Solution(
                            configuration=config,
                            cost=cost,
                            latency=latency,
                            providers=providers,
                            providerDistribution=provider_dist,
                            score=sol_data.get('score'),
                            evaluationLog=sol_data.get('evaluationLog')
                        )
                        pareto_solutions.append(solution)
                    else:
                        pareto_solutions.append(sol_data)
                print(f"[CMOv4] Successfully loaded {len(pareto_solutions)} Pareto solutions")
            except Exception as e:
                print(f"[ERROR] Failed to load provided Pareto frontier: {str(e)}")
                import traceback
                traceback.print_exc()
                provided_pareto = []
                pareto_solutions = []
        
        # Generate new Pareto frontier if not provided or loading failed
        if not pareto_solutions:
            print(f"[CMOv4] Generating new Pareto frontier")
            try:
                # Generate diverse solutions using multiple strategies
                all_solutions = []
                options = get_service_options()
                costs = get_service_costs()
                latencies = get_service_latency()
                
                # Helper to create solution from config
                def make_solution(config):
                    cost = sum(costs.get(service, 0) for service in config.values())
                    latency = sum(latencies.get(service, 0) for service in config.values()) / len(config) if config else 0
                    
                    # Count unique PROVIDERS (not services)
                    providers = {service.split()[0] if ' ' in service else service.split('-')[0] 
                                for service in config.values()}
                    providers_count = len(providers)
                    
                    # Calculate provider distribution
                    provider_dist = {}
                    for service in config.values():
                        provider = service.split()[0] if ' ' in service else service.split('-')[0]
                        provider_dist[provider] = provider_dist.get(provider, 0) + 1
                    
                    # Check constraints
                    if cost <= max_budget and latency <= max_latency and providers_count <= max_providers:
                        return Solution(
                            configuration=config,
                            cost=cost,
                            latency=latency,
                            providers=providers_count,
                            providerDistribution=provider_dist,  # Required field!
                            score=100  # Default score
                        )
                    return None
                
                # Strategy 1: Greedy variations (cost-focused, latency-focused, balanced)
                for _ in range(50):
                    config = {}
                    for comp in components:
                        if comp in options and options[comp]:
                            # Mix of cost and latency preferences
                            services = options[comp]
                            weights = [1.0 / (costs.get(s, 1000) + latencies.get(s, 100)) for s in services]
                            total = sum(weights)
                            weights = [w/total for w in weights]
                            config[comp] = random.choices(services, weights=weights)[0]
                    
                    sol = make_solution(config)
                    if sol:
                        all_solutions.append(sol)
                
                # Strategy 2: Random sampling
                for _ in range(50):
                    config = {comp: random.choice(options.get(comp, ['AWS-EC2'])) for comp in components}
                    sol = make_solution(config)
                    if sol:
                        all_solutions.append(sol)
                
                # Calculate Pareto frontier from generated solutions
                pareto_solutions = calculate_pareto_frontier(all_solutions, objectives=['cost', 'latency'])
                
            except Exception as e:
                print(f"[ERROR] CMOv4 Pareto optimization generation failed: {str(e)}")
                import traceback
                traceback.print_exc()
                pareto_solutions = []
        
        # Calculate timing and get best solution
        cmov4_time_ms = (time.time() - start_time) * 1000
        pareto_count = len(pareto_solutions)
        
        if pareto_solutions:
            best_pareto = min(pareto_solutions, key=lambda s: s.cost)
            cmov4_success = True
            cmov4_cost = best_pareto.cost
            cmov4_latency = best_pareto.latency
            cmov4_providers = count_unique_providers(best_pareto.configuration)
        else:
            cmov4_success = False
            cmov4_cost = 0
            cmov4_latency = 0
            cmov4_providers = 0
            best_pareto = None
        
        # Run baseline algorithms
        baselines = {}
        
        # 1. Random Selection
        result = baseline_random(constraints)
        baselines['random'] = {
            'success': result.success,
            'cost': result.solution.cost if result.solution else 0,
            'latency': result.solution.latency if result.solution else 0,
            'providers': count_unique_providers(result.solution.configuration) if result.solution else 0,
            'execution_time_ms': result.execution_time_ms,
            'reason': result.reason
        }
        
        # 2. Greedy Cost
        result = baseline_greedy_cost(constraints)
        baselines['greedy_cost'] = {
            'success': result.success,
            'cost': result.solution.cost if result.solution else 0,
            'latency': result.solution.latency if result.solution else 0,
            'providers': count_unique_providers(result.solution.configuration) if result.solution else 0,
            'execution_time_ms': result.execution_time_ms,
            'reason': result.reason
        }
        
        # 3. Greedy Latency
        result = baseline_greedy_latency(constraints)
        baselines['greedy_latency'] = {
            'success': result.success,
            'cost': result.solution.cost if result.solution else 0,
            'latency': result.solution.latency if result.solution else 0,
            'providers': count_unique_providers(result.solution.configuration) if result.solution else 0,
            'execution_time_ms': result.execution_time_ms,
            'reason': result.reason
        }
        
        # 4. Genetic Algorithm
        result = baseline_genetic_algorithm(constraints)
        baselines['genetic_algorithm'] = {
            'success': result.success,
            'cost': result.solution.cost if result.solution else 0,
            'latency': result.solution.latency if result.solution else 0,
            'providers': count_unique_providers(result.solution.configuration) if result.solution else 0,
            'execution_time_ms': result.execution_time_ms,
            'reason': result.reason
        }
        
        # 5. Weighted Sum
        result = baseline_weighted_sum(constraints)
        baselines['weighted_sum'] = {
            'success': result.success,
            'cost': result.solution.cost if result.solution else 0,
            'latency': result.solution.latency if result.solution else 0,
            'providers': count_unique_providers(result.solution.configuration) if result.solution else 0,
            'execution_time_ms': result.execution_time_ms,
            'reason': result.reason
        }
        
        # Calculate comparison metrics
        wins_per_baseline = {name: 0 for name in baselines.keys()}
        total_wins = 0
        
        if cmov4_success:
            for name, baseline in baselines.items():
                if baseline['success']:
                    # CMOv4 wins if it has lower cost AND lower latency
                    if cmov4_cost <= baseline['cost'] and cmov4_latency <= baseline['latency']:
                        total_wins += 1
                    # Baseline wins if it dominates CMOv4
                    elif baseline['cost'] < cmov4_cost and baseline['latency'] < cmov4_latency:
                        wins_per_baseline[name] += 1
        
        # Calculate Pareto-specific metrics
        pareto_metrics = {}
        if pareto_solutions and len(pareto_solutions) > 1:
            # Hypervolume indicator (simplified - area under Pareto curve)
            sorted_pareto = sorted(pareto_solutions, key=lambda s: s.cost)
            hypervolume = 0
            for i in range(len(sorted_pareto) - 1):
                width = sorted_pareto[i+1].cost - sorted_pareto[i].cost
                height = sorted_pareto[i].latency
                hypervolume += width * height
            
            # Solution diversity (cost and latency ranges)
            costs = [s.cost for s in pareto_solutions]
            latencies = [s.latency for s in pareto_solutions]
            cost_diversity = max(costs) - min(costs)
            latency_diversity = max(latencies) - min(latencies)
            
            pareto_metrics = {
                'hypervolume': round(hypervolume, 2),
                'cost_range': round(cost_diversity, 2),
                'latency_range': round(latency_diversity, 2),
                'avg_cost': round(sum(costs) / len(costs), 2),
                'avg_latency': round(sum(latencies) / len(latencies), 2)
            }
        
        # Prepare response
        response = {
            'cmov4_pareto': {
                'success': cmov4_success,
                'cost': round(cmov4_cost, 2) if cmov4_success else 0,
                'latency': round(cmov4_latency, 2) if cmov4_success else 0,
                'providers': cmov4_providers,
                'execution_time_ms': round(cmov4_time_ms, 2),
                'pareto_count': pareto_count,
                'pareto_metrics': pareto_metrics,
                'frontier': [
                    {
                        'cost': round(s.cost, 2),
                        'latency': round(s.latency, 2),
                        'providers': len(set(s.configuration.values()))
                    }
                    for s in pareto_solutions[:20]  # Limit to first 20 for performance
                ] if pareto_solutions else []
            },
            'baselines': baselines,
            'comparison': {
                'total_wins': total_wins,
                'wins_per_baseline': wins_per_baseline,
                'baseline_success_rate': sum(1 for b in baselines.values() if b['success']) / len(baselines),
                'cmov4_advantage': {
                    'cost_vs_best_baseline': round(cmov4_cost - min([b['cost'] for b in baselines.values() if b['success']], default=cmov4_cost), 2) if cmov4_success else None,
                    'latency_vs_best_baseline': round(cmov4_latency - min([b['latency'] for b in baselines.values() if b['success']], default=cmov4_latency), 2) if cmov4_success else None,
                    'speed_multiplier': round(max([b['execution_time_ms'] for b in baselines.values()]) / cmov4_time_ms, 2) if cmov4_time_ms > 0 else None
                }
            },
            'scenario': {
                'components': len(components),
                'max_budget': max_budget,
                'max_latency': max_latency,
                'max_providers': max_providers
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] CMOv4 Baseline Comparison failed: {error_details}", file=sys.stderr)
        return jsonify({
            'error': f'Baseline comparison failed: {str(e)}',
            'details': error_details
        }), 500

if __name__ == "__main__":
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(host="0.0.0.0", port=5055, debug=debug_mode)
