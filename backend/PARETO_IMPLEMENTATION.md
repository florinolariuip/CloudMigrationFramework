# Pareto Implementation

This document describes the implementation of Pareto optimization within the Cloud Migration Optimizer.

## Overview
Pareto optimization is used to identify solutions that are non-dominated with respect to multiple objectives, such as cost, performance, and scalability. A solution is Pareto optimal if no other solution is better in all objectives simultaneously.

## Algorithm
- The optimizer evaluates all candidate solutions.
- For each solution, it checks if there exists another solution that is better in every objective.
- Non-dominated solutions are collected as the Pareto front.

## Metrics
- **Cost**: Total migration and operational cost.
- **Performance**: Resource utilization, latency, throughput.
- **Scalability**: Ability to handle increased load or future growth.

## Visualization
Pareto fronts are visualized using scatter plots, where each axis represents an objective. Users can interact with these plots to explore trade-offs between solutions.

## Academic Value
Pareto optimization provides a rigorous method for multi-objective decision making, supporting transparent and reproducible research.

---
*For further details, see the source code in `engines/pareto.py` and related documentation.*

---

## Method and Findings (experiments)

### Method

- Objectives: minimize Cost ($), minimize Latency (ms).
- Dominance: A dominates B if A is no worse in all objectives and strictly better in at least one.
- Frontier extraction: non-dominated filter over feasible set; metrics include hypervolume and spacing.

### Extreme solutions (first run per N)

| N | Type | Cost ($) | Latency (ms) | Providers |
|---:|---|---:|---:|---:|
| 5 | Min Cost | 170.77 | 11.20 | 1 |
| 5 | Min Latency | 255.01 | 10.00 | 1 |
| 5 | Balanced | 226.01 | 10.20 | 2 |
| 10 | Min Cost | 530.87 | 10.30 | 2 |
| 10 | Min Latency | 566.75 | 9.50 | 1 |
| 10 | Balanced | 543.79 | 9.70 | 2 |
| 15 | Min Cost | 676.37 | 9.00 | 1 |
| 15 | Min Latency | 676.37 | 9.00 | 1 |
| 15 | Balanced | 676.37 | 9.00 | 1 |

Notes:

---

## New Experiments: Evolutionary and Oracle Baselines

| N | Algorithm | Min Cost | Min Latency | Balanced | Oracle Pareto |
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

---

## Threats to Validity

- **Frontier Quality**: Evolutionary algorithms may miss rare optima; oracle is only feasible for small N.
- **Stochasticity**: Results for NSGA-II/MOEA/D are averaged over fixed seeds.
- **Reproducibility**: All code, seeds, and requirements are pinned and available in the Docker image.

