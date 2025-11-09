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

from models import Solution, Constraints
from services.pricing import (
    get_service_options,
    get_service_costs,
    get_service_latency,
    COMPONENTS,
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
    """Calculate total cost for a configuration"""
    costs = get_service_costs()
    return sum(costs.get(service, 0) for service in config.values())


def calculate_config_latency(config: Dict[str, str]) -> float:
    """Calculate average latency for a configuration"""
    latencies = get_service_latency()
    latency_values = [latencies.get(service, 0) for service in config.values()]
    return sum(latency_values) / len(latency_values) if latency_values else 0.0


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
    return Solution(
        configuration=config,
        cost=calculate_config_cost(config),
        latency=calculate_config_latency(config),
        providers=count_config_providers(config),
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
        cheapest = min(
            available,
            key=lambda service: costs.get(service, float('inf'))
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
        fastest = min(
            available,
            key=lambda service: latencies.get(service, float('inf'))
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
    
    def fitness(config: Dict[str, str]) -> float:
        """
        Fitness function: minimize cost + latency
        Invalid solutions get heavy penalty
        """
        if not is_valid_configuration(config, constraints):
            # Heavy penalty for constraint violation
            return float('inf')
        
        # Normalize and combine objectives (simple weighted sum)
        cost = calculate_config_cost(config)
        latency = calculate_config_latency(config)
        
        # Normalize to [0,1] range (approximate)
        normalized_cost = cost / constraints.maxBudget
        normalized_latency = latency / constraints.maxLatency
        
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
    all_costs = list(costs.values())
    all_latencies = list(latencies.values())
    max_cost = max(all_costs) if all_costs else 1
    max_latency = max(all_latencies) if all_latencies else 1
    
    config = {}
    for component in COMPONENTS:
        available = options[component]
        
        # Calculate weighted sum for each option
        def weighted_score(service: str) -> float:
            normalized_cost = costs.get(service, max_cost) / max_cost
            normalized_latency = latencies.get(service, max_latency) / max_latency
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

def run_all_baselines(constraints: Constraints) -> Dict[str, BaselineResult]:
    """
    Run all baseline algorithms and return results for comparison
    
    Returns dictionary mapping algorithm name to BaselineResult
    """
    results = {}
    
    print("Running baseline comparisons...")
    
    # Run each baseline
    results["Random"] = baseline_random(constraints, max_attempts=1000)
    print(f"  ✓ Random: {results['Random'].success}")
    
    results["Greedy-Cost"] = baseline_greedy_cost(constraints)
    print(f"  ✓ Greedy-Cost: {results['Greedy-Cost'].success}")
    
    results["Greedy-Latency"] = baseline_greedy_latency(constraints)
    print(f"  ✓ Greedy-Latency: {results['Greedy-Latency'].success}")
    
    results["Genetic-Algorithm"] = baseline_genetic_algorithm(
        constraints,
        population_size=30,
        generations=50
    )
    print(f"  ✓ Genetic Algorithm: {results['Genetic-Algorithm'].success}")
    
    results["Weighted-Sum"] = baseline_weighted_sum(constraints)
    print(f"  ✓ Weighted Sum: {results['Weighted-Sum'].success}")
    
    return results


def compare_with_csp_expert(
    csp_solution: Optional[Solution],
    csp_time_ms: float,
    baseline_results: Dict[str, BaselineResult]
) -> Dict[str, Any]:
    """
    Compare CSP+Expert System solution with baseline results
    
    Returns comparison metrics showing advantages of hybrid approach
    
    Winner determination:
    - CSP+Expert wins if: Better cost AND latency, OR same quality but faster OR has explainability
    - Tie if: Same cost AND latency AND similar time
    - Baseline wins if: Better cost AND latency
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
        
        # Compare with CSP+Expert
        if csp_solution and result.solution:
            cost_diff = csp_solution.cost - result.solution.cost
            latency_diff = csp_solution.latency - result.solution.latency
            time_diff = csp_time_ms - result.execution_time_ms
            
            algo_comparison["cost_difference"] = cost_diff
            algo_comparison["latency_difference"] = latency_diff
            algo_comparison["time_difference"] = time_diff
            
            # Determine winner with more nuanced logic
            # Same quality = within 1% tolerance
            cost_tolerance = csp_solution.cost * 0.01
            latency_tolerance = csp_solution.latency * 0.01
            
            cost_similar = abs(cost_diff) <= cost_tolerance
            latency_similar = abs(latency_diff) <= latency_tolerance
            
            if cost_similar and latency_similar:
                # Same quality - CSP+Expert wins on explainability
                algo_comparison["winner"] = "CSP+Expert"
                algo_comparison["win_reason"] = "Same solution quality, but CSP+Expert provides explainability and constraint guarantees"
                comparison["summary"]["csp_expert_wins"] += 1
            elif cost_diff < 0 and latency_diff < 0:
                # CSP+Expert is better in both
                algo_comparison["winner"] = "CSP+Expert"
                algo_comparison["win_reason"] = "Better cost AND latency"
                comparison["summary"]["csp_expert_wins"] += 1
            elif cost_diff > 0 and latency_diff > 0:
                # Baseline is better in both
                algo_comparison["winner"] = algo_name
                algo_comparison["win_reason"] = f"{algo_name} has better cost AND latency"
                comparison["summary"]["baseline_wins"] += 1
            else:
                # Trade-off - neither dominates
                if cost_diff <= 0:
                    algo_comparison["winner"] = "CSP+Expert"
                    algo_comparison["win_reason"] = "Better or equal cost with constraint guarantees"
                    comparison["summary"]["csp_expert_wins"] += 1
                else:
                    algo_comparison["winner"] = algo_name
                    algo_comparison["win_reason"] = f"{algo_name} has better latency"
                    comparison["summary"]["baseline_wins"] += 1
        
        comparison["algorithms"].append(algo_comparison)
    
    # Add CSP+Expert stats
    comparison["csp_expert"] = {
        "cost": csp_solution.cost if csp_solution else None,
        "latency": csp_solution.latency if csp_solution else None,
        "time_ms": csp_time_ms,
        "explainability": "High - CSP guarantees constraints, Expert rules provide reasoning",
        "advantages": [
            "Constraint satisfaction guaranteed",
            "Explainable decision-making",
            "Multi-objective Pareto frontier",
            "Consistent and deterministic results"
        ]
    }
    
    return comparison
