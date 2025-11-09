"""
NSGA-II and MOEA/D Runners for Multi-Objective Optimization

This module provides wrappers for running NSGA-II and MOEA/D using pymoo.
Integrates with the existing Solution and experiment flow.
"""

from typing import List, Dict, Any
from models import Solution
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.optimize import minimize
from pymoo.core.problem import Problem

class CloudMigrationProblem(Problem):
    def __init__(self, components, constraints, objectives):
        super().__init__(n_var=len(components), n_obj=len(objectives), n_constr=0, xl=0, xu=1, type_var=np.int32)
        self.components = components
        self.constraints = constraints
        self.objectives = objectives
        # Map component options externally
        self.options = [comp['options'] for comp in components]

    def _evaluate(self, X, out, *args, **kwargs):
        # X: (pop_size, n_var) with indices into options
        F = []
        for row in X:
            config = {self.components[i]['name']: self.options[i][int(row[i])] for i in range(len(row))}
            # Evaluate objectives (cost, latency, etc.)
            vals = [self.objectives[obj](config) for obj in self.objectives]
            F.append(vals)
        out["F"] = np.array(F)


def run_nsga2(components, constraints, objectives, pop_size=50, n_gen=100, seed=42):
    problem = CloudMigrationProblem(components, constraints, objectives)
    algorithm = NSGA2(pop_size=pop_size)
    res = minimize(problem, algorithm, ('n_gen', n_gen), seed=seed, verbose=False)
    return res

def run_moead(components, constraints, objectives, pop_size=50, n_gen=100, seed=42):
    try:
        problem = CloudMigrationProblem(components, constraints, objectives)
        from pymoo.util.ref_dirs import get_reference_directions
        ref_dirs = get_reference_directions("das-dennis", problem.n_obj, n_partitions=pop_size)
        algorithm = MOEAD(ref_dirs=ref_dirs)
        res = minimize(problem, algorithm, ('n_gen', n_gen), seed=seed, verbose=False)
        print(f"[DEBUG] MOEA/D finished. Result F shape: {getattr(res, 'F', None).shape if hasattr(res, 'F') and res.F is not None else 'None'}")
        return res
    except Exception as e:
        print(f"[ERROR] MOEA/D failed: {e}")
        return None
