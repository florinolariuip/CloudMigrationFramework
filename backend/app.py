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
from backend.models import Constraints, Preferences, Solution
from backend.services.pricing import get_total_combinations, COMPONENTS
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
from backend.engines.terraform_generator import (
    generate_terraform_for_solution,
    generate_deployment_script
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

    # Extract latency model selection and attach to constraints for CMOv4
    latency_model = request.args.get('latency_model') or request.args.get('performance_metric')
    if latency_model:
        scenario.setdefault('constraints', {})['performanceMetric'] = latency_model
    
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
    # Persist selected performance metric (avg_latency | tail_latency | throughput | graph_latency)
    if "performanceMetric" in payload:
        DEFAULT_CONSTRAINTS["performanceMetric"] = str(payload.get("performanceMetric", "avg_latency"))
    
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
    Returns current service data with live API integration status.
    Enhanced to show real-time pricing source information.
    """
    from backend.services.pricing import service_cache
    
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    data = service_cache.get_service_data(force_refresh=force_refresh)
    
    # Extract API integration metrics
    pricing_sources = data.get("pricing_sources", {})
    api_status = data.get("api_status", {})
    live_percentage = data.get("live_data_percentage", 0)
    
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
        },
        "network_latency": __nl_status(),
        "live_api_status": {
            "success_rate": pricing_sources.get("success_rate", "0%"),
            "live_services": pricing_sources.get("live_services", 0),
            "fallback_services": pricing_sources.get("fallback_services", 0),
            "live_data_percentage": live_percentage,
            "provider_status": {
                "aws": "✅ Live" if api_status.get("aws") else "❌ Fallback",
                "azure": "✅ Live" if api_status.get("azure") else "❌ Fallback", 
                "gcp": "✅ Live" if api_status.get("gcp") else "❌ Fallback"
            },
            "integration_quality": (
                "Excellent" if live_percentage >= 80 else
                "Good" if live_percentage >= 60 else
                "Partial" if live_percentage >= 30 else
                "Poor"
            )
        }
    })

def __nl_status():
    try:
        from backend.services.network_latency_store import status, get_override
        st = status()
        # Do not include full matrix by default to keep payload small
        return {
            "has_override": st.get("has_override"),
            "entries": st.get("entries"),
            "ttl_seconds": st.get("ttl_seconds"),
            "age_seconds": st.get("age_seconds"),
        }
    except Exception:
        return {
            "has_override": False
        }

@app.get("/api/pricing-status")
def get_pricing_status():
    """
    Dedicated endpoint for live API integration monitoring.
    Useful for health checks and debugging.
    """
    from backend.services.pricing import service_cache
    
    data = service_cache.get_service_data()
    sources = data.get("sources", {})
    
    # Count services by source type
    live_count = sum(1 for source in sources.values() if "Live" in source)
    fallback_count = sum(1 for source in sources.values() if "Fallback" in source)
    total_count = len(sources)
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "total_services": total_count,
        "live_services": live_count,
        "fallback_services": fallback_count,
        "live_percentage": round(live_count / total_count * 100, 1) if total_count > 0 else 0,
        "api_status": data.get("api_status", {}),
        "pricing_sources": data.get("pricing_sources", {}),
        "service_breakdown": {
            service: source for service, source in sources.items()
        },
        "recommendations": [
            "✅ Excellent API integration" if live_count >= total_count * 0.8 else
            "⚠️ Some APIs failing, check network/credentials" if live_count >= total_count * 0.5 else
            "❌ Most APIs failing, using fallback data"
        ]
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


# Live network latency override endpoints
@app.get("/api/network-latency")
def get_network_latency_override():
    """Return current network latency matrix (default + override status)."""
    try:
        from backend.services.network_latency_store import get_override, status
        override = get_override()
        # Convert tuple keys to "a,b" for JSON friendliness
        override_json = {f"{a},{b}": v for (a, b), v in override.items()} if override else None
        return jsonify({
            "override": override_json,
            "status": status()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/network-latency")
def set_network_latency_override():
    """Set or clear the live network latency override matrix.

    Body formats supported:
    - { "matrix": { "us-east-1,eu-west-1": 92.0, ... }, "ttl_seconds": 3600 }
    - { "clear": true }
    """
    try:
        from backend.services.network_latency_store import set_override, clear_override, status
        payload = request.get_json(force=True, silent=True) or {}
        if payload.get("clear"):
            clear_override()
            return jsonify({"success": True, "status": status()})
        matrix = payload.get("matrix", {})
        ttl = payload.get("ttl_seconds")
        if not isinstance(matrix, dict) or not matrix:
            return jsonify({"error": "matrix must be a non-empty object mapping 'from,to' to milliseconds"}), 400
        set_override(matrix, ttl_seconds=ttl)
        return jsonify({"success": True, "status": status()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/network-latency/probe")
def probe_network_latency():
    """Probe TCP connect times (ms) from the server to regional endpoints.

    Query params:
      - regions: comma-separated region codes (default inferred from latency model)
      - attempts: number of attempts per region (default 3)
      - timeout_ms: per-attempt timeout in ms (default 500)
      - host_template: Python format string with {region} (default 'ec2.{region}.amazonaws.com')
      - port: TCP port to connect to (default 443)

    NOTE: This measures server→region connectivity, not inter-region RTTs.
    Use results to calibrate overrides manually via POST /api/network-latency.
    """
    import socket, time, statistics
    from typing import List

    # Infer default regions from latency model keys
    try:
        from backend.engines.latency_graph import RealisticLatencyModel
        model_regions = set()
        for (a, b) in RealisticLatencyModel().network_latency.keys():
            model_regions.add(a)
            model_regions.add(b)
        default_regions = sorted(model_regions)
    except Exception:
        default_regions = [
            'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-south-1', 'ap-northeast-1'
        ]

    regions_param = (request.args.get('regions') or '').strip()
    regions: List[str] = [r.strip() for r in regions_param.split(',') if r.strip()] or default_regions
    attempts = max(1, int(request.args.get('attempts', 3)))
    timeout_ms = max(100, int(request.args.get('timeout_ms', 500)))
    host_tmpl = request.args.get('host_template', 'ec2.{region}.amazonaws.com')
    port = int(request.args.get('port', 443))

    def connect_once(host: str, port: int, timeout_s: float) -> float | None:
        start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout_s):
                pass
            end = time.perf_counter()
            return (end - start) * 1000.0
        except Exception:
            return None

    results = {}
    measured = 0
    failed = 0
    for region in regions:
        host = host_tmpl.format(region=region)
        samples = []
        successes = 0
        for _ in range(attempts):
            ms = connect_once(host, port, timeout_ms / 1000.0)
            if ms is not None:
                samples.append(round(ms, 2))
                successes += 1
        if successes:
            measured += 1
            median_ms = round(statistics.median(samples), 2)
            results[region] = {
                'target': f'{host}:{port}',
                'attempts': attempts,
                'successes': successes,
                'samples_ms': samples,
                'median_ms': median_ms,
            }
        else:
            failed += 1
            results[region] = {
                'target': f'{host}:{port}',
                'attempts': attempts,
                'successes': 0,
                'error': f'All attempts failed (timeout {timeout_ms}ms)'
            }

    return jsonify({
        'regions': regions,
        'attempts': attempts,
        'timeout_ms': timeout_ms,
        'port': port,
        'host_template': host_tmpl,
        'summary': { 'measured': measured, 'failed': failed },
        'results': results,
        'note': 'These are server→region TCP connect medians, not inter-region RTTs.'
    })

@app.post("/api/multi-cloud-analysis")
def analyze_multi_cloud():
    """
    Analyze multi-cloud configuration for latency, cost, and operational concerns.
    Provides recommendations for addressing cross-cloud issues.
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        config = payload.get("configuration", {})
        
        if not config:
            return jsonify({"error": "No configuration provided"}), 400
        
        # Analyze provider distribution
        providers = {}
        for component, service in config.items():
            provider = service.split(' ')[0]
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(component)
        
        # Calculate cross-cloud penalties
        from backend.engines.constraints import calculate_cross_cloud_penalty, calculate_data_transfer_cost
        latency_penalty = calculate_cross_cloud_penalty(config)
        transfer_cost = calculate_data_transfer_cost(config, 100)  # 100GB/month
        
        # Generate recommendations
        recommendations = []
        if len(providers) > 1:
            recommendations.extend([
                "Consider regional co-location to reduce latency",
                "Implement caching to minimize cross-cloud data transfer",
                "Use dedicated network connections (VPN/peering)",
                "Monitor data transfer costs closely"
            ])
        
        if len(providers) > 2:
            recommendations.append("Consider reducing to 2 providers to minimize operational complexity")
        
        # Operational complexity assessment
        complexity_factors = {
            "multiple_consoles": len(providers),
            "billing_systems": len(providers),
            "security_models": len(providers),
            "api_integrations": len(config)
        }
        
        complexity_score = (
            len(providers) * 2 +  # Provider complexity
            len(config) * 0.1 +   # Service complexity
            (len(providers) - 1) * 1.5  # Cross-cloud complexity
        )
        
        return jsonify({
            "provider_analysis": {
                "providers": providers,
                "provider_count": len(providers),
                "is_multi_cloud": len(providers) > 1
            },
            "latency_analysis": {
                "cross_cloud_penalty_ms": round(latency_penalty, 2),
                "impact_level": "High" if latency_penalty > 15 else "Medium" if latency_penalty > 8 else "Low"
            },
            "cost_analysis": {
                "monthly_transfer_cost": round(transfer_cost, 2),
                "annual_transfer_cost": round(transfer_cost * 12, 2)
            },
            "operational_complexity": {
                "complexity_score": round(complexity_score, 1),
                "complexity_level": "High" if complexity_score > 8 else "Medium" if complexity_score > 4 else "Low",
                "factors": complexity_factors
            },
            "recommendations": recommendations,
            "mitigation_strategies": {
                "latency": [
                    "Deploy services in same regions (e.g., us-east-1, East US, us-east1)",
                    "Use CDN for static content delivery",
                    "Implement local caching layers"
                ],
                "cost": [
                    "Compress data transfers",
                    "Batch API calls",
                    "Use message queues for async communication"
                ],
                "complexity": [
                    "Use Terraform for unified infrastructure management",
                    "Implement consistent monitoring across clouds",
                    "Standardize security policies and tagging"
                ]
            }
        })
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Multi-cloud analysis error: {error_detail}")
        return jsonify({
            "error": str(e),
            "detail": error_detail
        }), 500

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
    # Handle component selection - convert UI strings to component names
    selected_components = cons.get("selected_components")
    if selected_components and isinstance(selected_components, list):
        # Map UI component names to internal component names
        component_mapping = {
            'Web Frontend': 'api_gateway',
            'Application Server': 'application_server', 
            'Database': 'database',
            'Cache': 'cache',
            'Monitoring': 'monitoring',
            'Storage': 'storage',
            'Message Queue': 'message_queue',
            'CDN': 'cdn',
            'Load Balancer': 'load_balancer',
            'Backup': 'backup',
            'Encryption': 'encryption',
            'Containers': 'containers',
            'Serverless Compute': 'serverless_compute',
            'Identity Management': 'identity_management',
            'Analytics': 'analytics'
        }
        mapped_components = []
        for comp in selected_components:
            if comp in component_mapping:
                mapped_components.append(component_mapping[comp])
            elif comp.lower() in [c.lower() for c in COMPONENTS]:
                mapped_components.append(comp.lower())
        selected_components = mapped_components if mapped_components else None
        print(f"[DEBUG] UI components: {cons.get('selected_components')}")
        print(f"[DEBUG] Mapped components: {selected_components}")

    constraints = Constraints(
        maxBudget=int(cons.get("maxBudget", DEFAULT_CONSTRAINTS["maxBudget"])),
        maxLatency=float(cons.get("maxLatency", DEFAULT_CONSTRAINTS["maxLatency"])),
        maxProviders=int(cons.get("maxProviders", DEFAULT_CONSTRAINTS["maxProviders"])),
        selected_components=selected_components
    )
    # Add workload profile if provided
    workload = payload.get("workload")
    if workload:
        constraints.workload_profile = {
            'requests_per_month': int(workload.get('requests_per_month', 0)),
            'cross_az_gb': int(workload.get('cross_az_gb', 0)),
            'internet_egress_gb': int(workload.get('internet_egress_gb', 0)),
            'ebs_gb': int(workload.get('ebs_gb', 0)),
            'rds_backup_gb': int(workload.get('rds_backup_gb', 0)),
            's3_gb': int(workload.get('s3_gb', 0))
        }
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
        print(f"[TIMING] Starting CSP phase with constraints: Budget=${constraints.maxBudget}, Latency={constraints.maxLatency}ms, Providers={constraints.maxProviders}")
        csp_start = time.time()
        feasible = generate_feasible_solutions(constraints)
        csp_duration = time.time() - csp_start
        print(f"[TIMING] CSP phase completed: {csp_duration*1000:.1f}ms")

        # Capture pre-dedup count for research reproducibility
        pre_dedup_count = len(feasible)

        # IMPORTANT: Remove duplicates before any further processing
        from backend.engines.rules import deduplicate_solutions
        feasible = deduplicate_solutions(feasible)
        post_dedup_count = len(feasible)
        duplicates_removed = pre_dedup_count - post_dedup_count
        if duplicates_removed > 0:
            print(f"[OPTIMIZE] Removed {duplicates_removed} duplicate solutions from CSP results (pre={pre_dedup_count}, post={post_dedup_count})")

        # Generate suggestions if no feasible solutions
        if not feasible:
            suggestions = []
            component_count = len(constraints.selected_components) if constraints.selected_components else 5
            
            if constraints.maxBudget < component_count * 1000:
                suggestions.append(f"Increase budget to ${component_count * 1500}/month (${component_count * 1500 - constraints.maxBudget} more)")
            
            if constraints.maxLatency < 100:
                suggestions.append(f"Increase max latency to 200-400ms (currently {constraints.maxLatency}ms)")
            
            if component_count > 6:
                suggestions.append(f"Reduce components to 4-6 (currently {component_count} selected)")
            
            if constraints.maxProviders == 1:
                suggestions.append("Allow 2-3 providers for more service options")
            
            return jsonify({
                "error": "No feasible solutions found",
                "suggestions": suggestions,
                "totalCombinations": get_total_combinations(),
                "feasibleSolutions": 0,
                "solutions": [],
                "metrics": {"feasible_count": 0}
            })

        # Deterministic ordering: sort solutions to eliminate ordering noise between runs
        feasible.sort(key=lambda s: (
            round(s.cost, 4),
            round(s.latency, 4),
            tuple(sorted(s.configuration.items()))
        ))

        # PHASE 2: Expert System - Rank by business rules
        print(f"[TIMING] Starting Expert System phase with {len(feasible)} solutions")
        expert_start = time.time()
        ranked = evaluate_solutions(feasible, preferences, constraints.maxBudget)
        expert_duration = time.time() - expert_start
        print(f"[TIMING] Expert System completed: {expert_duration*1000:.1f}ms, ranked {len(ranked)} solutions")

        # MULTI-OBJECTIVE: Calculate Pareto frontier (now on deduplicated solutions)
        print(f"[TIMING] Starting Pareto frontier calculation")
        pareto_start = time.time()
        pareto_frontier = calculate_pareto_frontier(feasible, objectives=['cost', 'latency'])
        pareto_ranked = evaluate_solutions(pareto_frontier, preferences, constraints.maxBudget)  # Rank Pareto solutions
        pareto_metrics = calculate_pareto_metrics(feasible, pareto_frontier)
        extreme_solutions = get_extreme_solutions(pareto_frontier)
        pareto_duration = time.time() - pareto_start
        print(f"[TIMING] Pareto frontier completed: {pareto_duration*1000:.1f}ms, found {len(pareto_frontier)} optimal solutions")

        # EXPLAINABILITY: Generate transparency data for best solution (Priority 3)
        print(f"[TIMING] Starting explainability generation")
        explainability_start = time.time()
        # Select best solution from Pareto frontier based on user preferences
        # Use balanced knee point as representative solution (optimal cost-latency trade-off)
        best_solution = extreme_solutions.get('balanced') if extreme_solutions else (ranked[0] if ranked else None)
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
        print(f"[TIMING] Explainability completed: {explainability_duration*1000:.1f}ms")

        total_combinations = get_total_combinations()
        total_duration = time.time() - start_time
        print(f"[TIMING] TOTAL OPTIMIZATION: {total_duration*1000:.1f}ms")
        print(f"[TIMING] Performance breakdown - CSP: {csp_duration*1000:.1f}ms ({(csp_duration/total_duration)*100:.1f}%), Expert: {expert_duration*1000:.1f}ms ({(expert_duration/total_duration)*100:.1f}%), Pareto: {pareto_duration*1000:.1f}ms ({(pareto_duration/total_duration)*100:.1f}%), Explain: {explainability_duration*1000:.1f}ms ({(explainability_duration/total_duration)*100:.1f}%)")

        # Academic metrics for research/analysis
        metrics = {
            "total_time_ms": round(total_duration * 1000, 2),
            "csp_time_ms": round(csp_duration * 1000, 2),
            "expert_time_ms": round(expert_duration * 1000, 2),
            "pareto_time_ms": round(pareto_duration * 1000, 2),
            "explainability_time_ms": round(explainability_duration * 1000, 2),
            "sankey_time_ms": round(sankey_duration * 1000, 2) if 'sankey_duration' in locals() else 0,
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
        # Include selected latency model for clarity in comparisons (avg_latency | tail_latency | throughput | graph_latency)
        try:
            metrics["latency_model"] = getattr(constraints, "performanceMetric", DEFAULT_CONSTRAINTS.get("performanceMetric", "avg_latency"))
        except Exception:
            metrics["latency_model"] = DEFAULT_CONSTRAINTS.get("performanceMetric", "avg_latency")

        # Academic extension: log the run for empirical validation
        RUN_LOG.append({
            "timestamp": datetime.now().isoformat(),
            "constraints": asdict(constraints),
            "preferences": asdict(preferences),
            "metrics": metrics,
            "topSolution": asdict(best_solution) if best_solution else None,
        })

        # SANKEY DIAGRAM: Generate visualization data for solution flows
        sankey_start = time.time()
        sankey_data = None
        latency_sankey_data = None
        terraform_preview = None
        if best_solution:
            from backend.services.pricing import get_service_costs, get_service_latency
            services_info = {
                'costs': get_service_costs(),
                'latency': get_service_latency()
            }
            sankey_data = generate_sankey_data(best_solution, services_info)
            latency_sankey_data = generate_latency_sankey(best_solution, services_info)
            
            # Generate Terraform preview for multi-cloud solutions
            if best_solution.providers > 1:
                try:
                    terraform_preview = generate_terraform_for_solution(best_solution)[:500] + "..." # Preview only
                except Exception as e:
                    print(f"[WARNING] Terraform preview generation failed: {e}")
                    terraform_preview = None
        
        sankey_duration = time.time() - sankey_start
        print(f"[TIMING] Sankey diagrams: {sankey_duration*1000:.1f}ms")

        resp = {
            "totalCombinations": total_combinations,
            "feasibleSolutions": post_dedup_count,
            "feasibleSolutionsPreDedup": pre_dedup_count,
            "duplicatesRemoved": duplicates_removed,
            "feasibilityRate": round((post_dedup_count / total_combinations) * 100, 1),
            "solutions": [asdict(s) for s in ranked],
            "topSolution": asdict(best_solution) if best_solution else None,
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
            },
            # Multi-cloud operational insights
            "multiCloudInsights": {
                "terraformPreview": terraform_preview,
                "crossCloudLatency": calculate_cross_cloud_penalty(best_solution.configuration) if best_solution else 0,
                "dataTransferCost": calculate_data_transfer_cost(best_solution.configuration, 100) if best_solution else 0,
                "operationalComplexity": "High" if best_solution and best_solution.providers > 2 else "Medium" if best_solution and best_solution.providers > 1 else "Low"
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
        
# Import cross-cloud penalty functions at module level
from backend.engines.constraints import calculate_cross_cloud_penalty, calculate_data_transfer_cost


@app.post("/api/compare-baselines")
def compare_baselines():
    """
    Academic Comparison Endpoint: Run all baseline algorithms and compare with CSP+Expert
    
    This endpoint runs 5 baseline algorithms alongside the CSP+Expert System approach
    to provide empirical evidence of the hybrid method's superiority for journal paper.
    
    Enhanced to accept pre-computed CSP+Expert results with accurate timing.
    
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
    
    # Check if pre-computed results are provided
    provided_solution = payload.get("providedSolution")
    provided_timing = payload.get("providedTiming", {})
    provided_pareto = payload.get("providedParetoFrontier", [])
    
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
    
    # Use provided results if available (Option 1: accurate timing)
    if provided_solution and provided_timing:
        print(f"[CMOv3 Baseline Comparison] Using provided solution and timing")
        # Reconstruct solution from provided data
        csp_solution = Solution(
            configuration=provided_solution.get('configuration', {}),
            cost=float(provided_solution.get('cost', 0)),
            latency=float(provided_solution.get('latency', 0)),
            providers=int(provided_solution.get('providers', 1)),
            providerDistribution=provided_solution.get('providerDistribution', {}),
            score=provided_solution.get('score'),
            evaluationLog=provided_solution.get('evaluationLog', [])
        )
        csp_time = provided_timing.get('csp_time_ms', 0)
        expert_time = provided_timing.get('expert_time_ms', 0)
        pareto_time = provided_timing.get('pareto_time_ms', 0)
        total_csp_time = provided_timing.get('total_time_ms', csp_time + expert_time)
        pareto_count = len(provided_pareto)
        
        print(f"[CMOv3] Provided timing: CSP={csp_time}ms, Expert={expert_time}ms, Pareto={pareto_time}ms, Total={total_csp_time}ms")
    else:
        # Run CSP + Expert System (fallback if no provided results)
        print(f"[CMOv3 Baseline Comparison] Running new CSP+Expert optimization")
        csp_start = time.time()
        feasible = generate_feasible_solutions(constraints)
        csp_time = (time.time() - csp_start) * 1000
        
        expert_start = time.time()
        ranked = evaluate_solutions(feasible, preferences, constraints.maxBudget)
        expert_time = (time.time() - expert_start) * 1000
        
        pareto_start = time.time()
        pareto_frontier = calculate_pareto_frontier(feasible, objectives=['cost', 'latency']) if feasible else []
        pareto_time = (time.time() - pareto_start) * 1000
        pareto_count = len(pareto_frontier)
        
        csp_solution = ranked[0] if ranked else None
        total_csp_time = csp_time + expert_time + pareto_time
    
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
            "timing_breakdown": {
                "csp_time_ms": round(csp_time, 2),
                "expert_time_ms": round(expert_time, 2),
                "pareto_time_ms": round(pareto_time, 2),
                "total_time_ms": round(total_csp_time, 2)
            },
            "explainability": "High - CSP guarantees constraints, Expert rules provide reasoning",
            "rules_fired": len(csp_solution.evaluationLog) if csp_solution and csp_solution.evaluationLog else 0,
            "pareto_count": pareto_count,
        },
        "baselines": {},
        "comparison": {
            "total_wins": comparison["summary"]["csp_expert_wins"],
            "total_ties": comparison["summary"]["csp_expert_ties"],
            "wins_per_baseline": {},
            "csp_expert_advantage": {
                "pareto_solutions_count": pareto_count,
                "explainability": "Full CSP+Expert+Pareto pipeline with rule traces"
            }
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

@app.post("/api/terraform")
def generate_terraform():
    """
    Generate Terraform Infrastructure-as-Code for a solution.
    Addresses operational complexity by providing unified IaC templates.
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        
        # Get solution configuration
        config = payload.get("configuration", {})
        if not config:
            return jsonify({"error": "No solution configuration provided"}), 400
        
        # Create a temporary solution object
        from backend.models import Solution
        solution = Solution(
            configuration=config,
            cost=payload.get("cost", 0),
            latency=payload.get("latency", 0),
            providers=payload.get("providers", 1),
            providerDistribution=payload.get("providerDistribution", {})
        )
        
        # Generate Terraform configuration
        terraform_config = generate_terraform_for_solution(solution)
        deployment_script = generate_deployment_script(solution)
        
        # Calculate estimated deployment time and complexity
        providers = set(service.split(' ')[0] for service in config.values())
        complexity_score = len(providers) * 2 + len(config) * 0.5
        estimated_time_minutes = max(10, int(complexity_score * 3))
        
        return jsonify({
            "terraform_config": terraform_config,
            "deployment_script": deployment_script,
            "metadata": {
                "providers": list(providers),
                "services_count": len(config),
                "complexity_score": round(complexity_score, 1),
                "estimated_deployment_time_minutes": estimated_time_minutes,
                "multi_cloud": len(providers) > 1,
                "recommendations": [
                    "Review provider credentials before deployment",
                    "Test in staging environment first",
                    "Set up monitoring and alerting",
                    "Configure backup and disaster recovery"
                ] + (["Consider VPN/peering for cross-cloud connectivity"] if len(providers) > 1 else [])
            }
        })
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Terraform generation error: {error_detail}")
        return jsonify({
            "error": str(e),
            "detail": error_detail
        }), 500

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
        from services.pricing import COMPONENTS, get_service_options, get_service_costs, get_service_latency, _resolve_service_key, get_cost_for_service, get_latency_for_service
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
            components = COMPONENTS  # Use all 18 components by default
        max_budget = float(scenario.get('maxBudget', 5000))
        max_latency = float(scenario.get('maxLatency', 200))
        max_providers = int(scenario.get('maxProviders', 3))
        provided_pareto = scenario.get('paretoFrontier', [])  # Use existing Pareto frontier if provided
        
        # Get CMOv4 timing data if provided (more accurate than regenerating)
        cmov4_timing = scenario.get('timing', {})
        cmov4_csp_time = cmov4_timing.get('csp_time_ms', 0)
        cmov4_expert_time = cmov4_timing.get('expert_time_ms', 0)
        cmov4_pareto_time = cmov4_timing.get('pareto_time_ms', 0)
        cmov4_total_time = cmov4_timing.get('total_time_ms', 0)
        
        # Create constraints
        constraints = Constraints(
            maxBudget=max_budget,
            maxLatency=max_latency,
            maxProviders=max_providers,
            selected_components=components
        )
        
        print(f"[CMOv4 Baseline Comparison] Components: {len(components)}, Budget: ${max_budget}, Latency: {max_latency}ms, Max Providers: {max_providers}")
        print(f"[CMOv4 Baseline Comparison] Provided Pareto frontier: {len(provided_pareto)} solutions")
        print(f"[CMOv4 Baseline Comparison] Provided timing: CSP={cmov4_csp_time}ms, Expert={cmov4_expert_time}ms, Pareto={cmov4_pareto_time}ms, Total={cmov4_total_time}ms")
        
        # Use provided CMOv4 results (Option 1: more accurate and fair)
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
        
        # If no provided solutions, return error (baseline comparison requires CMOv4 results first)
        if not pareto_solutions:
            return jsonify({
                'error': 'No CMOv4 results provided. Please run CMOv4 optimization first.',
                'cmov4_pareto': {'success': False, 'pareto_count': 0},
                'baselines': {}
            }), 400
        
        # Use provided timing (accurate) instead of measuring here
        cmov4_time_ms = cmov4_total_time if cmov4_total_time > 0 else 0.04  # Fallback to minimal value
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
                'timing_breakdown': {
                    'csp_time_ms': round(cmov4_csp_time, 2),
                    'expert_time_ms': round(cmov4_expert_time, 2),
                    'pareto_time_ms': round(cmov4_pareto_time, 2),
                    'total_time_ms': round(cmov4_time_ms, 2)
                },
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
                    'speed_multiplier': round(max([b['execution_time_ms'] for b in baselines.values()]) / cmov4_time_ms, 2) if cmov4_time_ms > 0 else None,
                    'pareto_solutions_count': pareto_count,
                    'explainability': 'Full CSP+Expert+Pareto pipeline with rule traces'
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
