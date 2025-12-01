from __future__ import annotations

# --- Defaults and Academic Configuration ---
DEFAULT_CONSTRAINTS = {
    "maxBudget": 5000,
    "maxLatency": 150,
    "maxProviders": 3,
    # Performance metric used by CSP feasibility check
    "performanceMetric": "avg_latency",  # avg_latency | tail_latency | throughput
}

# Pricing configuration (can be exposed via API)
DEFAULT_PRICING = {
    "aws_region": "us-east-1",     # us-east-1, us-west-2, eu-west-1, ap-southeast-1
    "azure_region": "westeurope",
    "gcp_region": "us-central1",   # us-central1, us-west1, europe-west1, asia-southeast1
    "currency": "USD",
}

# Service interdependency rules
SERVICE_DEPENDENCIES = [
    # Simplified dependencies to allow more feasible solutions for 18-component optimization
    # Original dependency (kept simple)
    {"if": "AWS RDS", "requires": "AWS EC2"},
    
    # Note: Many enterprise dependencies are optional in cloud architectures
    # Commenting out strict dependencies to allow feasible solutions
    # The expert system will still reward good architectural patterns via rules
]

# Expert System Rule Parameters
EXPERT_RULES_CONFIG = {
    # Main cost/latency rules (adjusted for $5k budget, 150ms latency)
    "cost_high_threshold": 4000,
    "cost_high_penalty": -25,
    "cost_moderate_threshold": 3000,
    "cost_moderate_penalty": -20,
    "cost_low_threshold": 2000,
    "cost_low_reward": 12,
    "latency_excellent_threshold": 80,
    "latency_excellent_reward": 15,
    "latency_poor_threshold": 120,
    "latency_poor_penalty": -10,
    "single_provider_bonus": 10,
    "preferred_provider_bonus": 8,
    "cost_priority_threshold": 3500,
    "cost_priority_bonus": 5,
    "performance_priority_threshold": 100,
    "performance_priority_bonus": 5,
    
    # Component-specific rules (updated for 18-component support)
    "cache_latency_threshold": 60.0,
    "cache_latency_reward": 8,
    "cdn_latency_threshold": 70.0,
    "cdn_latency_reward": 6,
    "monitoring_cost_threshold": 3750,
    "monitoring_cost_penalty": -8,
    "backup_cost_threshold": 4250,
    "backup_cost_reward": 7,
    "container_cost_threshold": 4000,
    "container_latency_threshold": 90.0,
    "container_balance_reward": 10,
    "serverless_latency_threshold": 75.0,
    "serverless_efficiency_reward": 7,
    "message_queue_cost_threshold": 3250,
    "message_queue_reliability_reward": 6,
    "load_balancer_cost_threshold": 3500,
    "load_balancer_availability_reward": 8,
    "encryption_compliance_reward": 9,
    "nosql_cost_threshold": 3000,
    "nosql_performance_reward": 8,
    "event_streaming_latency_threshold": 50.0,
    "event_streaming_reward": 10,
    "iot_cost_threshold": 2500,
    "iot_efficiency_reward": 7,
    
    # Multi-cloud operational rules
    "multi_cloud_penalty": -5,  # Penalty per additional provider
    "colocation_latency_threshold": 12.0,  # Good latency indicating regional co-location
    "colocation_bonus": 8,  # Reward for good multi-cloud latency
    "diversification_reward": 6,  # Reward for 2-provider risk diversification
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
