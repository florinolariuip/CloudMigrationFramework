"""
CMOv4 Optimizer
- CSP, Rule Engine, Pareto logic for advanced models
"""
from .models import Architecture, Component

# Mapping from CMOv4 component types to CMOv3 service names
COMPONENT_TYPE_MAPPING = {
    'web': 'api_gateway',
    'compute': 'application_server',
    'database': 'database',
    'cache': 'cache',
    'monitoring': 'monitoring',
    'message_queue': 'message_queue',
    'storage': 'storage',
    'load_balancer': 'load_balancer',
    'backup': 'backup',
    'security': 'encryption',
    'cdn': 'cdn',
    'analytics': 'analytics',
    'encryption': 'encryption',
    'containers': 'containers',
    'serverless_compute': 'serverless_compute',
    'identity': 'identity_management'
}

def map_cmov4_to_cmov3_components(components: list) -> list:
    """
    Map CMOv4 component types to CMOv3 service names.
    """
    mapped = []
    for comp in components:
        comp_type = comp.get('type', '').lower()
        if comp_type in COMPONENT_TYPE_MAPPING:
            mapped.append(COMPONENT_TYPE_MAPPING[comp_type])
    return list(set(mapped)) if mapped else None  # Remove duplicates

def optimize_architecture(arch: dict, constraints: dict, config: dict = None) -> dict:
    """
    Main entry for CMOv4 optimization.
    Uses the existing CMOv3 backend infrastructure with dynamic component selection.
    
    Step 1: Map CMOv4 architecture to CMOv3 constraints
    Step 2: Use CMOv3 CSP + Expert System for optimization (with all thresholds and rules)
    Step 3: Compute Pareto frontier and explanations
    
    Args:
        arch: Architecture dict with components, relationships, etc.
        constraints: Constraints dict with maxBudget, maxLatency, etc.
        config: Optional CSP configuration (search_strategy, sample_size)
    """
    try:
        # Import CMOv3 optimization logic
        from backend.models import Constraints, Preferences
        from backend.engines.constraints import generate_feasible_solutions
        from backend.engines.rules import evaluate_solutions, deduplicate_solutions
        from backend.engines.pareto import calculate_pareto_frontier, calculate_pareto_metrics, get_extreme_solutions
        from backend.config import EXPERT_RULES_CONFIG, SCORING_WEIGHTS, CSP_CONFIG
        
        # Temporarily update CSP_CONFIG if custom config provided
        original_config = None
        if config:
            original_config = CSP_CONFIG.copy()
            CSP_CONFIG.update(config)
        
        # Extract component names for selected_components
        components = arch.get('components', [])
        selected_components = map_cmov4_to_cmov3_components(components)
        
        # Map CMOv4 constraints to CMOv3 Constraints
        cmov3_constraints = Constraints(
            maxBudget=constraints.get('maxBudget', 10000),
            maxLatency=constraints.get('maxLatency', 150),
            maxProviders=len(constraints.get('requiredProviders', ['AWS', 'Azure', 'GCP'])),
            selected_components=selected_components
        )
        
        # Extract preferences from constraints dict or use defaults
        prefs_dict = constraints.get('preferences', {})
        preferences = Preferences(
            preferredProvider=prefs_dict.get('preferredProvider') or None,
            prioritizeCost=bool(prefs_dict.get('prioritizeCost', False)),
            prioritizePerformance=bool(prefs_dict.get('prioritizePerformance', True))
        )
        
        # Step 1: CSP - Generate feasible solutions
        feasible_solutions = generate_feasible_solutions(cmov3_constraints)
        
        # Deduplicate solutions BEFORE any further processing
        feasible_solutions = deduplicate_solutions(feasible_solutions)

        if not feasible_solutions:
            return {
                'solutions': [],
                'pareto_frontier': [],
                'explanations': ['No feasible solutions found for the given constraints'],
                'metrics': {},
                'thresholds_used': EXPERT_RULES_CONFIG
            }

        # Step 2: Rule Engine - Rank solutions using CMOv3 expert rules with thresholds
        ranked_solutions = evaluate_solutions(feasible_solutions, preferences, cmov3_constraints.maxBudget)

        # Step 3: Pareto Frontier - Select non-dominated solutions
        pareto_solutions = calculate_pareto_frontier(feasible_solutions, objectives=['cost', 'latency'])
        
        # Deduplicate Pareto solutions (safety check)
        pareto_solutions = deduplicate_solutions(pareto_solutions)

        # Enhanced cost calculation using UsageProfile + Instance Counts
        from backend.models import UsageProfile
        from backend.services.pricing import calculate_total_cost, get_service_costs
        from .helpers import get_instance_counts
        
        # Extract usage_profile from constraints and convert to UsageProfile object
        usage_profile_dict = constraints.get('usage_profile', {})
        if isinstance(usage_profile_dict, dict):
            usage_profile = UsageProfile(**usage_profile_dict)
        elif isinstance(usage_profile_dict, UsageProfile):
            usage_profile = usage_profile_dict
        else:
            usage_profile = UsageProfile()  # Use defaults
        
        # Extract instance counts from architecture
        instance_counts = get_instance_counts(components)
        total_instances = sum(instance_counts.values())
        print(f"[CMOv4] Instance counts: {instance_counts} (Total: {total_instances})")
        
        # Map CMOv3 service types to CMOv4 component types for scaling
        SERVICE_TO_COMPONENT_TYPE = {
            'api_gateway': 'web',
            'application_server': 'compute',
            'database': 'database',
            'cache': 'cache',
            'monitoring': 'monitoring',
            'message_queue': 'message_queue',
            'storage': 'storage',
            'load_balancer': 'load_balancer',
            'backup': 'backup',
            'encryption': 'encryption',
            'cdn': 'cdn',
            'analytics': 'analytics',
            'containers': 'containers',
            'serverless_compute': 'serverless_compute',
        }
        
        # Get base service costs
        service_costs = get_service_costs()
        
        # Recalculate costs with instance scaling
        for s in ranked_solutions:
            # Start with base cost (includes usage profile)
            base_cost = calculate_total_cost(s.configuration, usage_profile)
            
            # Add instance scaling for compute resources
            scaled_cost = 0
            for service_name in s.configuration.values():
                service_cost = service_costs.get(service_name, 0)
                
                # Determine component type from service name
                comp_type = None
                for svc_type, cmp_type in SERVICE_TO_COMPONENT_TYPE.items():
                    if svc_type in service_name.lower().replace(' ', '_'):
                        comp_type = cmp_type
                        break
                
                # Scale by instance count (default 1 if not found)
                instance_count = instance_counts.get(comp_type, 1) if comp_type else 1
                scaled_cost += service_cost * instance_count
            
            s.cost = scaled_cost if scaled_cost > 0 else base_cost
            
        for s in pareto_solutions:
            # Same scaling logic for Pareto solutions
            base_cost = calculate_total_cost(s.configuration, usage_profile)
            
            scaled_cost = 0
            for service_name in s.configuration.values():
                service_cost = service_costs.get(service_name, 0)
                
                comp_type = None
                for svc_type, cmp_type in SERVICE_TO_COMPONENT_TYPE.items():
                    if svc_type in service_name.lower().replace(' ', '_'):
                        comp_type = cmp_type
                        break
                
                instance_count = instance_counts.get(comp_type, 1) if comp_type else 1
                scaled_cost += service_cost * instance_count
            
            s.cost = scaled_cost if scaled_cost > 0 else base_cost

        # Calculate Pareto metrics for explainability
        max_cost = max(s.cost for s in feasible_solutions)
        max_latency = max(s.latency for s in feasible_solutions)
        reference_point = (max_cost * 1.1, max_latency * 1.1)
        pareto_metrics = calculate_pareto_metrics(feasible_solutions, pareto_solutions, reference_point)
        extreme_solutions = get_extreme_solutions(pareto_solutions)

        # Build detailed explanations
        explanations = [
            f"Generated {len(feasible_solutions)} feasible solutions from {len(components)} components",
            f"Pareto frontier contains {len(pareto_solutions)} non-dominated solutions",
            f"Architecture pattern: {arch.get('architecture_pattern', 'unknown')}",
            f"",
            "Expert System Rules Applied:",
            f"- Cost thresholds: High=${EXPERT_RULES_CONFIG['cost_high_threshold']}, Low=${EXPERT_RULES_CONFIG['cost_low_threshold']}",
            f"- Latency thresholds: Excellent<{EXPERT_RULES_CONFIG['latency_excellent_threshold']}ms, Poor>{EXPERT_RULES_CONFIG['latency_poor_threshold']}ms",
            f"- Single provider bonus: +{EXPERT_RULES_CONFIG['single_provider_bonus']} points",
            f"",
            "Best Solution:",
            f"- Cost: ${ranked_solutions[0].cost:.2f}/month" if ranked_solutions else "N/A",
            f"- Latency: {ranked_solutions[0].latency:.1f}ms" if ranked_solutions else "N/A",
            f"- Providers: {ranked_solutions[0].providers}" if ranked_solutions else "N/A",
            f"- Score: {ranked_solutions[0].score}" if ranked_solutions else "N/A"
        ]

        # Format results for CMOv4 response
        from dataclasses import asdict
        return {
            'solutions': [asdict(s) for s in ranked_solutions[:10]],  # Top 10
            'pareto_frontier': [asdict(s) for s in pareto_solutions],
            'explanations': explanations,
            'metrics': {
                'feasible_count': len(feasible_solutions),
                'pareto_count': len(pareto_solutions),
                'hypervolume': pareto_metrics.get('hypervolume', 0),
                'coverage_rate': pareto_metrics.get('coverage_rate', 0),
                'cost_range': pareto_metrics.get('cost_range', {}),
                'latency_range': pareto_metrics.get('latency_range', {}),
            },
            'extreme_solutions': {
                'min_cost': asdict(extreme_solutions['min_cost']) if 'min_cost' in extreme_solutions else None,
                'min_latency': asdict(extreme_solutions['min_latency']) if 'min_latency' in extreme_solutions else None,
                'balanced': asdict(extreme_solutions['balanced']) if 'balanced' in extreme_solutions else None,
            },
            'thresholds_used': {
                'cost_high': EXPERT_RULES_CONFIG['cost_high_threshold'],
                'cost_low': EXPERT_RULES_CONFIG['cost_low_threshold'],
                'latency_excellent': EXPERT_RULES_CONFIG['latency_excellent_threshold'],
                'latency_poor': EXPERT_RULES_CONFIG['latency_poor_threshold'],
                'single_provider_bonus': EXPERT_RULES_CONFIG['single_provider_bonus']
            },
            'scoring_weights': SCORING_WEIGHTS
        }
    except Exception as e:
        import traceback
        return {
            'solutions': [],
            'pareto_frontier': [],
            'explanations': [f"Error: {str(e)}", traceback.format_exc()],
            'metrics': {},
            'thresholds_used': {},
            'scoring_weights': {}
        }
    finally:
        # Restore original CSP_CONFIG if it was modified
        if original_config is not None:
            CSP_CONFIG.clear()
            CSP_CONFIG.update(original_config)

def run_csp(arch: Architecture, constraints: dict) -> list:
    """
    Generate feasible solutions using CSP logic.
    To be implemented: use relationships, tech stack, instance counts, and constraints.
    """
    # TODO: Implement CSP logic
    return []

def run_rule_engine(solutions: list, arch: Architecture, constraints: dict) -> tuple:
    """
    Filter and rank solutions using business rules and selection logic.
    Returns filtered solutions and explanations.
    """
    # TODO: Implement rule engine logic
    return solutions, []

def compute_pareto_frontier(solutions: list) -> list:
    """
    Compute Pareto frontier for trade-off analysis (cost, latency, etc).
    Returns non-dominated solutions.
    """
    # TODO: Implement Pareto frontier logic
    return solutions
