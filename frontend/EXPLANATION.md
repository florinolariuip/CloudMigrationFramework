## Search Strategy Configuration (CSP Search Algorithm)

The optimizer uses a Constraint Satisfaction Problem (CSP) engine to generate and filter all possible service combinations. You can configure how the search algorithm works in the Academic tab:

- **Search Strategy:**
  - **Exhaustive:** Evaluates every possible combination. Guarantees finding all feasible solutions, but can be slow for large search spaces.
  - **Heuristic:** Uses smart shortcuts to prune the search space, checking only the cheapest or most promising options per component. Much faster, but may miss some feasible solutions.
  - **Random Sample:** Evaluates a random subset of all possible combinations. Useful for very large search spaces where exhaustive search is impractical.

- **Sample Size:**
  - When using "Random Sample," you can set how many random combinations to evaluate. Larger sample sizes increase accuracy but take longer.

- **Early Termination:**
  - Optionally stop the search early after a set number of feasible solutions are found. Useful for quick prototyping or when only a few good solutions are needed.

**Best Practices:**
- Use "Exhaustive" for small problems or when you need all possible solutions.
- Use "Heuristic" or "Random Sample" for large problems to save time.
- Adjust sample size and early termination settings to balance speed and thoroughness.

All these settings are available in the Academic tab and can be tuned for your scenario or research needs.

# Cloud Migration Optimizer: Complete Usage & Configuration Guide

## What Can You Configure?

### 1. Hard Constraints (CSP Phase)
- **Max Budget ($/month):** Set the maximum monthly cost for your migration solution.
- **Max Latency (ms):** Set the strictest allowed average or tail latency for all services.
- **Max Providers:** Limit the number of cloud providers (e.g., 1, 2, or 3).
- **Performance Metric:** Choose between average latency, tail latency (p95), or throughput.
- **Service Dependencies:** Automatically enforced (e.g., AWS RDS requires AWS EC2).

### 2. Pricing & Region
- **Azure Region & Currency:** Select region/currency for live Azure pricing. (Extendable for AWS/GCP.)
- **Pricing Source Diagnostics:** See whether prices are fetched live (API) or fallback.

### 3. Expert System (Rule-Based Scoring)
- **Rule Thresholds & Bonuses:** Configure every scoring rule:
  - Preferred provider bonus (e.g., AWS, Azure, GCP)
  - Low cost reward (e.g., +12 points for <$2000)
  - Cost priority bonus
  - Performance priority bonus
  - Penalties for high/moderate cost or poor latency
  - Bonus for single-provider solutions
- **Rule Weights:** Adjust the importance of cost, performance, strategic, and preference rules (0.0–2.0).
- **All rule values and weights are configurable in the Academic tab.**

### 4. CSP Search Strategy
- **Strategy:** Choose exhaustive, heuristic, or random_sample search.
- **Sample Size:** For random sampling, set the number of samples.
- **Early Termination:** Optionally enable early stopping for large search spaces.

### 5. SKU Selection (Planned Feature)
- **SKU Selectors:** (Coming soon) Choose specific SKUs for each provider/service for more granular pricing.

---

## How to Use Efficiently

1. **Set Constraints:** Start with realistic budget, latency, and provider limits. Use the configuration tab.
2. **Select Pricing Region/Currency:** For accurate pricing, set Azure region/currency. Extend for AWS/GCP as needed.
3. **Tune Scoring Rules:** In the Academic tab, adjust rule thresholds and weights to match your business or research goals.
4. **Choose Search Strategy:** For small problems, use exhaustive. For large ones, try heuristic or random_sample.
5. **Run Optimization:** Click "Run Optimizer" to generate, filter, and score all possible service combinations.
6. **Review Diagnostics:** Use the troubleshooting card and source diagnostics to understand why solutions may be filtered out.
7. **Export Results:** Download results and run logs for further analysis or reporting.
8. **Iterate:** Adjust constraints, rules, or strategy and rerun to explore alternatives.

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

## Troubleshooting

- **Zero feasible solutions:** Increase budget/latency, allow more providers, or relax constraints.
- **Pricing issues:** Refresh pricing data or check region/currency settings.
- **Rule impact:** Use the Academic tab to see and adjust how each rule affects scoring.

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
For further details, see code comments in each backend and frontend file.
