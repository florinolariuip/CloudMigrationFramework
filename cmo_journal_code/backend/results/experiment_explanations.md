# Experiment Explanations

This file is dynamically generated to provide explanations for experiment results, figures, and tables. It is updated each time experiments are run.

---

### Pricing Data Sources
🔸 **AWS**: [Public Pricing API](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json)
🔸 **Azure**: [Retail Prices API](https://prices.azure.com/api/retail/prices)
🔸 **GCP**: [Public Pricing API](https://cloud.google.com/skus/)

---
## Pareto Frontier (NSGA-II)
- Number of Pareto-optimal solutions: **20**.
- Minimum cost found: **$676.37**.
- Minimum latency found: **9.00 ms**.
- Each point represents a trade-off between cost and latency where no other solution is strictly better in both.

## Hypervolume Trend
- **NSGA2** mean hypervolume: **nan**
- **MOEAD** mean hypervolume: **nan**
- **BASELINES** mean hypervolume: **nan**
Higher hypervolume indicates better coverage of the Pareto frontier (more diverse and optimal solutions).

## Baseline Algorithms
- **Random Selection**: Cost = $2097.99, Latency = 9.533333333333331 ms, Success = True
- **Greedy-Cost**: Cost = $577.73, Latency = 9.4 ms, Success = True
- **Greedy-Latency**: Cost = $676.37, Latency = 9.0 ms, Success = True
- **Genetic Algorithm**: Cost = $638.41, Latency = 9.133333333333333 ms, Success = True
- **Weighted Sum**: Cost = $624.1, Latency = 9.0 ms, Success = True
Baselines provide reference points for evaluating the optimizer. Lower cost/latency and higher success indicate better performance.

---
These explanations are generated based on the latest experiment results. For more details, see the documentation and code comments.