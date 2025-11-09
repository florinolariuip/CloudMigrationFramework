"""
Oracle exhaustive search for small-N problems (baseline)
Finds all valid configurations and returns the Pareto frontier.
"""
from typing import List
from models import Constraints, Solution
from services.pricing import get_service_options, COMPONENTS
from engines.pareto import calculate_pareto_frontier
import itertools

def run_oracle_exhaustive(constraints: Constraints) -> List[Solution]:
    options = get_service_options()
    # Generate all possible configurations (cartesian product)
    all_combinations = list(itertools.product(*[options[c] for c in COMPONENTS]))
    solutions = []
    for combo in all_combinations:
        config = {comp: val for comp, val in zip(COMPONENTS, combo)}
        # Check constraints (reuse baseline logic)
        from engines.baselines import is_valid_configuration, create_solution_from_config
        if is_valid_configuration(config, constraints):
            solutions.append(create_solution_from_config(config))
    # Return Pareto frontier
    return calculate_pareto_frontier(solutions)
