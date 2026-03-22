# Explainability Implementation

## Overview
This document describes the explainability features of the Hybrid CSP + Expert System + Pareto approach implemented in CMOv3 and CMOv4. The goal is to make every optimization run auditable end‑to‑end: from raw constraints and pricing, through rule evaluation, to the final Pareto‑ranked solutions and academic PDF reports.

## Key Explainability Features

1. **Constraint Proofs (backend.engines.explainability.generate_constraint_proof)**
   - For each evaluated solution, the backend constructs a constraint proof object that shows how key constraints were checked:
     - Budget: total monthly cost versus `maxBudget` (default ≈ $5,000).
     - Latency: end‑to‑end latency versus `maxLatency` (default ≈ 150 ms).
     - Provider limits: number of distinct providers versus `maxProviders` (default = 3).
     - Feasibility flags from the CSP engine.
   - These proofs are attached to the JSON payload returned by the optimization and benchmark endpoints and can be rendered directly in the UI or exported into the academic PDF report.

2. **Rule Traces (backend.engines.explainability.generate_rule_trace)**
   - The Expert System (implemented on top of the rules engine in `backend.engines.rules`) evaluates every feasible solution with 20+ business rules.
   - For each solution, the backend builds a rule trace that contains:
     - Rule identifier and category (e.g., provider diversity, latency sensitivity, budget adaptation).
     - Condition outcome (triggered / not triggered).
     - Score impact (points added or subtracted from the solution score).
   - Rule traces are returned alongside solutions in API responses so the frontend and PDF generator can show “why this architecture scored higher”.

3. **Decision Path (backend.engines.explainability.generate_decision_path)**
   - The decision path summarizes the full journey from raw constraints and preferences to the final ranked set of solutions. It typically includes:
     - How many combinations the CSP engine generated (strategic sampling in CMOv4, exhaustive or constrained search in CMOv3).
     - How many solutions remained after constraint filtering and deduplication.
     - How many solutions were scored by the Expert System and how many survived Pareto filtering.
   - This path is used both in the API responses and in the academic report generator to provide a high‑level narrative of the optimization process.

4. **Explainability Metrics and Comparison with Baselines (backend.engines.explainability.compare_explainability)**
   - The framework includes utilities to compare the explainability of the hybrid approach against baseline algorithms (GA, greedy, random, weighted sum).
   - Baselines are executed through `backend.engines.baselines`, and their outputs are wrapped with minimal metadata (cost, latency, iterations, convergence reason).
   - The hybrid approach enriches these results with constraint proofs, rule traces, and decision paths; the comparison function highlights this gap so that academic experiments can report not only performance metrics but also explainability advantages.

## Research Value
- Explainability supports reproducibility, auditability, and trust in optimization results.
- Enables researchers and practitioners to understand why a solution was chosen and how constraints were satisfied.
- Facilitates debugging, validation, and improvement of the optimization pipeline.
- Addresses the "black-box" problem common in optimization algorithms.

---
For examples, see the per‑run explainability data and decision traces in the main application interface and in the academic PDF report.

---

## Visual Explainability: Sankey and Latency Graphs

- **Cost Sankey diagrams** (`backend.engines.sankey.generate_sankey_data`)
   - Show cost allocation by component and provider within a selected solution.
   - Highlight cost drivers via thicker flows (for example, expensive databases or cross‑region data transfer).
   - Are generated on demand for any solution returned by the optimizer and embedded both in the frontend and in the academic report.
- **Latency Sankey / critical‑path views** (`backend.engines.sankey.generate_latency_sankey` and `backend/engines/latency_graph.py`)
   - Visualize latency contributions along the critical path in the architecture graph.
   - Help explain why two solutions with similar average latency may still differ in tail behavior or dependency structure.

### Example Interpretation (from experiments)

- For small component counts (e.g., 5 components), non‑dominated solutions often reflect simple single‑provider deployments where Sankey diagrams highlight which core service dominates cost.
- For medium architectures (e.g., 10 components), “balanced” solutions show clear cross‑provider splits, making it easy to explain how moving specific components between providers trades cost against latency.
- For larger architectures (e.g., 15 components), degenerate frontiers can emerge where one configuration dominates in both cost and latency; here, Sankey still helps identify which components leave little room for further optimization.

## Academic PDF Report Integration

The academic report generator (`backend/academic_report_generator.py`) consumes the same explainability payloads returned by the API:

- Constraint proofs and decision paths are summarized in dedicated sections that describe the optimization process and feasibility checks.
- Rule traces feed into narrative explanations of why selected architectures are preferable (for example, emphasizing cache usage for read‑heavy workloads or CDN adoption for global traffic).
- Pareto frontiers and Sankey diagrams are embedded as figures to visually communicate trade‑offs and cost/latency drivers.

This ensures that the explainability layer is not just a debugging aid but a first‑class component of the research reports generated from the framework.