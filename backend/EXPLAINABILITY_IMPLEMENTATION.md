# Explainability Implementation

## Overview
This document describes the explainability features of the Hybrid CSP + Expert System approach for cloud migration optimization.

## Key Explainability Features

1. **Constraint Proofs**
   - Shows exact calculations for each constraint (budget, latency, provider count, dependencies).
   - Example: Budget check displays the sum of all service costs and compares to the allowed maximum.

2. **Rule Traces**
   - Logs which expert rules fired for each solution and why.
   - Includes rule name, condition evaluated, and points added or subtracted.
   - Provides full transparency into the scoring logic.

3. **Decision Path**
   - Step-by-step reasoning from constraints to final solution selection.
   - Details how many combinations were generated, filtered, scored, and ranked.

4. **Comparison with Baselines**
   - Shows how explainability in the hybrid approach exceeds that of baseline algorithms.
   - Baselines typically lack detailed reasoning or constraint proofs.

## Academic Value
- Explainability supports reproducibility, auditability, and trust in optimization results.
- Enables users and reviewers to understand why a solution was chosen and how constraints were satisfied.
- Facilitates debugging, validation, and improvement of the optimization pipeline.

---
For examples, see the per-run explainability data and decision traces in the main app.

---

## What the Sankey shows (experiments)

- Cost allocation by component/provider within a selected solution.
- Identify cost drivers (thick flows) and optimization targets.

### Example interpretation (first run per N)

- N=5: Non‑dominated points; Sankey highlights drivers between Min Cost (170.77, 11.20ms, 1 provider) and Min Latency (255.01, 10.00ms, 1 provider).
- N=10: Balanced (543.79, 9.70ms, 2 providers) shows cross‑provider split—trading locality/performance vs. price.
- N=15: Degenerate frontier (676.37, 9.00ms, 1 provider) → single dominant cost path; limited optimization room.

## Rule trace (template)

Use this table to log rule effects from the backend explainability payload.

| Rule ID | Description | Triggered | Effect | Note |
|---|---|---|---|---|
| R-CACHE-1 | Prefer cache with read‑heavy workloads | Yes/No | Lowers read latency | — |
| R-CDN-2 | Use CDN when global users | Yes/No | Improves latency, adds provider | — |
| R-PROV-1 | Limit providers ≤ 2 | Yes | Prunes multi‑cloud variants | Binding constraint |

## Extremes table (from experiments)

| N | Type | Cost ($) | Latency (ms) | Providers |
|---:|---|---:|---:|---:|
| 5 | Min Cost | 170.77 | 11.20 | 1 |
| 5 | Min Latency | 255.01 | 10.00 | 1 |

---

## New Experiments: Evolutionary and Oracle Baselines

Explainability is preserved for all new baselines. NSGA-II, MOEA/D, and oracle exhaustive results are logged with full configuration and metrics. All runs use fixed seeds for reproducibility.

---

## Threats to Validity

- **Explainability**: Baselines lack detailed reasoning; only the hybrid approach provides full constraint and rule trace logs.
- **Stochasticity**: Evolutionary results are averaged over fixed seeds; logs are available for all runs.
- **Reproducibility**: All code, seeds, and requirements are pinned and available in the Docker image.
| 5 | Balanced | 226.01 | 10.20 | 2 |
| 10 | Min Cost | 530.87 | 10.30 | 2 |
| 10 | Min Latency | 566.75 | 9.50 | 1 |
| 10 | Balanced | 543.79 | 9.70 | 2 |
| 15 | Min Cost | 676.37 | 9.00 | 1 |
| 15 | Min Latency | 676.37 | 9.00 | 1 |
| 15 | Balanced | 676.37 | 9.00 | 1 |

## Takeaways

- Sankey + extremes clarify why points are non‑dominated (which costs shift).
- Rules explain pruning and structure; pair with provider counts to show constraint compliance.
- Use these visuals and tables directly in the paper (figures and appendix).