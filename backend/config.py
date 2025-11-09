from __future__ import annotations

# --- Defaults and Academic Configuration ---
DEFAULT_CONSTRAINTS = {
    "maxBudget": 5000,
    "maxLatency": 12,
    "maxProviders": 2,
    # Performance metric used by CSP feasibility check
    "performanceMetric": "avg_latency",  # avg_latency | tail_latency | throughput
}

# Pricing configuration (can be exposed via API)
DEFAULT_PRICING = {
    "azure_region": "westeurope",
    "currency": "USD",
}

# Service interdependency rules
SERVICE_DEPENDENCIES = [
    # Simplified dependencies to allow more feasible solutions for 15-component optimization
    # Original dependency (kept simple)
    {"if": "AWS RDS", "requires": "AWS EC2"},
    
    # Note: Many enterprise dependencies are optional in cloud architectures
    # Commenting out strict dependencies to allow feasible solutions
    # The expert system will still reward good architectural patterns via rules
]

# Expert System Rule Parameters
EXPERT_RULES_CONFIG = {
    "cost_high_threshold": 2800,
    "cost_high_penalty": -25,
    "cost_moderate_threshold": 2500,
    "cost_moderate_penalty": -20,
    "cost_low_threshold": 2000,
    "cost_low_reward": 12,
    "latency_excellent_threshold": 10,
    "latency_excellent_reward": 15,
    "latency_poor_threshold": 11.5,
    "latency_poor_penalty": -10,
    "single_provider_bonus": 10,
    "preferred_provider_bonus": 8,
    "cost_priority_threshold": 2600,
    "cost_priority_bonus": 5,
    "performance_priority_threshold": 10.5,
    "performance_priority_bonus": 5,
}

# Scoring Weights
SCORING_WEIGHTS = {
    "cost_weight": 1.0,
    "performance_weight": 1.0,
    "strategic_weight": 1.0,
    "preference_weight": 1.0,
}

# CSP Search Strategy
CSP_CONFIG = {
    "search_strategy": "heuristic",  # exhaustive | heuristic | random_sample | ml
    "sample_size": 100,
    "enable_early_termination": False,
    "early_termination_count": 100,
}
