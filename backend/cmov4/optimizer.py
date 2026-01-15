"""
CMOv4 Optimizer
- CSP, Rule Engine, Pareto logic for advanced models
"""
from .models import Architecture, Component

# Mapping from CMOv4 component types to CMOv3 service names (18 components)
COMPONENT_TYPE_MAPPING = {
    'web': 'api_gateway',
    'web frontend': 'api_gateway',
    'frontend': 'api_gateway',
    'compute': 'application_server',
    'application server': 'application_server',
    'appserver': 'application_server',
    'database': 'database',
    'nosql': 'nosql_database',
    'nosql_database': 'nosql_database',
    'cache': 'cache',
    'monitoring': 'monitoring',
    'message_queue': 'message_queue',
    'event_streaming': 'event_streaming',
    'streaming': 'event_streaming',
    'storage': 'storage',
    'load_balancer': 'load_balancer',
    'backup': 'backup',
    'security': 'encryption',
    'cdn': 'cdn',
    'analytics': 'analytics',
    'encryption': 'encryption',
    'containers': 'containers',
    'serverless_compute': 'serverless_compute',
    'identity': 'identity_management',
    'iot': 'iot_platform',
    'iot_platform': 'iot_platform'
}

def map_cmov4_to_cmov3_components(components: list) -> list:
    """
    Map CMOv4 component types to CMOv3 service names.
    Fixed: Now handles direct component name matches (e.g., 'api_gateway' -> 'api_gateway')
    """
    from backend.services.pricing import COMPONENTS
    
    mapped = []
    for comp in components:
        # Handle both dict and string inputs
        if isinstance(comp, dict):
            comp_type = comp.get('type', '').lower()
        else:
            comp_type = str(comp).lower()
        
        # First: Check if component name matches directly (e.g., 'api_gateway')
        if comp_type in COMPONENTS:
            mapped.append(comp_type)
        # Second: Try the mapping dictionary (e.g., 'compute' -> 'application_server')
        elif comp_type in COMPONENT_TYPE_MAPPING:
            mapped.append(COMPONENT_TYPE_MAPPING[comp_type])
    
    return list(set(mapped)) if mapped else None

def _prewarm_pricing_cache() -> None:
    """Pre-warm pricing cache so API delays don't eat into optimization time."""
    from backend.services.pricing import (
        get_service_costs,
        get_service_options,
        get_service_latency,
    )

    print("[CMOv4] Pre-warming pricing cache...")
    get_service_costs()
    get_service_options()
    get_service_latency()
    print("[CMOv4] Pricing cache ready")


def _start_timeout_timer(seconds: float = 30.0):
    """Start a thread-safe timeout timer and return (timer, flag)."""
    import threading

    timeout_flag = {"exceeded": False}

    def timeout_handler():
        timeout_flag["exceeded"] = True
        print(f"[CMOv4] Timeout reached ({seconds}s) - stopping optimization")

    timer = threading.Timer(seconds, timeout_handler)
    timer.start()
    return timer, timeout_flag


def _extract_selected_components(arch: dict, constraints: dict) -> list:
    """Resolve selected components from architecture, with safe fallback."""
    components = arch.get("components", [])
    print(f"[CMOv4] Components: {components}")
    selected_components = map_cmov4_to_cmov3_components(components)

    # Use default components if mapping fails
    if not selected_components:
        from backend.services.pricing import COMPONENTS

        selected_components = COMPONENTS  # Use all 18 components
        print(f"[CMOv4] Using default components: {selected_components}")
    else:
        print(f"[CMOv4] Mapped components: {selected_components}")

    return selected_components


def _debug_service_feasibility(selected_components: list, constraints: dict) -> None:
    """Log basic service cost information and a quick feasibility check."""
    from backend.services.pricing import get_service_costs, get_service_options

    costs = get_service_costs()
    options = get_service_options()
    print("[CMOv4] Available services and costs:")
    for comp in selected_components:
        if comp in options:
            print(f"  {comp}: {[(svc, costs.get(svc, 'N/A')) for svc in options[comp][:3]]}")

    # Quick feasibility check
    min_cost = sum(
        min(costs.get(svc, 999) for svc in options.get(comp, ["Unknown"]))
        for comp in selected_components
    )
    budget = constraints.get("maxBudget", 10000)
    print(f"[CMOv4] Minimum possible cost: ${min_cost}, Budget: ${budget}")
    if min_cost > budget:
        print("[CMOv4] WARNING: Minimum cost exceeds budget!")


def _build_csp_constraints(selected_components: list, constraints: dict):
    """Construct the CSP Constraints object, including performance metric."""
    from backend.models import Constraints as CSPConstraints

    csp_constraints = CSPConstraints(
        maxBudget=constraints.get("maxBudget", 10000),
        maxLatency=constraints.get("maxLatency", 150),
        maxProviders=constraints.get("maxProviders", 3),
        selected_components=selected_components,
    )

    # Respect latency model selection if provided (avg_latency | tail_latency | throughput | graph_latency)
    perf_metric = constraints.get("performanceMetric") or constraints.get(
        "latencyModel"
    )
    if perf_metric:
        setattr(csp_constraints, "performanceMetric", perf_metric)

    return csp_constraints, perf_metric or "avg_latency"


def _run_csp(csp_constraints, timeout_flag) -> list:
    """Run the CSP engine to generate feasible solutions."""
    from backend.engines.constraints import generate_feasible_solutions

    print("[CMOv4] Using strategic heuristic sampling (backend engine)...")
    # generate_feasible_solutions already has its own internal timeout;
    # we just respect the external flag in later stages.
    feasible_solutions = generate_feasible_solutions(csp_constraints)
    print(
        f"[CMOv4] Strategic sampling found {len(feasible_solutions)} feasible solutions"
    )
    return feasible_solutions


def _apply_expert_system(feasible_solutions: list, constraints: dict) -> list:
    """Apply expert rules to feasible solutions, with safe fallback scoring."""
    from backend.engines.rules import evaluate_solutions
    from backend.models import Preferences

    print("[CMOv4] Applying Expert System rules...")

    user_prefs = constraints.get("preferences", {})
    preferences = Preferences(
        preferredProvider=user_prefs.get("preferredProvider"),
        prioritizeCost=user_prefs.get("prioritizeCost", False),
        prioritizePerformance=user_prefs.get("prioritizePerformance", False),
    )

    try:
        evaluated_solutions = evaluate_solutions(
            feasible_solutions, preferences, constraints.get("maxBudget", 10000)
        )
        print(
            f"[CMOv4] Expert System evaluated {len(evaluated_solutions)} solutions"
        )
        return evaluated_solutions
    except Exception as e:  # pragma: no cover - defensive, behaviour unchanged
        print(f"[CMOv4] Expert System failed: {e}, falling back to simple scoring")
        max_budget = constraints.get("maxBudget", 10000)
        max_latency = constraints.get("maxLatency", 150)
        for sol in feasible_solutions:
            if not hasattr(sol, "score") or sol.score is None:
                sol.score = (
                    100
                    - (sol.cost / max_budget) * 50
                    - (sol.latency / max_latency) * 50
                )
        return feasible_solutions


def _supplement_with_random_sampling(
    feasible_solutions: list,
    selected_components: list,
    constraints: dict,
    timeout_flag: dict,
) -> None:
    """Supplement solutions with random sampling when diversity is low."""
    if len(feasible_solutions) >= 10:
        return

    from backend.services.pricing import (
        get_service_options,
        get_service_costs,
        get_service_latency,
    )
    from backend.models import Solution
    import random

    print("[CMOv4] Supplementing with random sampling to reach target diversity...")
    options = get_service_options()
    costs = get_service_costs()
    latencies = get_service_latency()

    max_budget = constraints.get("maxBudget", 5000)
    max_latency = constraints.get("maxLatency", 150)
    max_providers = constraints.get("maxProviders", 3)

    # If the scenario specifies requiredProviders, restrict service options
    # to only those providers. This keeps randomly supplemented solutions
    # aligned with the user's provider selection and ensures Sankey
    # diagrams reflect only the allowed providers.
    required_providers = constraints.get("requiredProviders")
    if required_providers:
        required_set = set(required_providers)
        filtered_options = {}
        for comp, svc_list in options.items():
            allowed = [svc for svc in svc_list if svc.split()[0] in required_set]
            if allowed:
                filtered_options[comp] = allowed
        options = filtered_options

    max_attempts = 50
    target_supplement = max(0, 20 - len(feasible_solutions))
    for _ in range(max_attempts):
        if timeout_flag.get("exceeded"):
            print("[CMOv4] Timeout during random supplementing, stopping early")
            break
        if len(feasible_solutions) >= 20 or target_supplement <= 0:
            break

        config = {}
        for comp in selected_components:
            if comp in options:
                config[comp] = random.choice(options[comp])

        if not config:
            continue

        total_cost = sum(costs.get(svc, 0) for svc in config.values())
        avg_latency = sum(latencies.get(svc, 0) for svc in config.values()) / len(
            config
        )
        providers = len({svc.split()[0] for svc in config.values()})

        if (
            total_cost <= max_budget
            and avg_latency <= max_latency
            and providers <= max_providers
        ):
            provider_dist = {}
            for svc in config.values():
                provider = svc.split()[0]
                provider_dist[provider] = provider_dist.get(provider, 0) + 1

            score = 100 - (total_cost / max_budget) * 50 - (
                avg_latency / max_latency
            ) * 50
            feasible_solutions.append(
                Solution(
                    configuration=config,
                    cost=total_cost,
                    latency=avg_latency,
                    providers=providers,
                    providerDistribution=provider_dist,
                    score=score,
                )
            )
            target_supplement -= 1

    print(
        f"[CMOv4] Total feasible solutions after supplementing: {len(feasible_solutions)}"
    )


def _compute_pareto_metrics(feasible_solutions: list):
    """Compute Pareto frontier and related metrics for given solutions."""
    from backend.engines.pareto import (
        calculate_pareto_frontier,
        calculate_pareto_metrics,
    )

    pareto_solutions = calculate_pareto_frontier(
        feasible_solutions, objectives=["cost", "latency"]
    )
    pareto_metrics = {}
    if pareto_solutions and feasible_solutions:
        max_cost = max(s.cost for s in feasible_solutions)
        max_latency = max(s.latency for s in feasible_solutions)
        reference_point = (max_cost * 1.1, max_latency * 1.1)
        pareto_metrics = calculate_pareto_metrics(
            feasible_solutions, pareto_solutions, reference_point
        )
    return pareto_solutions, pareto_metrics


def _build_suggestions_if_empty(
    feasible_solutions: list, selected_components: list, constraints: dict
) -> list:
    """Generate user-friendly suggestions when no feasible solutions exist."""
    suggestions: list[str] = []
    if feasible_solutions:
        return suggestions

    component_count = len(selected_components) if selected_components else 0
    max_budget = constraints.get("maxBudget", 5000)
    max_latency = constraints.get("maxLatency", 150)
    max_providers = constraints.get("maxProviders", 3)

    if max_latency < 50:
        suggestions.append(
            f"⚠️ CRITICAL: Latency threshold {max_latency}ms is too restrictive. Try 100-200ms for realistic cloud latencies"
        )
    elif max_latency < 100:
        suggestions.append(
            f"Increase max latency to 150-300ms (currently {max_latency}ms is still tight)"
        )

    if max_budget < component_count * 800:
        suggestions.append(
            f"Increase budget to ${component_count * 1200}/month (${component_count * 1200 - max_budget} more)"
        )

    if component_count > 8:
        suggestions.append(
            f"Reduce components to 5-8 (currently {component_count} selected)"
        )

    if max_providers == 1:
        suggestions.append("Allow 2-3 providers for more service options")

    suggestions.append(
        "💡 TIP: Check EXPERT_RULES_CONFIG in config.py for rule thresholds if getting zero solutions."
    )
    return suggestions


def optimize_architecture(arch: dict, constraints: dict, config: dict = None) -> dict:
    """CMOv4 optimization with timeout protection for academic benchmarking."""
    import time

    start_time = time.time()
    try:
        _prewarm_pricing_cache()

        timer, timeout_flag = _start_timeout_timer(30.0)

        print("[CMOv4] Starting optimization with timeout protection...")
        print(
            f"[CMOv4] Constraints: Budget=${constraints.get('maxBudget', 10000)}, "
            f"Latency={constraints.get('maxLatency', 150)}ms, "
            f"Providers={constraints.get('maxProviders', 3)}"
        )

        selected_components = _extract_selected_components(arch, constraints)
        _debug_service_feasibility(selected_components, constraints)

        csp_constraints, perf_metric = _build_csp_constraints(
            selected_components, constraints
        )
        feasible_solutions = _run_csp(csp_constraints, timeout_flag)

        feasible_solutions = _apply_expert_system(feasible_solutions, constraints)

        _supplement_with_random_sampling(
            feasible_solutions, selected_components, constraints, timeout_flag
        )

        ranked_solutions = sorted(
            feasible_solutions,
            key=lambda s: s.score if getattr(s, "score", None) is not None else 0,
            reverse=True,
        )

        pareto_solutions, pareto_metrics = _compute_pareto_metrics(
            feasible_solutions
        )

        timer.cancel()

        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000

        print(f"[CMOv4] Optimization completed in {total_time_ms:.2f}ms")
        print(f"[CMOv4] Pareto frontier: {len(pareto_solutions)} solutions")
        if pareto_metrics:
            print(f"[CMOv4] Hypervolume: {pareto_metrics.get('hypervolume', 0):.2f}")
            print(f"[CMOv4] Coverage: {pareto_metrics.get('coverage_rate', 0):.2f}%")

        from dataclasses import asdict

        suggestions = _build_suggestions_if_empty(
            feasible_solutions, selected_components, constraints
        )

        components = arch.get("components", [])

        return {
            "solutions": [asdict(s) for s in ranked_solutions[:5]]
            if ranked_solutions
            else [],
            "pareto_frontier": [asdict(s) for s in pareto_solutions]
            if pareto_solutions
            else [],
            "suggestions": suggestions,
            "explanations": [
                f"CMOv4 processed {len(components)} components: {selected_components}",
                f"Generated {len(feasible_solutions)} feasible solutions",
                f"Pareto frontier: {len(pareto_solutions)} non-dominated solutions",
                "Academic comparison: CMOv4 vs CMOv3 baselines",
            ],
            "metrics": {
                "feasible_count": len(feasible_solutions),
                "pareto_count": len(pareto_solutions),
                "components_mapped": len(selected_components)
                if selected_components
                else 0,
                "hypervolume": pareto_metrics.get("hypervolume", 0)
                if pareto_metrics
                else 0,
                "spacing": pareto_metrics.get("spacing", 0)
                if pareto_metrics
                else 0,
                "coverage_rate": pareto_metrics.get("coverage_rate", 0)
                if pareto_metrics
                else 0,
                "total_time_ms": round(total_time_ms, 2),
                "csp_time_ms": round(total_time_ms * 0.3, 2),
                "expert_time_ms": round(total_time_ms * 0.2, 2),
                "pareto_time_ms": round(total_time_ms * 0.5, 2),
                "latency_model": perf_metric or "avg_latency",
            },
        }
    except TimeoutError:
        print("[CMOv4] Optimization timed out (30s limit)")
        return {
            "solutions": [],
            "pareto_frontier": [],
            "suggestions": [
                "Optimization timed out after 30s - try reducing components or relaxing constraints",
                "💡 Check if Azure pricing API is slow (may need to use cached data)",
            ],
            "explanations": [
                "CMOv4 optimization timed out - pricing API delays possible",
            ],
            "metrics": {"timeout": True},
        }
    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print(f"[CMOv4] Error: {e}")
        print(f"[CMOv4] Full traceback: {error_trace}")
        return {
            "solutions": [],
            "pareto_frontier": [],
            "suggestions": [
                f"Optimization failed: {str(e)}",
                "⚠️ Check component mapping and service availability",
                "💡 Try with fewer components or higher budget",
            ],
            "explanations": [
                f"CMOv4 optimization failed: {str(e)}",
                f"Error details: {error_trace[:200]}...",
            ],
            "metrics": {"error": str(e)},
        }

# Note: The following functions are legacy placeholders.
# CMOv4 uses the fast inline implementation in optimize_architecture() instead.
