"""
Pareto Multi-Objective Optimization Module

This module implements Pareto frontier calculation for cloud migration optimization.
Unlike single-objective optimization, it finds all non-dominated solutions, allowing
users to make informed trade-offs between conflicting objectives.

Key Concepts:
- Pareto Dominance: Solution A dominates B if A is better in all objectives
- Pareto Frontier: Set of all non-dominated solutions
- Trade-off Analysis: Visualize cost vs performance vs provider diversity
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from backend.models import Solution


def dominates(sol_a: Solution, sol_b: Solution, objectives: List[str] = None) -> bool:
    """
    Check if solution A dominates solution B.
    
    A dominates B if:
    - A is better than or equal to B in ALL objectives
    - A is strictly better than B in AT LEAST ONE objective
    
    For minimization objectives (cost, latency):
    - "Better" means smaller value
    
    Args:
        sol_a: First solution
        sol_b: Second solution
        objectives: List of objective names to compare (default: ['cost', 'latency'])
    
    Returns:
        True if sol_a dominates sol_b, False otherwise
    """
    if objectives is None:
        objectives = ['cost', 'latency']
    
    better_or_equal_count = 0
    strictly_better_count = 0
    
    for obj in objectives:
        val_a = getattr(sol_a, obj, 0)
        val_b = getattr(sol_b, obj, 0)
        
        if val_a <= val_b:
            better_or_equal_count += 1
            if val_a < val_b:
                strictly_better_count += 1
        else:
            # A is worse in this objective, cannot dominate
            return False
    
    # A dominates B if better/equal in all AND strictly better in at least one
    return better_or_equal_count == len(objectives) and strictly_better_count > 0


def calculate_pareto_frontier(solutions: List[Solution], objectives: List[str] = None) -> List[Solution]:
    """
    Calculate the Pareto frontier from a set of solutions.
    
    The Pareto frontier contains all non-dominated solutions - solutions that
    are not strictly worse than any other solution in all objectives.
    
    Args:
        solutions: List of all feasible solutions
        objectives: Objectives to optimize (default: ['cost', 'latency'])
    
    Returns:
        List of non-dominated solutions (Pareto frontier)
    """
    if not solutions:
        return []
    
    if objectives is None:
        objectives = ['cost', 'latency']
    
    pareto_solutions = []
    
    for candidate in solutions:
        is_dominated = False
        
        # Check if any other solution dominates this candidate
        for other in solutions:
            if candidate != other and dominates(other, candidate, objectives):
                is_dominated = True
                break
        
        # If not dominated by any solution, it's on the Pareto frontier
        if not is_dominated:
            pareto_solutions.append(candidate)
    
    return pareto_solutions


def calculate_pareto_rank(solutions: List[Solution], objectives: List[str] = None) -> Dict[int, int]:
    """
    Calculate Pareto rank for each solution.
    
    Rank 1 = Pareto frontier (non-dominated)
    Rank 2 = Dominated only by rank 1 solutions
    Rank 3 = Dominated only by rank 1 and 2 solutions
    etc.
    
    This creates layers of the Pareto frontier.
    
    Args:
        solutions: List of all solutions
        objectives: Objectives to optimize
    
    Returns:
        Dictionary mapping solution index to its Pareto rank
    """
    if objectives is None:
        objectives = ['cost', 'latency']
    
    remaining = solutions.copy()
    ranks = {}
    current_rank = 1
    
    while remaining:
        # Find Pareto frontier in remaining solutions
        frontier = calculate_pareto_frontier(remaining, objectives)
        
        # Assign current rank to frontier solutions
        for sol in frontier:
            idx = solutions.index(sol)
            ranks[idx] = current_rank
        
        # Remove frontier from remaining
        remaining = [s for s in remaining if s not in frontier]
        current_rank += 1
    
    return ranks


def calculate_hypervolume(pareto_solutions: List[Solution], 
                         reference_point: Tuple[float, float],
                         objectives: List[str] = None) -> float:
    """
    Calculate hypervolume indicator for Pareto frontier quality.
    
    Hypervolume measures the volume of objective space dominated by the
    Pareto set. Higher hypervolume = better Pareto frontier.
    
    Simplified 2D implementation for cost and latency.
    
    Args:
        pareto_solutions: Solutions on Pareto frontier
        reference_point: Worst acceptable values (max_cost, max_latency)
        objectives: Objectives (default: ['cost', 'latency'])
    
    Returns:
        Hypervolume value (area in 2D case)
    """
    if not pareto_solutions:
        return 0.0
    
    if objectives is None:
        objectives = ['cost', 'latency']
    
    # Sort solutions by first objective (cost)
    sorted_sols = sorted(pareto_solutions, key=lambda s: s.cost)
    
    hypervolume = 0.0
    prev_cost = 0.0
    
    for sol in sorted_sols:
        # Rectangle width: current_cost - previous_cost
        width = sol.cost - prev_cost
        # Rectangle height: reference_latency - current_latency
        height = reference_point[1] - sol.latency
        
        if width > 0 and height > 0:
            hypervolume += width * height
        
        prev_cost = sol.cost
    
    return hypervolume


def calculate_spacing_metric(pareto_solutions: List[Solution]) -> float:
    """
    Calculate spacing metric for Pareto frontier distribution.
    
    Measures how evenly distributed the Pareto solutions are.
    Lower spacing = more uniform distribution = better coverage.
    
    Args:
        pareto_solutions: Solutions on Pareto frontier
    
    Returns:
        Spacing metric (0 = perfectly uniform)
    """
    if len(pareto_solutions) < 2:
        return 0.0
    
    # Calculate distances between consecutive solutions
    sorted_sols = sorted(pareto_solutions, key=lambda s: s.cost)
    distances = []
    
    for i in range(len(sorted_sols) - 1):
        # Euclidean distance in normalized objective space
        cost_diff = sorted_sols[i+1].cost - sorted_sols[i].cost
        lat_diff = sorted_sols[i+1].latency - sorted_sols[i].latency
        dist = (cost_diff**2 + lat_diff**2)**0.5
        distances.append(dist)
    
    # Calculate mean distance
    mean_dist = sum(distances) / len(distances)
    
    # Calculate variance
    variance = sum((d - mean_dist)**2 for d in distances) / len(distances)
    
    # Spacing metric = standard deviation
    spacing = variance**0.5
    
    return spacing


def get_extreme_solutions(pareto_solutions: List[Solution]) -> Dict[str, Solution]:
    """
    Get extreme solutions from Pareto frontier.
    
    Returns:
        Dictionary with:
        - 'min_cost': Solution with minimum cost
        - 'min_latency': Solution with minimum latency
        - 'balanced': Solution closest to ideal point (min cost, min latency)
    """
    if not pareto_solutions:
        return {}
    
    min_cost_sol = min(pareto_solutions, key=lambda s: s.cost)
    min_latency_sol = min(pareto_solutions, key=lambda s: s.latency)
    
    # Find min values for normalization
    min_cost = min(s.cost for s in pareto_solutions)
    min_latency = min(s.latency for s in pareto_solutions)
    max_cost = max(s.cost for s in pareto_solutions)
    max_latency = max(s.latency for s in pareto_solutions)
    
    # Avoid division by zero
    cost_range = max_cost - min_cost if max_cost > min_cost else 1
    latency_range = max_latency - min_latency if max_latency > min_latency else 1
    
    # Find most balanced solution (closest to ideal point in normalized space)
    balanced_sol = min(pareto_solutions, key=lambda s: 
        ((s.cost - min_cost) / cost_range)**2 + 
        ((s.latency - min_latency) / latency_range)**2
    )
    
    return {
        'min_cost': min_cost_sol,
        'min_latency': min_latency_sol,
        'balanced': balanced_sol
    }


def calculate_pareto_metrics(solutions: List[Solution], 
                             pareto_solutions: List[Solution],
                             reference_point: Tuple[float, float] = None) -> Dict[str, Any]:
    """
    Calculate comprehensive Pareto frontier metrics.
    
    Args:
        solutions: All feasible solutions
        pareto_solutions: Solutions on Pareto frontier
        reference_point: Reference point for hypervolume (optional)
    
    Returns:
        Dictionary of metrics
    """
    if not solutions or not pareto_solutions:
        return {}
    
    # Auto-calculate reference point if not provided
    if reference_point is None:
        max_cost = max(s.cost for s in solutions)
        max_latency = max(s.latency for s in solutions)
        reference_point = (max_cost * 1.1, max_latency * 1.1)
    
    metrics = {
        'frontier_size': len(pareto_solutions),
        'coverage_rate': len(pareto_solutions) / len(solutions) * 100,
        'hypervolume': calculate_hypervolume(pareto_solutions, reference_point),
        'spacing': calculate_spacing_metric(pareto_solutions),
        'extreme_solutions': get_extreme_solutions(pareto_solutions),
    }
    
    # Add cost and latency ranges
    if pareto_solutions:
        metrics['cost_range'] = {
            'min': min(s.cost for s in pareto_solutions),
            'max': max(s.cost for s in pareto_solutions),
        }
        metrics['latency_range'] = {
            'min': min(s.latency for s in pareto_solutions),
            'max': max(s.latency for s in pareto_solutions),
        }
    
    return metrics
