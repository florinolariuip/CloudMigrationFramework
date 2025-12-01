
# Constraints Engine (CSP):
# This module generates and filters possible cloud migration solutions using hard constraints.
# Key numbers: budget, latency, provider count, dependencies. See EXPLANATION.md for full details.

from __future__ import annotations

from typing import Dict, List, Any
import itertools

from backend.models import Constraints, Solution
from backend.services.pricing import (
    get_service_options,
    get_service_costs,
    get_service_latency,
    COMPONENTS,
    get_total_combinations,
)
from backend.services.pricing import _resolve_service_key, get_cost_for_service, get_latency_for_service
from backend.config import CSP_CONFIG, SERVICE_DEPENDENCIES



# Calculate data transfer costs between cloud providers
def calculate_data_transfer_cost(config: Dict[str, str], monthly_gb: float = 100) -> float:
    """Calculate estimated monthly data transfer costs between clouds"""
    providers = {s.split(" ")[0] for s in config.values()}
    if len(providers) <= 1:
        return 0.0  # Single cloud, no transfer costs
    
    # Data transfer costs per GB between providers
    transfer_costs = {
        ('AWS', 'Azure'): 0.09,
        ('AWS', 'GCP'): 0.12,
        ('Azure', 'GCP'): 0.12
    }
    
    total_cost = 0.0
    provider_list = list(providers)
    for i in range(len(provider_list)):
        for j in range(i + 1, len(provider_list)):
            pair = tuple(sorted([provider_list[i], provider_list[j]]))
            cost_per_gb = transfer_costs.get(pair, 0.15)  # Default $0.15/GB
            total_cost += cost_per_gb * monthly_gb
    
    return total_cost

# Calculate the total monthly cost for a given configuration.
# Each service's cost is fetched from pricing; sum all selected services + data transfer.
def calculate_total_cost(config: Dict[str, str], workload_profile: Dict[str, int] = None) -> float:
    if workload_profile:
        from backend.services.pricing import calculate_workload_cost
        return calculate_workload_cost(config, **workload_profile)
    
    # Fallback to base costs + transfer
    base_cost = sum(get_cost_for_service(s) for s in config.values())
    transfer_cost = calculate_data_transfer_cost(config, 100)
    return base_cost + transfer_cost



# Calculate cross-cloud latency penalty based on provider distribution
def calculate_cross_cloud_penalty(config: Dict[str, str]) -> float:
    """Calculate latency penalty for cross-cloud communication"""
    providers = {s.split(" ")[0] for s in config.values()}
    if len(providers) <= 1:
        return 0.0  # Single cloud, no penalty
    
    # Define cross-cloud latency penalties (ms)
    cross_cloud_penalties = {
        ('AWS', 'Azure'): 8.0,
        ('AWS', 'GCP'): 10.0, 
        ('Azure', 'GCP'): 12.0
    }
    
    penalty = 0.0
    provider_list = list(providers)
    for i in range(len(provider_list)):
        for j in range(i + 1, len(provider_list)):
            pair = tuple(sorted([provider_list[i], provider_list[j]]))
            penalty += cross_cloud_penalties.get(pair, 15.0)  # Default 15ms
    
    return penalty / len(providers)  # Average penalty per provider

# Calculate performance metric for a configuration.
# Supported metrics:
#   - avg_latency: mean latency across all services + cross-cloud penalty
#   - tail_latency: 95th percentile latency (demo: sorted, index)
#   - throughput: inverse of mean latency (demo: 1000 / avg)
def calculate_performance(config: Dict[str, str], metric: str = "avg_latency") -> float:
    latencies = [get_latency_for_service(s) for s in config.values()]
    if not latencies:
        return 0.0
    
    base_latency = 0.0
    if metric == "avg_latency":
        base_latency = sum(latencies) / len(latencies)
    elif metric == "tail_latency":
        # 95th percentile (approximate)
        sorted_latencies = sorted(latencies)
        base_latency = sorted_latencies[int(0.95 * len(sorted_latencies))] if sorted_latencies else 0.0
    elif metric == "throughput":
        # Demo: throughput = 1000 / avg_latency
        avg = sum(latencies) / len(latencies)
        return 1000 / avg if avg > 0 else 0.0
    else:
        base_latency = sum(latencies) / len(latencies)
    
    # Add cross-cloud penalty for multi-cloud configurations
    cross_cloud_penalty = calculate_cross_cloud_penalty(config)
    return base_latency + cross_cloud_penalty



# Count the number of unique cloud providers in the configuration.
# Provider is inferred from the first word of each service string.
def count_providers(config: Dict[str, str]) -> int:
    providers = {s.split(" ")[0] for s in config.values()}
    return len(providers)



# Return a count of services per provider in the configuration.
def provider_distribution(config: Dict[str, str]) -> Dict[str, int]:
    dist: Dict[str, int] = {}
    for s in config.values():
        p = s.split(" ")[0]
        dist[p] = dist.get(p, 0) + 1
    return dist



# Check if all service dependencies are satisfied.
# E.g., if RDS is chosen, EC2 must also be present.
def check_dependencies(config: Dict[str, str]) -> bool:
    for rule in SERVICE_DEPENDENCIES:
        if rule["if"] in config.values() and rule["requires"] not in config.values():
            return False
    return True



# Main entry: generate all feasible solutions given constraints.
# Steps:
#   1. Generate all possible service combinations (Cartesian product)
#   2. Apply hard constraints:
#       - Budget (cost <= maxBudget)
#       - Performance (latency <= maxLatency)
#       - Provider count (<= maxProviders)
#       - Dependencies (check_dependencies)
#   3. Prune configs with missing cost data
#   4. Return list of Solution objects for scoring/ranking

def generate_feasible_solutions(constraints: Constraints) -> List[Solution]:
    """
    Constraints Engine (CSP):
    - Generates combinations over selected components (or all if not specified)
    - Applies hard constraints: budget, performance (selected metric), max providers, interdependencies
    - Supports pruning strategies (exhaustive, heuristic, random_sample, ml placeholder)
    """
    import time
    start_time = time.time()
    
    solutions: List[Solution] = []
    service_options = get_service_options()
    metric = getattr(constraints, "performanceMetric", "avg_latency")

    # Use selected_components if provided, else default to all COMPONENTS
    selected_components = constraints.selected_components if constraints.selected_components else COMPONENTS
    print(f"[TIMING] CSP starting with {len(selected_components)} components, strategy: {CSP_CONFIG.get('search_strategy', 'exhaustive')}")

    strategy = CSP_CONFIG.get("search_strategy", "exhaustive")
    combination_start = time.time()
    picks = itertools.product(*(service_options[c] for c in selected_components))
    if strategy == "random_sample":
        import random
        all_picks = list(picks)
        picks = random.sample(all_picks, min(CSP_CONFIG.get("sample_size", 1000), len(all_picks)))
        print(f"[TIMING] Random sampling: {len(picks)} from {len(all_picks)} combinations")
    elif strategy == "heuristic":
        import random
        print(f"[TIMING] Pre-caching pricing data for heuristic generation...")
        
        # Pre-cache all pricing data to avoid repeated API calls
        costs = get_service_costs()
        latencies = get_service_latency()
        
        # Pre-sort all options by cost and latency to avoid repeated sorting
        sorted_by_cost = {}
        sorted_by_latency = {}
        for component in selected_components:
            options = service_options.get(component, [])
            if options:
                sorted_by_cost[component] = sorted(options, key=lambda x: costs.get(x, 999999))
                sorted_by_latency[component] = sorted(options, key=lambda x: latencies.get(x, 999999))
            else:
                sorted_by_cost[component] = []
                sorted_by_latency[component] = []
        
        print(f"[TIMING] Pricing data cached, generating heuristic combinations...")
        heuristic_picks = []

        # Strategy 1: Pure cheapest (cost-optimized)
        if all(sorted_by_cost[c] for c in selected_components):
            heuristic_picks.append([sorted_by_cost[c][0] for c in selected_components])

        # Strategy 2: Pure fastest (performance-optimized)
        if all(sorted_by_latency[c] for c in selected_components):
            heuristic_picks.append([sorted_by_latency[c][0] for c in selected_components])

        # Strategy 3-5: Balanced - pick from top 2 options (simplified)
        for _ in range(3):
            pick = []
            for c in selected_components:
                cost_opts = sorted_by_cost[c][:2]
                latency_opts = sorted_by_latency[c][:2]
                all_opts = list(set(cost_opts + latency_opts))
                if all_opts:
                    pick.append(random.choice(all_opts))
                elif service_options.get(c):
                    pick.append(service_options[c][0])
            if len(pick) == len(selected_components):
                heuristic_picks.append(pick)

        # Strategy 6-8: Single-provider solutions (simplified)
        for provider in ['AWS', 'Azure', 'GCP']:
            pick = []
            for c in selected_components:
                provider_opts = [opt for opt in service_options.get(c, []) if opt.startswith(provider)]
                if provider_opts:
                    pick.append(provider_opts[0])  # Use first available instead of min cost lookup
                elif sorted_by_cost.get(c):
                    pick.append(sorted_by_cost[c][0])
            if len(pick) == len(selected_components):
                heuristic_picks.append(pick)

        # Strategy 9-20: Random sampling (reduced from 40 to 12 for speed)
        for _ in range(12):
            pick = []
            for c in selected_components:
                opts = service_options.get(c, [])
                if opts:
                    pick.append(random.choice(opts))
            if len(pick) == len(selected_components):
                heuristic_picks.append(pick)

        picks = heuristic_picks
        print(f"[TIMING] Heuristic generation: {len(heuristic_picks)} strategic combinations in {(time.time() - combination_start)*1000:.1f}ms")
    elif strategy == "ml":
        # Use iterator directly, don't convert to list
        picks = itertools.islice(picks, CSP_CONFIG.get("sample_size", 1000))
        print(f"[TIMING] ML sampling: up to {CSP_CONFIG.get('sample_size', 1000)} combinations")
    else:
        # Exhaustive - use iterator directly to avoid memory issues
        print(f"[TIMING] Exhaustive search: processing combinations as iterator")

    # Add timeout protection for constraint checking
    constraint_start = time.time()
    max_constraint_time = 30.0  # 30 second timeout
    
    for i, pick in enumerate(picks):
        # Check timeout every 100 iterations
        if i % 100 == 0 and (time.time() - constraint_start) > max_constraint_time:
            print(f"[TIMING] Constraint checking timeout after {max_constraint_time}s, processed {i}/{len(picks)} combinations")
            break
            
        conf = {comp: svc for comp, svc in zip(selected_components, pick)}
        # Extract workload profile from constraints if provided
        workload_profile = getattr(constraints, 'workload_profile', None)
        cost = calculate_total_cost(conf, workload_profile)
        perf = calculate_performance(conf, metric)
        providers = count_providers(conf)
        # Apply multi-cloud complexity penalty to budget (5% per additional provider)
        complexity_penalty = max(0, (providers - 1) * 0.05) * cost
        adjusted_cost = cost + complexity_penalty
        
        if adjusted_cost <= constraints.maxBudget and perf <= constraints.maxLatency and providers <= constraints.maxProviders and check_dependencies(conf):
            solutions.append(
                Solution(
                    configuration=conf,
                    cost=adjusted_cost,  # Use adjusted cost with complexity penalty
                    latency=perf,
                    providers=providers,
                    providerDistribution=provider_distribution(conf),
                )
            )
            
        # Early termination if we have enough solutions
        if len(solutions) >= 50:  # Limit to 50 feasible solutions for performance
            print(f"[TIMING] Early termination: found {len(solutions)} feasible solutions")
            break
    
    total_time = time.time() - start_time
    print(f"[TIMING] CSP completed: {len(solutions)} feasible solutions in {total_time*1000:.1f}ms")
    return solutions
