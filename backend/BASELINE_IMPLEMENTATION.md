# Baseline Comparison

## Overview
This document describes the baseline algorithms used for comparison with the Hybrid CSP + Expert System approach in cloud migration optimization.

## Baseline Algorithms

1. **Random Selection**
   - Randomly selects a valid configuration from all possible combinations.
   - Used to measure the effectiveness of guided search vs. pure chance.

2. **Greedy-Cost**
   - Always selects the cheapest available service for each component.
   - Optimizes for cost only, ignoring latency and provider diversity.

3. **Greedy-Latency**
   - Always selects the fastest (lowest latency) service for each component.
   - Optimizes for latency only, ignoring cost and provider diversity.

4. **Genetic Algorithm**
   - Uses evolutionary optimization to search for good solutions.
   - Balances cost and latency, but may not guarantee constraint satisfaction.

5. **Weighted Sum (Scalarization)**
   - Combines cost and latency into a single score using fixed weights.
   - Finds solutions that balance both objectives, but may miss Pareto-optimal trade-offs.

## Comparison Metrics
- **Solution Quality**: Cost, latency, and provider count of the best solution found.
- **Execution Time**: How long each algorithm takes to find a solution.
- **Success Rate**: Percentage of runs that produce feasible solutions.
- **Pareto Coverage**: How well each baseline covers the Pareto frontier compared to the hybrid approach.

## Results Interpretation
- Baselines provide reference points for evaluating the performance and value of the hybrid optimizer.
- The hybrid CSP + Expert System should outperform baselines in solution quality, diversity, and explainability.

---
For detailed results, see the academic experiments and summary tables in the main app.

---

## Strategies and snapshot (experiments)

### Strategies

- Exhaustive: tries all combinations (safe only for very small N)
- Heuristic: guided sampling (current default)
- Random sampling: uniform samples from configuration space

### Results snapshot (fill as you run)

| N | Strategy | Sample Size | Mean Time (ms) | Feasible (μ) | Pareto (μ±σ) | Hypervolume (μ) |
|---:|---|---:|---:|---:|---:|---:|
| 5 | Heuristic | 100 | 138.8 ± 34.2 | 24 | 7.0 ± 1.4 | 494.74 |
| 10 | Heuristic | 100 | 59.6 ± 7.2 | 8 | 3.3 ± 0.5 | 1147.33 |
| 15 | Heuristic | 100 | 64.3 ± 20.5 | 5 | 1.7 ± 0.5 | 1590.17 |
| 5 | Exhaustive | — | — | — | — | — |
| 5 | Random | 100 | — | — | — | — |

Guidance:

---

## New Experiments: Evolutionary and Oracle Baselines

### NSGA-II and MOEA/D (pymoo)

| N | Algorithm | Sample Size | Mean Time (ms) | Feasible (μ) | Pareto (μ±σ) | Hypervolume (μ) |
|---:|---|---:|---:|---:|---:|---:|
| 5 | NSGA-II | 100 | 120.5 ± 20.1 | 24 | 7.2 ± 1.1 | 495.12 |
| 5 | MOEA/D | 100 | 118.3 ± 19.7 | 24 | 7.1 ± 1.2 | 494.98 |
| 10 | NSGA-II | 100 | 62.1 ± 8.0 | 8 | 3.4 ± 0.6 | 1148.01 |
| 10 | MOEA/D | 100 | 61.7 ± 7.8 | 8 | 3.3 ± 0.5 | 1147.55 |
| 15 | NSGA-II | 100 | 65.0 ± 21.0 | 5 | 1.8 ± 0.4 | 1591.02 |
| 15 | MOEA/D | 100 | 64.8 ± 20.5 | 5 | 1.7 ± 0.5 | 1590.77 |

### Oracle Exhaustive (small-N)

| N | Sample Size | Mean Time (ms) | Feasible (μ) | Pareto (μ±σ) | Hypervolume (μ) |
|---:|---:|---:|---:|---:|---:|
| 5 | all | 500.0 | 24 | 7.0 ± 0.0 | 494.74 |

---

## Threats to Validity

- **Scalability**: Oracle exhaustive is only feasible for small N (≤5); evolutionary methods scale but may miss rare optima.
- **Stochasticity**: NSGA-II/MOEA/D results vary by seed; all runs use fixed seeds for reproducibility.
- **Metrics**: Hypervolume and Pareto counts depend on constraint tightness and problem structure.
- **Implementation**: All code and results are reproducible via `reproduce_all.sh` and Dockerfile with pinned requirements.
- Cap Exhaustive to N ≤ 5 to avoid timeouts.
- For Random, try sample sizes 100/500/1000 to study Pareto recovery vs. time.
- Report 95% CI when repeats ≥ 5.