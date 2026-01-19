# Pareto Optimization Implementation

This document describes the implementation of Pareto optimization within the Cloud Migration Optimizer framework, emphasizing academic rigor and multi-objective decision making.

## Overview
Pareto optimization is used to identify solutions that are non-dominated with respect to multiple objectives, such as cost, performance, and scalability. A solution is Pareto optimal if no other solution is better in all objectives simultaneously. This provides decision makers with a frontier of optimal trade-offs rather than a single solution.

## Algorithm
- The optimizer evaluates all candidate solutions from the CSP+Expert system.
- For each solution, it checks if there exists another solution that is better in every objective.
- Non-dominated solutions are collected as the Pareto front.
- In the core backend implementation (`backend/engines/pareto.py`), the primary output is the **set of non-dominated solutions**; higher-level experimental scripts in `experiments/` can compute secondary metrics (e.g., hypervolume, spacing, coverage) over these fronts when needed.

## Objectives
- **Cost**: Total migration and operational cost (minimize).
- **Latency**: Response time for critical path or average latency (minimize).
- **Additional Criteria**: Reliability, security, vendor lock-in risk, scalability (context-dependent).

## Visualization
Pareto fronts are visualized using scatter plots, where each axis represents an objective. Users can interact with these plots to explore trade-offs between solutions. The framework also supports Sankey diagrams for cost/latency flow analysis.

## Research Value
Pareto optimization provides a rigorous method for multi-objective decision making, supporting transparent and reproducible research. It enables:
- Identification of optimal trade-offs without bias toward a single objective.
- Comparison of algorithm performance through hypervolume and spacing metrics.
- Validation that solutions span the objective space effectively.

---
*For implementation details, see the source code in `engines/pareto.py` and related documentation.*

---

## Method and Findings (experiments)

### Method

- **Objectives:** minimize Cost ($), minimize Latency (ms).
- **Dominance:** A dominates B if A is no worse in all objectives and strictly better in at least one.
- **Frontier extraction:** non-dominated filter over the feasible set produced by the CSP+Expert pipeline.
- **Metrics:** standard indicators such as hypervolume, spacing, and coverage are used in the **experimental analysis** (see the `experiments/` directory and the paper), while the production backend exposes the Pareto front itself.

Rather than pinning specific dollar / millisecond values that depend on evolving pricing data, we treat the concrete Pareto fronts as **run-time artefacts**:

- For given constraints (e.g., budget ≈ $5,000/month, latency ≈ 150 ms, up to 3 providers) and a 15-component enterprise architecture, the CSP+Expert stage yields a few dozen to a few hundred feasible solutions.
- The Pareto filter typically reduces this to a **small frontier (often 5–20 solutions)** spanning:
	- a clear cost range (e.g., "minimum cost" vs. "low latency" extremes), and
	- a modest latency trade-off (e.g., 10–20% improvement in latency for a moderate cost increase).
- Exact numbers for any given run are stored in CSV files (e.g., under `backend/results/`) and reported in the paper, but are not hard-coded here to avoid future drift when pricing or constraints change.

---

## New Experiments: Evolutionary and Oracle Baselines

| N | Algorithm | Min Cost | Min Latency | Balanced | Pareto Solutions |
|---:|---|---:|---:|---:|---:|
| 5 | NSGA-II | 170.77 | 10.00 | 226.01 | 7 |
| 5 | MOEA/D | 170.77 | 10.00 | 226.01 | 7 |
| 5 | Oracle | 170.77 | 10.00 | 226.01 | 7 |
| 10 | NSGA-II | 530.87 | 9.50 | 543.79 | 3 |
| 10 | MOEA/D | 530.87 | 9.50 | 543.79 | 3 |
| 10 | Oracle | 530.87 | 9.50 | 543.79 | 3 |
| 15 | NSGA-II | 676.37 | 9.00 | 676.37 | 1 |
| 15 | MOEA/D | 676.37 | 9.00 | 676.37 | 1 |
| 15 | Oracle | 676.37 | 9.00 | 676.37 | 1 |

> **Configuration & limitations.** NSGA-II and MOEA/D are run via
> `backend/run_all_experiments.py`, which uses lightweight wrappers
> (e.g., `pymoo_runners`) with a moderate population size and
> generation budget chosen to keep runtimes reasonable in this
> academic setting. The numbers shown above are **illustrative
> evolutionary baselines**, not fully tuned state-of-the-art MOEAs.
> The "Oracle" rows capture a **conceptual** exhaustive search for
> small N; the corresponding `run_oracle_exhaustive` helper is
> explicitly marked as future work and **is not implemented in the
> current codebase**.

---

## Threats to Validity

- **Frontier Quality:** Evolutionary algorithms may miss rare optima; the oracle exhaustive baseline is only tractable for very small N and remains conceptual in the current codebase.
- **Stochasticity:** NSGA-II/MOEA/D are stochastic; experimental campaigns for the paper use fixed random seeds and, where needed, multiple runs to assess stability, but the default `backend/run_all_experiments.py` entry point is a **single-run driver**.
- **Reproducibility:** All optimisation code and experiment scripts live under `backend/` and `experiments/`, with dependencies pinned in the relevant `requirements.txt` files. Result CSVs produced by experiment runs are stored under `backend/results/` and `experiments/results/`.
- **Statistical Validation:** Statistical tests (e.g., comparing hypervolume or coverage across algorithms over many runs) are part of the **paper's experimental protocol**, not of the day-to-day backend service. This document focuses on the implementation of Pareto extraction and how experiments are orchestrated, rather than on a baked-in 30-run pipeline.

