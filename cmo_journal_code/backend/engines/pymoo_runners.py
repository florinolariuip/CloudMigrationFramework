"""
NSGA-II and MOEA/D Runners for Multi-Objective Optimization

This module provides wrappers for running NSGA-II and MOEA/D using pymoo.
Integrates with the existing Solution and experiment flow.

Constraint handling (fix):
  The original implementation used n_constr=0, meaning hard constraints
  (budget, latency, provider count) were silently ignored.  This made the
  comparison with CMO methodologically unfair because CMO enforces all
  constraints as hard requirements.

  This version adds n_constr=3 with a penalty-based constraint vector G:
    G[0] = cost    - maxBudget   (must be <= 0 to be feasible)
    G[1] = latency - maxLatency  (must be <= 0)
    G[2] = providers - maxProviders (must be <= 0)

  pymoo's NSGA-II and MOEA/D natively handle inequality constraints through
  feasibility-first selection, which is equivalent to a hard constraint
  approach for the population as a whole.
"""

from typing import List, Dict, Any
from models import Solution
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.optimize import minimize
from pymoo.core.problem import Problem


class CloudMigrationProblem(Problem):
    """
    Combinatorial cloud migration problem for pymoo.

    Decision variables: integer indices into the option lists for each
    component (one index per component).

    Objectives (minimise both):
      F[0] = cost
      F[1] = latency

    Constraints (all must be <= 0 for feasibility):
      G[0] = cost    - maxBudget
      G[1] = latency - maxLatency
      G[2] = provider_count - maxProviders
    """

    def __init__(self, components, constraints, objectives):
        n_var = len(components)
        # Option counts per variable (upper bound for integer encoding)
        xu = np.array([len(comp['options']) - 1 for comp in components], dtype=int)

        super().__init__(
            n_var=n_var,
            n_obj=len(objectives),
            n_constr=3,            # budget, latency, providers — hard constraints
            xl=np.zeros(n_var, dtype=int),
            xu=xu,
            vtype=int,
        )
        self.components  = components
        self.constraints = constraints
        self.objectives  = objectives
        self.options     = [comp['options'] for comp in components]

    def _evaluate(self, X, out, *args, **kwargs):
        F, G = [], []
        max_budget    = getattr(self.constraints, 'maxBudget',   float('inf'))
        max_latency   = getattr(self.constraints, 'maxLatency',  float('inf'))
        max_providers = getattr(self.constraints, 'maxProviders', float('inf'))

        for row in X:
            config = {
                self.components[i]['name']: self.options[i][int(np.clip(row[i], 0, len(self.options[i]) - 1))]
                for i in range(len(row))
            }

            # Objective values
            vals = [self.objectives[obj](config) for obj in self.objectives]
            cost    = vals[0] if len(vals) > 0 else 0.0
            latency = vals[1] if len(vals) > 1 else 0.0

            # Provider count
            providers = len({svc.split()[0] for svc in config.values()})

            F.append(vals)
            # G[i] <= 0  ⟺  constraint satisfied
            G.append([
                cost    - max_budget,
                latency - max_latency,
                providers - max_providers,
            ])

        out["F"] = np.array(F, dtype=float)
        out["G"] = np.array(G, dtype=float)


def run_nsga2(components, constraints, objectives, pop_size=50, n_gen=100, seed=42):
    """Run NSGA-II with hard constraint enforcement (n_constr=3)."""
    problem   = CloudMigrationProblem(components, constraints, objectives)
    algorithm = NSGA2(pop_size=pop_size)
    res = minimize(problem, algorithm, ('n_gen', n_gen), seed=seed, verbose=False)
    return res


def run_moead(components, constraints, objectives, pop_size=50, n_gen=100, seed=42):
    """Run MOEA/D with hard constraint enforcement (n_constr=3)."""
    try:
        problem = CloudMigrationProblem(components, constraints, objectives)
        from pymoo.util.ref_dirs import get_reference_directions
        ref_dirs  = get_reference_directions("das-dennis", problem.n_obj, n_partitions=pop_size)
        algorithm = MOEAD(ref_dirs=ref_dirs)
        res = minimize(problem, algorithm, ('n_gen', n_gen), seed=seed, verbose=False)
        f_shape = getattr(res, 'F', None)
        print(f"[DEBUG] MOEA/D finished. Result F shape: {f_shape.shape if f_shape is not None else 'None'}")
        return res
    except Exception as e:
        print(f"[ERROR] MOEA/D failed: {e}")
        return None
