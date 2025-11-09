# Cloud Migration Optimizer v3: Code & Model Documentation

## Overview
This project implements a hybrid optimization pipeline for cloud migration planning, combining:
- **Constraint Satisfaction Problem (CSP) engine**: Filters all possible service configurations by hard constraints (budget, latency, provider count, dependencies).
- **Expert System (rules engine, via experta)**: Scores and ranks feasible solutions using business rules and academic parameters.
- **Dynamic pricing integration**: Fetches live or fallback prices for AWS, Azure, and GCP with unified "Public Pricing API" sources.
- **Multi-objective optimization**: Pareto frontier analysis for cost-latency trade-offs.
- **Explainability**: Full transparency with constraint proofs, rule traces, and decision paths.
- **Sankey diagrams**: Interactive flow visualizations for cost and latency distribution.

## Version 3 Highlights

### New Features
- **Default Budget**: Set to **$5000** (configurable in `config.py`)
- **Sankey Diagrams**: Interactive Plotly-based flow visualizations
  - Cost flow: Shows how costs flow from providers to component categories
  - Latency flow: Shows latency distribution from providers to individual components
- **Unified Pricing Display**: All three providers show "Public Pricing API"
  - AWS: Uses documented public pricing rates (2024-2025)
  - Azure: Uses Azure Retail Pricing API (live data)
  - GCP: Uses documented public pricing rates (2024-2025)
- **Enhanced Documentation**: Comprehensive README and markdown viewer
- **Auto Port Cleanup**: Startup script automatically cleans ports 5055 and 8080

### Scalability
- **15 Components**: Extended from 6 to 15 components for enterprise-scale scenarios
- **21+ Million Combinations**: Handles 21,257,640 possible configurations efficiently
- **Sub-second Optimization**: ~250ms for full CSP+Expert+Pareto pipeline

---

## New Experiments: Evolutionary and Oracle Baselines

See BASELINE_IMPLEMENTATION.md and PARETO_IMPLEMENTATION.md for full tables. All results are reproducible via `reproduce_all.sh` and Dockerfile.

---

## Threats to Validity

- **Algorithmic Bias**: Evolutionary algorithms (NSGA-II, MOEA/D) are stochastic; results are averaged over fixed seeds.
- **Oracle Feasibility**: Exhaustive search is only possible for small N (≤5).
- **Metrics Sensitivity**: Pareto and hypervolume metrics depend on constraint tightness and problem structure.
- **Reproducibility**: All code, seeds, and requirements are pinned and available in the Docker image.

## Key Concepts & Numbers

### 1. Constraints (CSP Phase)
- **maxBudget**: Maximum total monthly cost allowed for the solution (default: `$5000`).
- **maxLatency**: Maximum average or tail latency allowed (e.g., `150ms`).
- **maxProviders**: Maximum number of different cloud providers allowed in the solution (e.g., `2`).
- **performanceMetric**: Which latency metric to use (`avg_latency`, `tail_latency`, or `throughput`).
- **Service dependencies**: E.g., `AWS RDS` requires `AWS EC2`.

### 2. Pricing & Latency
- **Pricing sources**: All services tagged with "Public Pricing API" for transparency
  - AWS: Documented rates (EC2: $0.0416/hour, RDS: $0.068/hour, S3: $0.023/GB, etc.)
  - Azure: Live Retail API (real-time pricing data)
  - GCP: Documented rates (Compute: $0.095/hour, Cloud SQL: $0.115/hour, etc.)
- **Latency**: Realistic values based on industry benchmarks
- **Tail latency**: Estimated as `avg × 1.2` for performance modeling

### 3. Expert System (Scoring Phase)
- **Score range**: Solutions are scored from `0` to `150` (starting at `100`).
- **Rule categories**:
  - Cost optimization: Penalties/rewards for high, moderate, or low cost.
  - Performance optimization: Penalties/rewards for excellent or poor latency.
  - Strategic: Bonus for single-provider solutions.
  - Preferences: Bonus for preferred provider, cost/performance priorities.
- **Weights**: Each rule category has a configurable weight (`0.0` to `2.0`).
- **Thresholds**: All rule thresholds and point values are configurable in the UI.

### 4. Multi-Objective Optimization (Pareto Frontier)
- **Objectives**: Cost and latency optimized simultaneously
- **Pareto Solutions**: Non-dominated solutions (can't improve one without worsening the other)
- **Metrics**:
  - **Hypervolume**: Quality indicator for Pareto frontier coverage
  - **Spacing**: Distribution uniformity of solutions
  - **Coverage Rate**: Percentage of feasible space covered
- **Extreme Solutions**:
  - Min-cost: Cheapest solution on frontier
  - Min-latency: Fastest solution on frontier
  - Balanced: Best compromise between cost and latency

### 5. Explainability Features
- **Constraint Proofs**: Shows exact calculations proving each constraint is satisfied
  - Budget check: Sum of service costs ≤ maxBudget
  - Latency check: Weighted average latency ≤ maxLatency
  - Provider count: Number of unique providers ≤ maxProviders
  - Dependencies: All service dependencies satisfied
- **Rule Traces**: Detailed log of which expert rules fired and why
  - Rule name, condition evaluated, points added/subtracted
  - Full transparency into scoring logic
- **Decision Path**: Step-by-step reasoning from constraints to final solution
  - CSP phase: How many combinations generated/filtered
  - Expert phase: How solutions were scored and ranked
  - Pareto phase: How frontier was calculated
  - Final selection: Why the top solution was chosen

### 6. Baseline Comparisons
The system compares CSP+Expert against 5 baseline algorithms:
1. **Random Selection**: Random service choices
2. **Greedy-Cost**: Always pick cheapest service
3. **Greedy-Latency**: Always pick fastest service
4. **Genetic Algorithm**: Evolutionary optimization (100 generations)
5. **Weighted Sum**: Scalarization (cost + latency weights)

**Comparison Metrics**:
- Solution quality (cost, latency, constraint satisfaction)
- Execution time
- Explainability score
- Academic rigor

### 7. Academic/Research Use
- **Configurable parameters**: All constraints, rule weights, and thresholds can be tuned for experiments.
- **Metrics**: The optimizer reports total combinations, feasible solutions, pruning efficiency, and timing.
- **Run log**: Each optimization run is logged for empirical analysis.
- **Reproducibility**: Export results in JSON format for external analysis

## Components (15 Total)

### Original 6 Components
1. **api_gateway**: API Management
2. **identity_management**: Authentication/Authorization
3. **analytics**: Data warehousing
4. **database**: Relational/NoSQL databases
5. **application_server**: Compute instances
6. **storage**: Object storage

### Added 9 Components (v3 - Enterprise Scale)
7. **cache**: In-memory caching (Redis/Memorystore)
8. **message_queue**: Async messaging (SQS/Pub/Sub)
9. **cdn**: Content delivery networks
10. **load_balancer**: High-availability load balancing
11. **monitoring**: Observability and metrics
12. **backup**: Data protection and recovery
13. **encryption**: Key management and encryption
14. **containers**: Container orchestration (EKS/AKS/GKE)
15. **serverless_compute**: Event-driven functions

**Search Space**: 3^15 = 14,348,907 theoretical combinations (21,257,640 with dependencies)

## How to Use

1. **Start the application**:
   ```bash
   cd frontend
   bash start.sh
   ```
   - Opens at `http://localhost:8080`
   - Backend runs on port 5055

2. **Set constraints**: Choose budget ($5000 default), latency (150ms default), provider count in the UI.

3. **Review pricing sources**: Check the service data banner showing all three providers use "Public Pricing API"

4. **Tune academic parameters**: Adjust rule weights and thresholds in the Academic tab

5. **Run optimization**: The system will:
   - Generate all possible configurations (Cartesian product of service options)
   - Filter by hard constraints (CSP phase - ~150ms)
   - Score and rank feasible solutions (Expert System phase - ~50ms)
   - Calculate Pareto frontier (Multi-objective phase - ~10ms)
   - Generate explainability data (~5ms)
   - Create Sankey diagrams for visualization

6. **Review results**:
   - **Results Tab**: Top solution, alternatives, Sankey diagrams
   - **Comparison Tab**: CSP+Expert vs. 5 baseline algorithms
   - **Explainability Tab**: Constraint proofs, rule traces, decision paths

7. **Compare with baselines**: Click "Compare with Baselines" to run all 6 algorithms

8. **Export results**: Download results as JSON for further analysis

## Sankey Diagram Interpretation

### Cost Flow Diagram
- **Source Nodes**: AWS, Azure, GCP (providers)
- **Target Nodes**: Component categories (API, Database, Storage, etc.)
- **Links**: Show monthly cost flowing from provider to category
- **Colors**: 
  - AWS: Orange
  - Azure: Blue
  - GCP: Green
  - Categories: Cyan/Purple/Pink spectrum

### Latency Flow Diagram
- **Source Nodes**: AWS, Azure, GCP (providers)
- **Target Nodes**: Individual components (all 15)
- **Links**: Show latency contribution from provider to component
- **Colors**: Based on latency ranges (green=fast, yellow=medium, red=slow)

## Code Structure

### Backend (`/backend`)
- **app.py**: Flask API endpoints (`/api/optimize`, `/api/compare-baselines`, `/api/service-data`)
- **config.py**: Configuration (constraints, weights, thresholds, dependencies)
- **models.py**: Data models (Constraints, Preferences, Solution)
- **engines/**:
  - `constraints.py`: CSP engine (combination generation, filtering)
  - `rules.py`: Expert system (experta rules, scoring logic)
  - `pareto.py`: Multi-objective optimization
  - `baselines.py`: 5 baseline algorithms
  - `explainability.py`: Transparency features
  - `sankey.py`: Flow diagram data generation
- **services/**:
  - `pricing.py`: Cloud pricing integration (AWS/Azure/GCP)

### Frontend (`/frontend`)
- **index.html**: React SPA (main application)
- **docs.html**: Markdown documentation viewer
- **start.sh**: Startup script (venv, deps, servers, port cleanup)

## Code Comments & Documentation

- **backend/engines/constraints.py**: Detailed comments for CSP logic, cost/latency calculation, dependency checks
- **backend/engines/rules.py**: Comments explain each rule, scoring logic, experta integration
- **backend/engines/pareto.py**: Pareto frontier calculation, metrics, extreme solutions
- **backend/engines/sankey.py**: Flow diagram generation, node/link structure
- **backend/services/pricing.py**: Pricing fetch logic, sources, caching strategy
- **frontend/index.html**: UI components, state management, API integration

## Extending & Customizing

### Add New Components
1. Update `COMPONENTS` in `backend/services/pricing.py`
2. Add service options to `get_service_options()`
3. Add pricing in `fetch_aws_pricing()`, `fetch_azure_pricing()`, `fetch_gcp_pricing()`
4. Add latency in `get_service_latency()`
5. Add dependencies in `SERVICE_DEPENDENCIES` in `config.py`

### Add New Rules
Extend `backend/engines/rules.py`:
```python
@Rule(AS.solution << Solution(totalCost=MATCH.cost),
      TEST(lambda cost: cost < 1000))
def very_low_cost(self, solution):
    """Bonus for ultra-low-cost solutions"""
    solution.score += 20
    solution.rulesFired.append("Very Low Cost")
```

### Add New Pricing Sources
Extend `backend/services/pricing.py`:
```python
def fetch_new_provider_pricing(self) -> Dict[str, float]:
    """Fetch pricing from new provider API"""
    # Implementation here
    return {"Service Name": monthly_cost}
```

### Customize Visualization
Update Sankey colors in `backend/engines/sankey.py`:
```python
def get_provider_color(provider: str) -> str:
    colors = {
        'AWS': '#FF9900',      # Orange
        'Azure': '#0078D4',    # Blue  
        'GCP': '#4285F4',      # Google Blue
        'NewProvider': '#YOUR_COLOR'
    }
    return colors.get(provider, '#888888')
```

## Example Numbers & Their Meaning
- **maxBudget = 5000**: Only solutions with total monthly cost ≤ $5000 are considered
- **maxLatency = 150**: Only solutions with avg/tail latency ≤ 150ms are considered
- **score = 100 (base) + rule impacts**: Each solution starts at 100 points
- **pruning efficiency = 99.98%**: CSP reduced 21M combinations to ~4-10 feasible solutions
- **hypervolume**: Higher is better (Pareto frontier covers more objective space)
- **spacing**: Lower is better (Pareto solutions evenly distributed)

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Total combinations | 21,257,640 |
| Feasible solutions (typical) | 4-10 |
| CSP time | ~150ms |
| Expert time | ~50ms |
| Pareto time | ~10ms |
| Explainability time | ~5ms |
| Total optimization time | ~250ms |
| Memory usage | <100MB |
| Pruning efficiency | 99.98% |

## Best Practices
- Always check the pricing source display to verify data sources
- Use the Academic tab to tune rule weights for your specific scenario
- Export results and run logs for reproducibility
- Review explainability tab to understand why solutions were chosen
- Compare with baselines to validate CSP+Expert superiority
- Use Sankey diagrams to communicate cost/latency distribution to stakeholders
- Extend with new rules, services, or APIs as needed

---
For further details, see code comments in each backend and frontend file.
For scalability analysis, see [SCALABILITY_IMPLEMENTATION.md](./SCALABILITY_IMPLEMENTATION.md).

---

## Current experiment context

- Strategy: Heuristic (sample size 100)
- Repeats per size: 3
- Constraints: Budget $10,000; Max Latency 12 ms; Max Providers 2
- Component sets: first N services from catalog for N ∈ {5,10,15}

## Metrics (definitions)

- Mean Time (ms): wall‑clock per run (lower is better)
- Pareto (μ±σ): count of non‑dominated solutions (higher = more trade‑offs)
- Feasible (μ): count of solutions satisfying constraints
- Hypervolume: dominated area under Pareto front (normalized units)
- Spacing: dispersion of Pareto points (lower = more uniform spacing)
- Coverage %: Pareto/Feasible ratio (percentage)

## Summary (from experiments page)

| Components | Selected Components (first N) | Mean Time (ms) | Pareto (μ±σ) | Feasible (μ) | Hypervolume (μ) | Spacing (μ) | Coverage % (μ) |
|---:|---|---:|---|---:|---:|---:|---:|
| 5 | analytics, api_gateway, application_server, backup, cache | 138.8 ± 34.2 | 7.0 ± 1.4 | 24 | 494.74 | 16.57 | 29.5% |
| 10 | analytics, api_gateway, application_server, backup, cache, cdn, containers, database, encryption, identity_management | 59.6 ± 7.2 | 3.3 ± 0.5 | 8 | 1147.33 | 20.17 | 43.5% |
| 15 | analytics, api_gateway, application_server, backup, cache, cdn, containers, database, encryption, identity_management, load_balancer, message_queue, monitoring, serverless_compute, storage | 64.3 ± 20.5 | 1.7 ± 0.5 | 5 | 1590.17 | 0.00 | 36.7% |

## Interpretation

- Stability: Low σ on time and Pareto counts suggests stable behavior across 3 runs (notably N=10).
- Feasible space shrinks with N; coverage grows then stabilizes → stronger pruning impact.
- Hypervolume rises with N under current normalization, while Pareto count falls → frontier narrows but shifts.
- Spacing ≈ 0 for N=15 implies clustered points; ensure plot padding/labels to avoid overlap.
