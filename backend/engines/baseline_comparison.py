"""
Baseline Comparison Module

Provides helper functions for comparing CMOv4 Pareto optimization
against baseline algorithms.
"""

import time
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import asdict

from models import Constraints, Solution
from services.pricing import get_service_options, get_service_costs, get_service_latency, get_cost_for_service, get_latency_for_service
from engines.pareto import calculate_pareto_frontier
from engines.baselines import (
    baseline_random,
    baseline_greedy_cost,
    baseline_greedy_latency,
    baseline_genetic_algorithm,
    baseline_weighted_sum
)


# Constants
GREEDY_SAMPLE_COUNT = 50
RANDOM_SAMPLE_COUNT = 50
MAX_FRONTIER_RESULTS = 20
DEFAULT_SCORE = 100


def count_unique_providers(configuration: Dict[str, str]) -> int:
    """
    Count unique cloud providers in a service configuration.
    
    Args:
        configuration: Dictionary mapping components to services
                      (e.g., {"database": "AWS RDS", "cache": "Azure Redis"})
    
    Returns:
        Number of unique providers (e.g., 2 for AWS + Azure)
    
    Examples:
        >>> count_unique_providers({"db": "AWS RDS", "cache": "AWS ElastiCache"})
        1
        >>> count_unique_providers({"db": "AWS RDS", "cache": "Azure Redis"})
        2
    """
    if not configuration:
        return 0
    
    providers = {
        service.split()[0] if ' ' in service else service.split('-')[0]
        for service in configuration.values()
    }
    return len(providers)


def load_pareto_frontier_from_data(pareto_data: List[Dict]) -> Tuple[List[Solution], Optional[str]]:
    """
    Load and convert Pareto frontier from dictionary data to Solution objects.
    
    Args:
        pareto_data: List of solution dictionaries from benchmark results
    
    Returns:
        Tuple of (pareto_frontier, error_message)
        - pareto_frontier: List of Solution objects
        - error_message: Error description if loading failed, None otherwise
    
    Example:
        >>> solutions, error = load_pareto_frontier_from_data([{
        ...     'configuration': {'db': 'AWS RDS'},
        ...     'cost': 267.27,
        ...     'latency': 7.88,
        ...     'providers': 1,
        ...     'providerDistribution': {'AWS': 1}
        ... }])
        >>> len(solutions)
        1
    """
    pareto_frontier = []
    
    try:
        for sol_data in pareto_data:
            if isinstance(sol_data, dict):
                # Extract required fields with defaults
                config = sol_data.get('configuration', {})
                cost = float(sol_data.get('cost', 0))
                latency = float(sol_data.get('latency', 0))
                providers = int(sol_data.get('providers', 0))
                provider_dist = sol_data.get('providerDistribution', {})
                
                # Create Solution object
                solution = Solution(
                    configuration=config,
                    cost=cost,  # Keep as float for decimal precision
                    latency=latency,
                    providers=providers,
                    providerDistribution=provider_dist,
                    score=sol_data.get('score'),
                    evaluationLog=sol_data.get('evaluationLog'),
                    constraintProof=sol_data.get('constraintProof'),
                    ruleTrace=sol_data.get('ruleTrace')
                )
                pareto_frontier.append(solution)
            else:
                # Already a Solution object
                pareto_frontier.append(sol_data)
        
        return pareto_frontier, None
        
    except (KeyError, ValueError, TypeError) as e:
        error_msg = f"Failed to load Pareto frontier: {str(e)}"
        return [], error_msg


def generate_pareto_frontier(
    components: List[str],
    constraints: Constraints
) -> Tuple[List[Solution], float]:
    """
    Generate Pareto frontier using sample-based optimization.
    
    Args:
        components: List of component names to include
        constraints: Constraints for optimization (budget, latency, providers)
    
    Returns:
        Tuple of (pareto_frontier, generation_time_ms)
    
    Strategy:
        1. Generate greedy samples (cost/latency weighted)
        2. Generate random samples
        3. Filter valid solutions
        4. Calculate Pareto frontier
    """
    start_time = time.time()
    all_solutions = []
    options = get_service_options()
    costs = get_service_costs()
    latencies = get_service_latency()
    
    def make_solution(config: Dict[str, str]) -> Optional[Solution]:
        """Create a Solution from configuration if it satisfies constraints."""
        cost = sum(get_cost_for_service(service) for service in config.values())
        latency = sum(get_latency_for_service(service) for service in config.values()) / len(config) if config else 0
        
        # Count unique providers
        providers = count_unique_providers(config)
        
        # Calculate provider distribution
        provider_dist = {}
        for service in config.values():
            provider = service.split()[0] if ' ' in service else service.split('-')[0]
            provider_dist[provider] = provider_dist.get(provider, 0) + 1
        
        # Check constraints
        if (cost <= constraints.maxBudget and 
            latency <= constraints.maxLatency and 
            providers <= constraints.maxProviders):
            return Solution(
                configuration=config,
                cost=cost,
                latency=latency,
                providers=providers,
                providerDistribution=provider_dist,
                score=DEFAULT_SCORE
            )
        return None
    
    # Strategy 1: Greedy variations (cost/latency weighted)
    for _ in range(GREEDY_SAMPLE_COUNT):
        config = {}
        for comp in components:
            if comp in options and options[comp]:
                services = options[comp]
                # Weight by inverse of cost + latency
                weights = [1.0 / (get_cost_for_service(s) + get_latency_for_service(s) + 1e-9) for s in services]
                total = sum(weights)
                weights = [w / total for w in weights]
                config[comp] = random.choices(services, weights=weights)[0]
        
        sol = make_solution(config)
        if sol:
            all_solutions.append(sol)
    
    # Strategy 2: Random sampling
    for _ in range(RANDOM_SAMPLE_COUNT):
        config = {
            comp: random.choice(options.get(comp, ['AWS EC2']))
            for comp in components
        }
        sol = make_solution(config)
        if sol:
            all_solutions.append(sol)
    
    # Calculate Pareto frontier
    pareto_frontier = calculate_pareto_frontier(all_solutions, objectives=['cost', 'latency'])
    generation_time = (time.time() - start_time) * 1000
    
    return pareto_frontier, generation_time


def format_baseline_result(result, algorithm_name: str) -> Dict[str, Any]:
    """
    Format baseline algorithm result into consistent dictionary structure.
    
    Args:
        result: BaselineResult object from baseline algorithm
        algorithm_name: Name of the algorithm (for logging)
    
    Returns:
        Dictionary with standardized baseline result fields
    """
    return {
        'success': result.success,
        'cost': result.solution.cost if result.solution else 0,
        'latency': result.solution.latency if result.solution else 0,
        'providers': count_unique_providers(result.solution.configuration) if result.solution else 0,
        'execution_time_ms': result.execution_time_ms,
        'reason': result.reason
    }


def run_baseline_algorithms(constraints: Constraints) -> Dict[str, Dict[str, Any]]:
    """
    Run all 5 baseline algorithms and collect results.
    
    Args:
        constraints: Constraints for optimization
    
    Returns:
        Dictionary mapping algorithm names to their results
        
    Baseline Algorithms:
        - random: Random selection with constraint checking
        - greedy_cost: Always select cheapest service
        - greedy_latency: Always select fastest service
        - genetic_algorithm: Evolutionary optimization
        - weighted_sum: Scalarization approach
    """
    baselines = {}
    
    # 1. Random Selection
    result = baseline_random(constraints)
    baselines['random'] = format_baseline_result(result, 'Random Selection')
    
    # 2. Greedy Cost
    result = baseline_greedy_cost(constraints)
    baselines['greedy_cost'] = format_baseline_result(result, 'Greedy Cost')
    
    # 3. Greedy Latency
    result = baseline_greedy_latency(constraints)
    baselines['greedy_latency'] = format_baseline_result(result, 'Greedy Latency')
    
    # 4. Genetic Algorithm
    result = baseline_genetic_algorithm(constraints)
    baselines['genetic_algorithm'] = format_baseline_result(result, 'Genetic Algorithm')
    
    # 5. Weighted Sum
    result = baseline_weighted_sum(constraints)
    baselines['weighted_sum'] = format_baseline_result(result, 'Weighted Sum')
    
    return baselines


def calculate_comparison_metrics(
    pareto_frontier: List[Solution],
    baselines: Dict[str, Dict[str, Any]],
    cmov4_cost: float,
    cmov4_latency: float
) -> Tuple[Dict[str, int], int, Dict[str, Any]]:
    """
    Calculate comparison metrics between CMOv4 and baseline algorithms.
    
    Args:
        pareto_frontier: CMOv4's Pareto frontier solutions
        baselines: Results from baseline algorithms
        cmov4_cost: Best cost from Pareto frontier
        cmov4_latency: Corresponding latency
    
    Returns:
        Tuple of (wins_per_baseline, total_wins, pareto_metrics)
    """
    # Calculate wins
    wins_per_baseline = {name: 0 for name in baselines.keys()}
    total_wins = 0
    
    for name, baseline in baselines.items():
        if baseline['success']:
            # CMOv4 wins if it dominates baseline
            if cmov4_cost < baseline['cost'] and cmov4_latency < baseline['latency']:
                total_wins += 1
            # Baseline wins if it dominates CMOv4
            elif baseline['cost'] < cmov4_cost and baseline['latency'] < cmov4_latency:
                wins_per_baseline[name] += 1
    
    # Calculate Pareto-specific metrics
    pareto_metrics = {}
    if pareto_frontier and len(pareto_frontier) > 1:
        sorted_pareto = sorted(pareto_frontier, key=lambda s: s.cost)
        
        # Hypervolume (simplified - area under Pareto curve)
        hypervolume = 0
        for i in range(len(sorted_pareto) - 1):
            width = sorted_pareto[i + 1].cost - sorted_pareto[i].cost
            height = sorted_pareto[i].latency
            hypervolume += width * height
        
        # Solution diversity
        costs = [s.cost for s in pareto_frontier]
        latencies = [s.latency for s in pareto_frontier]
        
        pareto_metrics = {
            'hypervolume': round(hypervolume, 2),
            'cost_range': round(max(costs) - min(costs), 2),
            'latency_range': round(max(latencies) - min(latencies), 2),
            'avg_cost': round(sum(costs) / len(costs), 2),
            'avg_latency': round(sum(latencies) / len(latencies), 2)
        }
    
    return wins_per_baseline, total_wins, pareto_metrics


def prepare_comparison_response(
    pareto_frontier: List[Solution],
    baselines: Dict[str, Dict[str, Any]],
    cmov4_time_ms: float,
    cmov4_cost: float,
    cmov4_latency: float,
    cmov4_providers: int,
    scenario: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare the final JSON response for baseline comparison endpoint.
    
    Args:
        pareto_frontier: CMOv4's Pareto frontier
        baselines: Baseline algorithm results
        cmov4_time_ms: CMOv4 execution time
        cmov4_cost: Best cost from Pareto frontier
        cmov4_latency: Corresponding latency
        cmov4_providers: Number of providers in best solution
        scenario: Input scenario parameters
    
    Returns:
        Complete response dictionary
    """
    pareto_count = len(pareto_frontier)
    cmov4_success = pareto_count > 0
    
    # Calculate comparison metrics
    wins_per_baseline, total_wins, pareto_metrics = calculate_comparison_metrics(
        pareto_frontier, baselines, cmov4_cost, cmov4_latency
    )
    
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
                    'providers': count_unique_providers(s.configuration)
                }
                for s in pareto_frontier[:MAX_FRONTIER_RESULTS]
            ] if pareto_frontier else []
        },
        'baselines': baselines,
        'comparison': {
            'total_wins': total_wins,
            'wins_per_baseline': wins_per_baseline,
            'baseline_success_rate': sum(1 for b in baselines.values() if b['success']) / len(baselines),
            'cmov4_advantage': {
                'cost_vs_best_baseline': round(
                    cmov4_cost - min([b['cost'] for b in baselines.values() if b['success']], default=cmov4_cost),
                    2
                ) if cmov4_success else None,
                'latency_vs_best_baseline': round(
                    cmov4_latency - min([b['latency'] for b in baselines.values() if b['success']], default=cmov4_latency),
                    2
                ) if cmov4_success else None,
                'speed_multiplier': round(
                    max([b['execution_time_ms'] for b in baselines.values()]) / cmov4_time_ms,
                    2
                ) if cmov4_time_ms > 0 else None
            }
        },
        'scenario': {
            'components': scenario.get('components', []),
            'constraints': {
                'maxBudget': scenario.get('maxBudget'),
                'maxLatency': scenario.get('maxLatency'),
                'maxProviders': scenario.get('maxProviders')
            }
        }
    }
    
    return response
