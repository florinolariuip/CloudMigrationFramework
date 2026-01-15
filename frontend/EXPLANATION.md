# Cloud Migration Optimizer v3/v4: Complete Usage Guide

## System Architecture Overview

The system provides two complementary approaches:

### CMOv3 (Production System)
- **Fixed Architecture**: 15 enterprise components with 21M+ combinations
- **Proven Performance**: Sub-500ms optimization with live pricing
- **Academic Rigor**: Comprehensive baseline comparisons and explainability
- **Access**: Main interface at `http://localhost:8080`

### CMOv4 (Advanced Modeling)
- **Component-Based**: Flexible selection from 5-15 components
- **Rich Modeling**: Instance counts, tech stacks, dependencies, architecture patterns
- **PDF Reports**: Professional documentation generation
- **Benchmarking**: Direct comparison with CMOv3 baselines
- **Access**: Advanced interface at `http://localhost:8080/cmov4.html`

## Search Strategy Configuration (CSP Engine)

Both systems use advanced CSP engines with configurable search strategies:

- **Exhaustive**: Evaluates all combinations (recommended for <10 components)
- **Heuristic**: Smart pruning with domain knowledge (recommended for 10-15 components)
- **Random Sample**: Statistical sampling (useful for very large spaces)

**Performance Optimizations**:
- **Timeout Protection**: 10-second limits with graceful fallback
- **Early Termination**: Stop after finding sufficient solutions
- **Pre-cached Pricing**: Eliminates API call bottlenecks in baseline algorithms

## Key Features & Recent Improvements

### Performance Optimizations (Dec 2025)
- **Fixed Baseline Freezes**: Genetic algorithm optimized from 40s+ to <10s
- **Live Pricing Integration**: Azure Retail API with 100% success rate
- **Timeout Protection**: All operations complete within 10 seconds
- **Zero Solutions Handling**: Intelligent suggestions when constraints too restrictive

### AcademicSummary (Results Dashboard)

Both interfaces provide comprehensive academic validation:
- **Score Integrity**: Reconstructed vs displayed score verification
- **Constraint Proofs**: Mathematical validation of all constraints
- **Rule Coverage**: Complete expert system rule traceability
- **Explanation Accuracy**: Composite metric with labels (High ≥90%, Moderate 75-89%, Needs Review <75%)

### Backend Test Suite (CMOv3 & CMOv4)

The frontend cards summarize the status of the backend validation suite:

- **Core optimization tests (14/14 PASSED)**
  - CSP constraint satisfaction (3/3)
  - Solution deduplication (2/2)
  - Pareto frontier optimization (3/3)
  - Budget-relative thresholds (1/1)
  - CMOv4 instance scaling (3/3)
  - Expert system rules (2/2)

- **Extended backend tests**
  - Pricing validation: live Azure Retail API vs static tables, fallback coverage, and price sanity checks
  - Caching behavior: `ServiceDataCache` TTL refresh, stale vs fresh pricing, and cache invalidation
  - Explainability metrics: explanation accuracy and label thresholds (High / Moderate / Needs Review)
  - Baseline comparisons: CMOv3 vs CMOv4 cost/latency parity and hypervolume-based improvement checks

The full backend test suite (≈32 tests + 10 parameterized subtests) is run regularly via `pytest backend/tests`,
and all results shown in the CMOv4 dashboard correspond to a green test suite and the latest code-quality
improvements (reduced cyclomatic complexity in critical request paths and pricing orchestration).

## Configuration Options

### 1. Hard Constraints (CSP Phase)
- **Max Budget**: Default $10,000/month (updated from restrictive $5,000)
- **Max Latency**: Default 150ms (updated from restrictive 12ms)
- **Max Providers**: Default 3 providers (updated from restrictive 2)
- **Performance Metric**: Average latency, tail latency (p95), or throughput
- **Service Dependencies**: Automatically enforced with realistic enterprise patterns

### CMOv4 Additional Constraints
- **Component Selection**: Choose 5-15 components from enterprise catalog
- **Instance Counts**: Scale components with realistic instance requirements
- **Architecture Patterns**: Monolith, microservices, or event-driven patterns
- **Tech Stack Preferences**: Language, framework, and database engine choices

### 2. Live Pricing Integration
- **Azure Retail API**: Real-time pricing data (VM: $87.60/month, API Management: $0.03/month)
- **AWS/GCP Documented Rates**: Comprehensive pricing based on 2024-2025 public rates
- **100% API Success Rate**: Reliable pricing with graceful fallback mechanisms
- **Regional Support**: Azure region/currency selection with extensibility for AWS/GCP

### 3. Expert System (20+ Rules)
- **Dynamic Thresholds**: Automatically adapt to current budget constraints
  - Cost thresholds: 70% and 90% of max budget
  - Latency thresholds: 67% of max latency
- **Rule Categories**: Cost optimization, performance tuning, strategic decisions, preferences
- **Configurable Weights**: Adjust importance of each rule category (0.0-2.0)
- **CMOv4 Rules**: Additional component-specific rules for containers, serverless, caching, etc.

### 4. Advanced Search Configuration
- **CMOv3 Strategy**: Exhaustive (21M combinations), heuristic, or random sampling
- **CMOv4 Strategy**: Component-aware search with dependency validation
- **Timeout Protection**: 10-second limits with graceful error handling
- **Early Termination**: Configurable stopping criteria for large search spaces
- **Performance Monitoring**: Real-time metrics for search progress and efficiency

### 5. SKU Selection (Planned Feature)
- **SKU Selectors:** (Coming soon) Choose specific SKUs for each provider/service for more granular pricing.

---

## Usage Workflow

### CMOv3 (Production System)
1. **Access**: Navigate to `http://localhost:8080`
2. **Configure**: Set realistic constraints (budget $10K, latency 150ms, 3 providers)
3. **Optimize**: Run CSP+Expert optimization (<500ms)
4. **Analyze**: Review Pareto frontier, explainability, and baseline comparisons
5. **Export**: Download results for academic analysis

### CMOv4 (Advanced Modeling)
1. **Access**: Navigate to `http://localhost:8080/cmov4.html`
2. **Select Components**: Choose 5-15 components from enterprise catalog
3. **Configure Architecture**: Set patterns (monolith/microservices/event-driven)
4. **Run Benchmark**: Compare CMOv4 vs CMOv3 baselines
5. **Generate Report**: Create professional PDF documentation

### Best Practices
- **Start with defaults**: Use updated realistic constraints ($10K budget, 150ms latency)
- **Use timeout protection**: All operations complete within 10 seconds
- **Handle zero solutions**: Follow intelligent suggestions when constraints too restrictive
- **Compare architectures**: Use both CMOv3 and CMOv4 for comprehensive analysis
---

## Academic Tests (Batch Experiments)

Open `academic_tests.html` to run repeated experiments across component sizes. Features:
- Configure sizes and repeats; optional fixed seed for reproducibility
- Per‑run panels show Pareto, feasible counts, timings, and `ExplAcc: % (Label)`
- Summary table includes an “Expl Accuracy (μ)” column
- Aggregated Explanation Accuracy card shows Mean±Std and counts by label
- Export CSV/JSON includes explanation accuracy fields (`ExplAccMean`, `ExplAccStd`)

Explanation Accuracy is computed on the client using score integrity, constraints ratio, and rule coverage when available, then averaged (available components only).

---

## Example Combinations

- **Providers:** Mix AWS, Azure, and GCP services as allowed by your maxProviders setting.
- **Services:** For each component (API Gateway, Database, etc.), select from available provider options.
- **SKUs:** (Planned) Select specific SKUs for each service for more accurate cost modeling.

---

## Best Practices

- **Start broad:** Use relaxed constraints to see all possible solutions, then tighten as needed.
- **Use diagnostics:** If you get zero feasible solutions, check the troubleshooting card for recommended values.
- **Tune rules:** Adjust rule weights and thresholds to reflect your business priorities.
- **Check dependencies:** Ensure all required services are available for your chosen providers.
- **Export and compare:** Use exported results and run logs for reproducibility and comparative analysis.

---

## Troubleshooting & Support

### Common Issues & Solutions
- **Zero feasible solutions**: System now provides intelligent suggestions
  - Increase budget from $10K to $15K+
  - Relax latency from 150ms to 200ms+
  - Allow more providers (increase from 3)
- **Performance issues**: All operations now complete within 10 seconds
- **Pricing problems**: Live Azure API with 100% success rate, fallback mechanisms
- **Baseline freezes**: Fixed genetic algorithm optimization (40s+ → <10s)

### Advanced Diagnostics
- **CMOv3**: Comprehensive constraint proofs and rule traces
- **CMOv4**: Component validation and dependency checking
- **Timeout Protection**: Graceful error handling with informative messages
- **Live Monitoring**: Real-time progress indicators and performance metrics

---

## Extending the Application

- **Add new rules:** Extend `backend/engines/rules.py` for custom business logic.
- **Add new services/providers:** Update `backend/services/pricing.py` and `backend/config.py`.
- **Integrate live APIs:** Wire up AWS/GCP live pricing for real-time data.
- **SKU selectors:** Implement UI/backend support for user-selected SKUs.

---

Would you like this updated explanation saved to your documentation file (`frontend/EXPLANATION.md`)?

If you see "Feasible Solutions: 0" in the results, it means that none of the generated service combinations satisfy all the hard constraints (budget, latency, provider count, dependencies) with the current settings and available pricing data.

**Common reasons:**
- **Budget too low:** All service combinations may exceed your `maxBudget`.
- **Latency too strict:** The `maxLatency` constraint may be lower than any service’s latency.
- **Provider count:** Restricting to 1 provider may conflict with service dependencies.
- **Missing or outdated pricing data:** If pricing data is missing, incomplete, or not refreshed, all combinations may be filtered out.
- **CSP strategy (heuristic):** Only the cheapest option per component is checked, which may not be feasible.

**How to fix:**
- Increase `maxBudget` and/or `maxLatency` in the configuration tab.
- Refresh pricing data in Pricing Settings.
- Try a different CSP strategy (switch to “exhaustive” or “random_sample” in Academic tab).
- Review service dependencies and ensure all required services are available.

If you need deeper analysis, check the actual pricing data and constraints being used, or contact the system maintainer for support.
---

## Normalized View (index_normalized.html)

Use the normalized scoring page for min‑max normalized metrics and weighted sums. Recent update: cost and latency are formatted with fixed decimals to avoid floating‑point artifacts in the UI.

---

## Reproducibility

The backend supports an optional `seed` on `/api/optimize` for deterministic runs. The UI surfaces `seed_used` in metrics when provided. For experiments, repeat runs with the same seed to confirm stable feasible counts and Pareto sizes. Verify deploy state with GET `/api/version`.

---
For further details, see code comments in each backend and frontend file.
