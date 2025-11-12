
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
from backend.config import CSP_CONFIG, SERVICE_DEPENDENCIES



# Calculate the total monthly cost for a given configuration.
# Each service's cost is fetched from pricing; sum all selected services.
def calculate_total_cost(config: Dict[str, str]) -> float:
    costs = get_service_costs()
    return sum(costs.get(s, 0) for s in config.values())



# Calculate performance metric for a configuration.
# Supported metrics:
#   - avg_latency: mean latency across all services
#   - tail_latency: 95th percentile latency (demo: sorted, index)
#   - throughput: inverse of mean latency (demo: 1000 / avg)
def calculate_performance(config: Dict[str, str], metric: str = "avg_latency") -> float:
    latencies_map = get_service_latency()
    latencies = [latencies_map.get(s, 0) for s in config.values()]
    if not latencies:
        return 0.0
    if metric == "avg_latency":
        return sum(latencies) / len(latencies)
    if metric == "tail_latency":
        # 95th percentile (approximate)
        sorted_latencies = sorted(latencies)
        return sorted_latencies[int(0.95 * len(sorted_latencies))] if sorted_latencies else 0.0
    if metric == "throughput":
        # Demo: throughput = 1000 / avg_latency
        avg = sum(latencies) / len(latencies)
        return 1000 / avg if avg > 0 else 0.0
    return sum(latencies) / len(latencies)



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
    solutions: List[Solution] = []
    service_options = get_service_options()
    metric = getattr(constraints, "performanceMetric", "avg_latency")

    # Use selected_components if provided, else default to all COMPONENTS
    selected_components = constraints.selected_components if constraints.selected_components else COMPONENTS

    strategy = CSP_CONFIG.get("search_strategy", "exhaustive")
    picks = itertools.product(*(service_options[c] for c in selected_components))
    if strategy == "random_sample":
        import random
        picks = random.sample(list(picks), min(CSP_CONFIG.get("sample_size", 1000), len(list(itertools.product(*(service_options[c] for c in selected_components))))))
    elif strategy == "heuristic":
        import random
        costs = get_service_costs()
        latencies = get_service_latency()

        def get_sorted_options(component, sort_by='cost'):
            options = service_options[component]
            if sort_by == 'cost':
                return sorted(options, key=lambda x: costs.get(x, float('inf')))
            elif sort_by == 'latency':
                return sorted(options, key=lambda x: latencies.get(x, float('inf')))
            return options

        heuristic_picks = []

        # Strategy 1: Pure cheapest (cost-optimized)
        heuristic_picks.append([get_sorted_options(c, 'cost')[0] for c in selected_components])

        # Strategy 2: Pure fastest (performance-optimized)
        heuristic_picks.append([get_sorted_options(c, 'latency')[0] for c in selected_components])

        # Strategy 3-5: Balanced - pick from top 2 options for each component (diverse combinations)
        for _ in range(3):
            pick = []
            for c in selected_components:
                cost_options = get_sorted_options(c, 'cost')[:2]
                latency_options = get_sorted_options(c, 'latency')[:2]
                all_top = list(set(cost_options + latency_options))
                pick.append(random.choice(all_top) if all_top else service_options[c][0])
            heuristic_picks.append(pick)

        # Strategy 6-10: Single-provider solutions (AWS, Azure, GCP)
        for provider in ['AWS', 'Azure', 'GCP']:
            pick = []
            for c in selected_components:
                provider_options = [opt for opt in service_options[c] if opt.startswith(provider)]
                if provider_options:
                    pick.append(min(provider_options, key=lambda x: costs.get(x, float('inf'))))
                else:
                    pick.append(get_sorted_options(c, 'cost')[0])
            heuristic_picks.append(pick)

        # Strategy 11-15: Random sampling from top 3 options per component
        for _ in range(5):
            pick = []
            for c in selected_components:
                top_options = get_sorted_options(c, 'cost')[:3]
                pick.append(random.choice(top_options) if top_options else service_options[c][0])
            heuristic_picks.append(pick)

        # Strategy 16-50: Fully random sampling to ensure we find feasible solutions
        for _ in range(35):
            pick = []
            for c in selected_components:
                all_options = service_options[c]
                pick.append(random.choice(all_options))
            heuristic_picks.append(pick)

        picks = heuristic_picks
    elif strategy == "ml":
        picks = list(picks)[:CSP_CONFIG.get("sample_size", 1000)]

    for pick in picks:
        conf = {comp: svc for comp, svc in zip(selected_components, pick)}
        cost = calculate_total_cost(conf)
        perf = calculate_performance(conf, metric)
        providers = count_providers(conf)
        if cost <= constraints.maxBudget and perf <= constraints.maxLatency and providers <= constraints.maxProviders and check_dependencies(conf):
            solutions.append(
                Solution(
                    configuration=conf,
                    cost=cost,
                    latency=perf,
                    providers=providers,
                    providerDistribution=provider_distribution(conf),
                )
            )
    return solutions
