"""
Baseline Comparison Algorithms for Cloud Migration Optimization

This module implements 5 baseline algorithms to compare against the CSP + Expert System approach:
1. Random Selection - Randomly picks services for each component
2. Greedy-Cost - Always selects the cheapest available service
3. Greedy-Latency - Always selects the fastest (lowest latency) service
4. Genetic Algorithm - Evolutionary optimization approach
5. Weighted Sum - Scalarization of multi-objective problem

Each algorithm aims to find valid cloud configurations but uses different strategies.
These baselines are critical for academic evaluation and demonstrating the superiority
of the hybrid CSP + Expert System approach.
"""

from __future__ import annotations

import random
import time
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

from backend.models import Solution, Constraints
from backend.services.pricing import (
    get_service_options,
    get_service_costs,
    get_service_latency,
    COMPONENTS,
    _resolve_service_key,
    get_cost_for_service,
    get_latency_for_service,
)


@dataclass
class BaselineResult:
    """Result from a baseline algorithm"""
    algorithm: str
    solution: Optional[Solution]
    execution_time_ms: float
    iterations: int
    success: bool
    reason: str = ""


def calculate_config_cost(config: Dict[str, str]) -> float:
    """
    Calculate total cost for a configuration.
    
    IMPORTANT: Includes data transfer costs for multi-cloud configurations
    to ensure fair comparison with CMOv4 (which accounts for these costs).
    Academic rigor requires baselines to include the same cost components.
    """
    from backend.engines.constraints import calculate_data_transfer_cost
    
    # Base service costs
    base_cost = sum(get_cost_for_service(service) for service in config.values())
    
    # Add multi-cloud data transfer costs (100GB/month typical workload)
    transfer_cost = calculate_data_transfer_cost(config, 100)
    
    total_cost = base_cost + transfer_cost
    
    # Debug logging
    if transfer_cost > 0:
        print(f"[Baseline] Cost calculation: base=${base_cost:.2f} + transfer=${transfer_cost:.2f} = ${total_cost:.2f}")
    
    return total_cost


def calculate_config_latency(config: Dict[str, str]) -> float:
    """
    Calculate average latency for a configuration.
    
    IMPORTANT: Includes cross-cloud latency penalties for multi-cloud configurations
    to ensure fair comparison with CMOv4 (which accounts for these penalties).
    Academic rigor requires baselines to include the same latency components.
    """
    from backend.engines.constraints import calculate_cross_cloud_penalty
    
    # Base average latency
    latency_values = [get_latency_for_service(service) for service in config.values()]
    base_latency = sum(latency_values) / len(latency_values) if latency_values else 0.0
    
    # Add cross-cloud communication penalty
    cross_cloud_penalty = calculate_cross_cloud_penalty(config)
    
    return base_latency + cross_cloud_penalty


def count_config_providers(config: Dict[str, str]) -> int:
    """Count unique providers in a configuration"""
    providers = {service.split(" ")[0] for service in config.values()}
    return len(providers)


def get_provider_distribution(config: Dict[str, str]) -> Dict[str, int]:
    """Get provider distribution for a configuration"""
    dist: Dict[str, int] = {}
    for service in config.values():
        provider = service.split(" ")[0]
        dist[provider] = dist.get(provider, 0) + 1
    return dist


def is_valid_configuration(config: Dict[str, str], constraints: Constraints) -> bool:
    """Check if a configuration satisfies constraints"""
    cost = calculate_config_cost(config)
    latency = calculate_config_latency(config)
    providers = count_config_providers(config)
    
    return (
        cost <= constraints.maxBudget and
        latency <= constraints.maxLatency and
        providers <= constraints.maxProviders
    )


def create_solution_from_config(config: Dict[str, str]) -> Solution:
    """Create a Solution object from a configuration"""
    cost = calculate_config_cost(config)
    latency = calculate_config_latency(config)
    providers = count_config_providers(config)
    
    # Debug logging
    print(f"[create_solution_from_config] cost=${cost:.2f}, latency={latency:.2f}ms, providers={providers}")
    
    return Solution(
        configuration=config,
        cost=cost,
        latency=latency,
        providers=providers,
        providerDistribution=get_provider_distribution(config),
        score=None,
        evaluationLog=None,
    )


# ============================================================================
# BASELINE 1: Random Selection
# ============================================================================

def baseline_random(constraints: Constraints, max_attempts: int = 1000) -> BaselineResult:
    """
    Random Selection Baseline
    
    Strategy: Randomly selects services for each component until a valid
    configuration is found or max attempts is reached.
    
    This represents the worst-case scenario - no intelligence, just random guessing.
    Expected to perform poorly but establishes a lower bound for comparison.
    """
    start_time = time.time()
    options = get_service_options()
    
    for attempt in range(max_attempts):
        # Randomly select one service for each component
        config = {
            component: random.choice(options[component])
            for component in COMPONENTS
        }
        
        if is_valid_configuration(config, constraints):
            execution_time = (time.time() - start_time) * 1000
            return BaselineResult(
                algorithm="Random Selection",
                solution=create_solution_from_config(config),
                execution_time_ms=execution_time,
                iterations=attempt + 1,
                success=True,
                reason=f"Found valid solution after {attempt + 1} random attempts"
            )
    
    execution_time = (time.time() - start_time) * 1000
    return BaselineResult(
        algorithm="Random Selection",
        solution=None,
        execution_time_ms=execution_time,
        iterations=max_attempts,
        success=False,
        reason=f"No valid solution found after {max_attempts} random attempts"
    )


# ============================================================================
# BASELINE 2: Greedy-Cost
# ============================================================================

def baseline_greedy_cost(constraints: Constraints) -> BaselineResult:
    """
    Greedy-Cost Baseline
    
    Strategy: Always selects the cheapest available service for each component.
    
    This represents a pure cost-minimization approach without considering
    other factors. Should produce low-cost solutions but may fail on
    latency or provider constraints.
    """
    start_time = time.time()
    options = get_service_options()
    costs = get_service_costs()
    
    config = {}
    for component in COMPONENTS:
        # Find the cheapest service for this component
        available = options[component]
        # Use safe lookup to tolerate alias naming
        from backend.services.pricing import get_cost_for_service
        cheapest = min(
            available,
            key=lambda service: get_cost_for_service(service) or float('inf')
        )
        config[component] = cheapest
    
    execution_time = (time.time() - start_time) * 1000
    
    if is_valid_configuration(config, constraints):
        return BaselineResult(
            algorithm="Greedy-Cost",
            solution=create_solution_from_config(config),
            execution_time_ms=execution_time,
            iterations=1,
            success=True,
            reason="Greedy cost minimization successful"
        )
    else:
        return BaselineResult(
            algorithm="Greedy-Cost",
            solution=create_solution_from_config(config),  # Return it anyway for comparison
            execution_time_ms=execution_time,
            iterations=1,
            success=False,
            reason="Greedy solution violates constraints"
        )


# ============================================================================
# BASELINE 3: Greedy-Latency
# ============================================================================

def baseline_greedy_latency(constraints: Constraints) -> BaselineResult:
    """
    Greedy-Latency Baseline
    
    Strategy: Always selects the fastest (lowest latency) service for each component.
    
    This represents a pure performance-maximization approach. Should produce
    fast solutions but may fail on cost or provider constraints.
    """
    start_time = time.time()
    options = get_service_options()
    latencies = get_service_latency()
    
    config = {}
    for component in COMPONENTS:
        # Find the fastest service for this component
        available = options[component]
        from backend.services.pricing import get_latency_for_service
        fastest = min(
            available,
            key=lambda service: get_latency_for_service(service) or float('inf')
        )
        config[component] = fastest
    
    execution_time = (time.time() - start_time) * 1000
    
    if is_valid_configuration(config, constraints):
        return BaselineResult(
            algorithm="Greedy-Latency",
            solution=create_solution_from_config(config),
            execution_time_ms=execution_time,
            iterations=1,
            success=True,
            reason="Greedy latency minimization successful"
        )
    else:
        return BaselineResult(
            algorithm="Greedy-Latency",
            solution=create_solution_from_config(config),  # Return it anyway for comparison
            execution_time_ms=execution_time,
            iterations=1,
            success=False,
            reason="Greedy solution violates constraints"
        )


# ============================================================================
# BASELINE 4: Genetic Algorithm
# ============================================================================

def baseline_genetic_algorithm(
    constraints: Constraints,
    population_size: int = 50,
    generations: int = 100,
    mutation_rate: float = 0.1,
    crossover_rate: float = 0.7
) -> BaselineResult:
    """
    Genetic Algorithm Baseline
    
    Strategy: Evolutionary optimization using selection, crossover, and mutation.
    
    Represents a meta-heuristic approach commonly used in cloud optimization.
    Should find good solutions but lacks explainability and may be slow.
    
    Algorithm:
    1. Initialize random population
    2. Evaluate fitness (lower cost + latency is better)
    3. Select parents using tournament selection
    4. Create offspring through crossover and mutation
    5. Replace population with best individuals
    6. Repeat for N generations
    """
    start_time = time.time()
    options = get_service_options()
    
    def create_random_individual() -> Dict[str, str]:
        """Create a random configuration"""
        return {
            component: random.choice(options[component])
            for component in COMPONENTS
        }
    
    # Pre-calculate costs and latencies once
    costs = get_service_costs()
    latencies = get_service_latency()
    
    def fitness(config: Dict[str, str]) -> float:
        """
        Fitness function: minimize cost + latency
        Invalid solutions get heavy penalty
        
        IMPORTANT: Uses calculate_config_cost() and calculate_config_latency()
        to include multi-cloud penalties for fair comparison with CMOv4.
        """
        # Use proper calculation functions that include multi-cloud penalties
        total_cost = calculate_config_cost(config)
        total_latency = calculate_config_latency(config)
        providers = len({service.split(" ")[0] for service in config.values()})
        
        # Check constraints quickly
        if (total_cost > constraints.maxBudget or 
            total_latency > constraints.maxLatency or 
            providers > constraints.maxProviders):
            return float('inf')
        
        # Normalize and combine objectives
        normalized_cost = total_cost / constraints.maxBudget
        normalized_latency = total_latency / constraints.maxLatency
        
        return normalized_cost + normalized_latency
    
    def tournament_selection(population: List[Dict[str, str]], k: int = 3) -> Dict[str, str]:
        """Select best individual from k random individuals"""
        tournament = random.sample(population, k)
        return min(tournament, key=fitness)
    
    def crossover(parent1: Dict[str, str], parent2: Dict[str, str]) -> Dict[str, str]:
        """Single-point crossover"""
        child = {}
        crossover_point = random.randint(0, len(COMPONENTS) - 1)
        for i, component in enumerate(COMPONENTS):
            child[component] = parent1[component] if i < crossover_point else parent2[component]
        return child
    
    def mutate(config: Dict[str, str]) -> Dict[str, str]:
        """Random mutation - change one component"""
        mutated = config.copy()
        component = random.choice(COMPONENTS)
        mutated[component] = random.choice(options[component])
        return mutated
    
    # Initialize population
    population = [create_random_individual() for _ in range(population_size)]
    
    best_solution = None
    best_fitness = float('inf')
    
    for generation in range(generations):
        # Progress logging every 10 generations
        if generation % 10 == 0:
            print(f"    GA Generation {generation}/{generations}...")
        
        # Evaluate and track best
        for individual in population:
            fit = fitness(individual)
            if fit < best_fitness:
                best_fitness = fit
                best_solution = individual.copy()
        
        # Create next generation
        next_generation = []
        
        # Elitism: keep best 10%
        elite_count = max(1, population_size // 10)
        sorted_pop = sorted(population, key=fitness)
        next_generation.extend(sorted_pop[:elite_count])
        
        # Generate offspring
        while len(next_generation) < population_size:
            # Selection
            parent1 = tournament_selection(population)
            parent2 = tournament_selection(population)
            
            # Crossover
            if random.random() < crossover_rate:
                child = crossover(parent1, parent2)
            else:
                child = parent1.copy()
            
            # Mutation
            if random.random() < mutation_rate:
                child = mutate(child)
            
            next_generation.append(child)
        
        population = next_generation
    
    execution_time = (time.time() - start_time) * 1000
    
    if best_solution and is_valid_configuration(best_solution, constraints):
        return BaselineResult(
            algorithm="Genetic Algorithm",
            solution=create_solution_from_config(best_solution),
            execution_time_ms=execution_time,
            iterations=generations * population_size,
            success=True,
            reason=f"GA converged after {generations} generations"
        )
    else:
        return BaselineResult(
            algorithm="Genetic Algorithm",
            solution=create_solution_from_config(best_solution) if best_solution else None,
            execution_time_ms=execution_time,
            iterations=generations * population_size,
            success=False,
            reason="GA failed to find valid solution"
        )


# ============================================================================
# BASELINE 5: Weighted Sum
# ============================================================================

def baseline_weighted_sum(
    constraints: Constraints,
    cost_weight: float = 0.5,
    latency_weight: float = 0.5
) -> BaselineResult:
    """
    Weighted Sum Baseline
    
    Strategy: Scalarization of multi-objective problem using weighted sum.
    For each component, select service that minimizes: w1*cost + w2*latency
    
    This is a common approach in multi-objective optimization but requires
    careful weight tuning and may miss solutions on non-convex Pareto fronts.
    """
    start_time = time.time()
    options = get_service_options()
    costs = get_service_costs()
    latencies = get_service_latency()
    
    # Normalize weights
    total_weight = cost_weight + latency_weight
    cost_weight = cost_weight / total_weight
    latency_weight = latency_weight / total_weight
    
    # Estimate normalization factors (max values)
    # Use safe getters for normalization
    from backend.services.pricing import get_cost_for_service, get_latency_for_service
    all_costs = [get_cost_for_service(s) for s in costs.keys()]
    all_latencies = [get_latency_for_service(s) for s in latencies.keys()]
    max_cost = max(all_costs) if all_costs else 1
    max_latency = max(all_latencies) if all_latencies else 1
    
    config = {}
    for component in COMPONENTS:
        available = options[component]
        
        # Calculate weighted sum for each option
        def weighted_score(service: str) -> float:
            normalized_cost = get_cost_for_service(service) / max_cost
            normalized_latency = get_latency_for_service(service) / max_latency
            return cost_weight * normalized_cost + latency_weight * normalized_latency
        
        # Select service with minimum weighted sum
        best_service = min(available, key=weighted_score)
        config[component] = best_service
    
    execution_time = (time.time() - start_time) * 1000
    
    if is_valid_configuration(config, constraints):
        return BaselineResult(
            algorithm="Weighted Sum",
            solution=create_solution_from_config(config),
            execution_time_ms=execution_time,
            iterations=1,
            success=True,
            reason=f"Weighted sum (cost={cost_weight:.2f}, latency={latency_weight:.2f}) successful"
        )
    else:
        return BaselineResult(
            algorithm="Weighted Sum",
            solution=create_solution_from_config(config),
            execution_time_ms=execution_time,
            iterations=1,
            success=False,
            reason="Weighted sum solution violates constraints"
        )


# ============================================================================
# Comparison Function
# ============================================================================

def run_all_baselines(constraints: Constraints, fast: bool = False) -> Dict[str, BaselineResult]:
    """
    Run all baseline algorithms and return results for comparison.

    Args:
        constraints: Hard constraints (budget, latency, providers).
        fast: When True, uses reduced GA parameters suitable for quick smoke
              tests (pop=20, gen=30).  Set fast=False (the default) for all
              academic / publication runs to ensure the GA has the same 5,000-
              evaluation budget (pop=50 × gen=100) as reported in the paper.
              Never use fast=True in multi-run or statistical-test pipelines.

    Returns dictionary mapping algorithm name to BaselineResult.
    """
    import time

    # GA parameters — consistent with the paper's method section
    ga_pop  = 20  if fast else 50
    ga_gen  = 30  if fast else 100
    rand_attempts = 100 if fast else 1000

    # Pre-warm the cache to avoid API calls during baselines
    print("Pre-warming pricing cache...")
    from backend.services.pricing import service_cache
    service_cache.get_service_data()  # This will use cached data if available
    print(f"Cache warmed. Running baseline comparisons (fast={fast})...")

    results = {}
    timings = {}

    # Run baselines sequentially with timeout to avoid ProcessPoolExecutor issues
    baseline_functions = [
        (baseline_random,             (constraints, rand_attempts), "Random"),
        (baseline_greedy_cost,        (constraints,),               "Greedy-Cost"),
        (baseline_greedy_latency,     (constraints,),               "Greedy-Latency"),
        (baseline_genetic_algorithm,  (constraints, ga_pop, ga_gen),"Genetic-Algorithm"),
        (baseline_weighted_sum,       (constraints,),               "Weighted-Sum"),
    ]
    
    for fn, args, name in baseline_functions:
        start_time = time.time()
        try:
            print(f"  Running {name}...")
            result = fn(*args)
            elapsed = time.time() - start_time
            timings[name] = elapsed
            results[name] = result
            print(f"  ✓ {name}: {getattr(result, 'success', None)} (time: {elapsed:.2f}s)")
        except Exception as exc:
            elapsed = time.time() - start_time
            timings[name] = elapsed
            print(f"  ✗ {name} failed after {elapsed:.2f}s: {exc}")
            results[name] = None
    
    print("Baseline timings:")
    for name, t in timings.items():
        print(f"    {name}: {t:.2f}s")
    
    return results


def compare_with_csp_expert(
    csp_solution: Optional[Solution],
    csp_time_ms: float,
    baseline_results: Dict[str, BaselineResult]
) -> Dict[str, Any]:
    """
    Compare CSP+Expert System solution with baseline results using
    strict Pareto dominance as the win criterion.

    Winner determination (Pareto-correct):
      - CSP+Expert WINS   : csp_solution dominates baseline (better in both
                            cost AND latency simultaneously).
      - TIE               : Neither solution dominates the other (trade-off).
                            Note: CSP+Expert still provides constraint
                            guarantees and full explainability for any tie.
      - Baseline WINS     : baseline solution dominates csp_solution (better
                            in both cost AND latency).

    This replaces the previous logic that awarded a win whenever CMO was
    cheaper, regardless of latency — which does not reflect Pareto dominance.
    """
    comparison = {
        "algorithms": [],
        "summary": {
            "csp_expert_wins": 0,
            "csp_expert_ties": 0,
            "baseline_wins": 0,
        },
        "advantages": {
            "explainability": "CSP+Expert provides full constraint reasoning and rule-based scoring explanations",
            "guarantee": "CSP guarantees all solutions satisfy hard constraints",
            "multi_objective": "Pareto frontier provides trade-off analysis, not just single solution"
        }
    }

    for algo_name, result in baseline_results.items():
        algo_comparison = {
            "name": algo_name,
            "success": result.success,
            "cost": result.solution.cost if result.solution else None,
            "latency": result.solution.latency if result.solution else None,
            "time_ms": result.execution_time_ms,
            "iterations": result.iterations,
        }

        if csp_solution and result.solution:
            cost_diff    = csp_solution.cost    - result.solution.cost
            latency_diff = csp_solution.latency - result.solution.latency
            time_diff    = csp_time_ms          - result.execution_time_ms

            algo_comparison["cost_difference"]    = cost_diff
            algo_comparison["latency_difference"] = latency_diff
            algo_comparison["time_difference"]    = time_diff

            # Strict Pareto dominance (1% tolerance for floating-point noise)
            tol_c = csp_solution.cost    * 0.01
            tol_l = csp_solution.latency * 0.01

            csp_dominates      = cost_diff <= tol_c  and latency_diff <= tol_l \
                                  and (cost_diff < -tol_c or latency_diff < -tol_l)
            baseline_dominates = cost_diff >= -tol_c and latency_diff >= -tol_l \
                                  and (cost_diff > tol_c or latency_diff > tol_l)

            if csp_dominates:
                algo_comparison["winner"]   = "CSP+Expert"
                algo_comparison["win_reason"] = "Pareto-dominates baseline (better cost AND latency)"
                comparison["summary"]["csp_expert_wins"] += 1
            elif baseline_dominates:
                algo_comparison["winner"]   = algo_name
                algo_comparison["win_reason"] = f"{algo_name} Pareto-dominates CSP+Expert"
                comparison["summary"]["baseline_wins"] += 1
            else:
                # Non-dominated trade-off
                algo_comparison["winner"]   = "Tie"
                algo_comparison["win_reason"] = (
                    "Non-dominated trade-off; CSP+Expert retains advantage via "
                    "constraint guarantees and full explainability"
                )
                comparison["summary"]["csp_expert_ties"] += 1

        comparison["algorithms"].append(algo_comparison)

    comparison["csp_expert"] = {
        "cost":     csp_solution.cost    if csp_solution else None,
        "latency":  csp_solution.latency if csp_solution else None,
        "time_ms":  csp_time_ms,
        "explainability": "High — CSP guarantees constraints, Expert rules provide full reasoning trace",
        "advantages": [
            "Hard constraint satisfaction guaranteed",
            "Explainable decision-making (constraint proof + rule trace)",
            "Multi-objective Pareto frontier (not a single scalarised point)",
            "Deterministic and reproducible results"
        ]
    }

    return comparison
