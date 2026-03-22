from __future__ import annotations

from typing import List, Dict, Any, Optional

from backend.models import Preferences, Solution
from backend.config import EXPERT_RULES_CONFIG, SCORING_WEIGHTS

# Regional mapping for cross-cloud latency optimization
REGIONAL_MAPPING = {
    'AWS': {'us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'},
    'Azure': {'East US', 'West US 2', 'West Europe', 'Southeast Asia'},
    'GCP': {'us-east1', 'us-west1', 'europe-west1', 'asia-southeast1'}
}

def estimate_cross_cloud_latency(config: Dict[str, str]) -> float:
    """Estimate cross-cloud latency based on service distribution"""
    providers = {s.split(" ")[0] for s in config.values()}
    if len(providers) <= 1:
        return 0.0
    
    # Base cross-cloud latencies (ms) - can be reduced with regional co-location
    base_latencies = {
        ('AWS', 'Azure'): 8.0,
        ('AWS', 'GCP'): 10.0,
        ('Azure', 'GCP'): 12.0
    }
    
    total_penalty = 0.0
    provider_list = list(providers)
    for i in range(len(provider_list)):
        for j in range(i + 1, len(provider_list)):
            pair = tuple(sorted([provider_list[i], provider_list[j]]))
            total_penalty += base_latencies.get(pair, 15.0)
    
    return total_penalty / len(providers) if providers else 0.0

# Experta-based expert system
from experta import KnowledgeEngine, Fact, Rule, Field, MATCH


class SolutionFact(Fact):
    cost = Field(float)
    latency = Field(float)
    providers = Field(int)
    main_provider = Field(str)
    preferences = Field(object)
    score = Field(float, default=100)
    evaluation_log = Field(list, default=[])

class SolutionScoringEngine(KnowledgeEngine):
    def __init__(self, preferences, rules_config, weights, max_budget=None):
        super().__init__()
        self.preferences = preferences
        self.rules_config = rules_config
        self.weights = weights
        self.max_budget = max_budget
        self.final_score = 100
        self.evaluation_log = []

    @Rule(SolutionFact(cost=MATCH.cost))
    def high_cost_penalty(self, cost):
        # If max_budget is provided, use it to calculate threshold (90% of budget)
        # Otherwise, use the configured absolute threshold
        threshold = (
            self.max_budget * 0.90 if self.max_budget 
            else self.rules_config["cost_high_threshold"]
        )
        if cost > threshold:
            impact = self.rules_config["cost_high_penalty"] * self.weights["cost_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"High cost penalty (>${threshold:.0f})",
                "impact": round(impact, 1),
                "weight": self.weights["cost_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def moderate_cost_penalty(self, cost):
        # Use budget-relative thresholds if available
        high_threshold = (
            self.max_budget * 0.80 if self.max_budget 
            else self.rules_config["cost_high_threshold"]
        )
        moderate_threshold = (
            self.max_budget * 0.60 if self.max_budget 
            else self.rules_config["cost_moderate_threshold"]
        )
        if cost > moderate_threshold and cost <= high_threshold:
            impact = self.rules_config["cost_moderate_penalty"] * self.weights["cost_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Moderate cost penalty (>${moderate_threshold:.0f})",
                "impact": round(impact, 1),
                "weight": self.weights["cost_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def low_cost_reward(self, cost):
        # Use budget-relative threshold if available (40% of budget)
        threshold = (
            self.max_budget * 0.40 if self.max_budget 
            else self.rules_config["cost_low_threshold"]
        )
        if cost < threshold:
            impact = self.rules_config["cost_low_reward"] * self.weights["cost_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Low cost reward (<${threshold:.0f})",
                "impact": round(impact, 1),
                "weight": self.weights["cost_weight"],
            })

    @Rule(SolutionFact(latency=MATCH.latency))
    def excellent_performance(self, latency):
        if latency < self.rules_config["latency_excellent_threshold"]:
            impact = self.rules_config["latency_excellent_reward"] * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Excellent performance (<{self.rules_config['latency_excellent_threshold']}ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(latency=MATCH.latency))
    def poor_performance(self, latency):
        if latency > self.rules_config["latency_poor_threshold"]:
            impact = self.rules_config["latency_poor_penalty"] * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Poor performance (>{self.rules_config['latency_poor_threshold']}ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(providers=MATCH.providers))
    def single_provider_bonus(self, providers):
        if providers == 1:
            impact = self.rules_config["single_provider_bonus"] * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Single provider consistency",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(main_provider=MATCH.main_provider))
    def preferred_provider_bonus(self, main_provider):
        if self.preferences.preferredProvider and main_provider == self.preferences.preferredProvider:
            impact = self.rules_config["preferred_provider_bonus"] * self.weights["preference_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Preferred provider bonus ({main_provider})",
                "impact": round(impact, 1),
                "weight": self.weights["preference_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def cost_priority_alignment(self, cost):
        if self.preferences.prioritizeCost and cost < self.rules_config["cost_priority_threshold"]:
            impact = self.rules_config["cost_priority_bonus"] * self.weights["preference_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Cost priority alignment",
                "impact": round(impact, 1),
                "weight": self.weights["preference_weight"],
            })

    @Rule(SolutionFact(latency=MATCH.latency))
    def performance_priority_alignment(self, latency):
        if self.preferences.prioritizePerformance and latency < self.rules_config["performance_priority_threshold"]:
            impact = self.rules_config["performance_priority_bonus"] * self.weights["preference_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Performance priority alignment",
                "impact": round(impact, 1),
                "weight": self.weights["preference_weight"],
            })

    # --- Priority 4: Expert rules for new components (cache, CDN, monitoring, containers, etc.) ---
    
    @Rule(SolutionFact(latency=MATCH.latency))
    def caching_performance_boost(self, latency):
        """Reward solutions with cache components that achieve low latency"""
        threshold = self.rules_config.get("cache_latency_threshold", 8.0)
        reward = self.rules_config.get("cache_latency_reward", 8)
        if latency < threshold:
            impact = reward * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Caching performance boost (<{threshold:g}ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(latency=MATCH.latency))
    def cdn_latency_reduction(self, latency):
        """Reward CDN usage for content delivery optimization"""
        threshold = self.rules_config.get("cdn_latency_threshold", 9.0)
        reward = self.rules_config.get("cdn_latency_reward", 6)
        if latency < threshold:
            impact = reward * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"CDN latency reduction (<{threshold:g}ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def monitoring_overhead_penalty(self, cost):
        """Penalize excessive monitoring costs"""
        threshold = self.rules_config.get("monitoring_cost_threshold", 2700)
        penalty = self.rules_config.get("monitoring_cost_penalty", -8)
        if cost > threshold:
            impact = penalty * self.weights["cost_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Monitoring overhead penalty (>${threshold:g})",
                "impact": round(impact, 1),
                "weight": self.weights["cost_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def backup_redundancy_reward(self, cost):
        """Reward solutions with backup services for data protection"""
        threshold = self.rules_config.get("backup_cost_threshold", 2900)
        reward = self.rules_config.get("backup_cost_reward", 7)
        if cost < threshold:
            impact = reward * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Backup redundancy reward (<${threshold:g})",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(providers=MATCH.providers))
    def encryption_compliance_bonus(self, providers):
        """Reward encryption services for security compliance"""
        reward = self.rules_config.get("encryption_compliance_reward", 9)
        impact = reward * self.weights["strategic_weight"]
        self.final_score += impact
        self.evaluation_log.append({
            "rule": "Encryption compliance bonus",
            "impact": round(impact, 1),
            "weight": self.weights["strategic_weight"],
        })

    @Rule(SolutionFact(cost=MATCH.cost, latency=MATCH.latency))
    def container_orchestration_balance(self, cost, latency):
        """Reward container solutions with balanced cost/performance"""
        cost_threshold = self.rules_config.get("container_cost_threshold", 2800)
        latency_threshold = self.rules_config.get("container_latency_threshold", 10.5)
        reward = self.rules_config.get("container_balance_reward", 10)
        if cost < cost_threshold and latency < latency_threshold:
            impact = reward * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Container orchestration balance (<${cost_threshold:g}, <{latency_threshold:g}ms)",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(latency=MATCH.latency))
    def serverless_efficiency(self, latency):
        """Reward serverless compute for efficiency and scalability"""
        threshold = self.rules_config.get("serverless_latency_threshold", 9.5)
        reward = self.rules_config.get("serverless_efficiency_reward", 7)
        if latency < threshold:
            impact = reward * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Serverless efficiency (<{threshold:g}ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def message_queue_reliability(self, cost):
        """Reward message_queue for asynchronous processing reliability"""
        threshold = self.rules_config.get("message_queue_cost_threshold", 2600)
        reward = self.rules_config.get("message_queue_reliability_reward", 6)
        if cost < threshold:
            impact = reward * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Message queue reliability (<${threshold:g})",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def load_balancer_availability(self, cost):
        """Reward load balancer for high availability"""
        threshold = self.rules_config.get("load_balancer_cost_threshold", 2750)
        reward = self.rules_config.get("load_balancer_availability_reward", 8)
        if cost < threshold:
            impact = reward * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Load balancer availability (<${threshold:g})",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def nosql_performance_reward(self, cost):
        """Reward NoSQL database solutions for performance and scalability"""
        threshold = self.rules_config.get("nosql_cost_threshold", 3000)
        reward = self.rules_config.get("nosql_performance_reward", 8)
        if cost < threshold:
            impact = reward * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"NoSQL performance reward (<${threshold:g})",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(latency=MATCH.latency))
    def event_streaming_efficiency(self, latency):
        """Reward event streaming for real-time data processing"""
        threshold = self.rules_config.get("event_streaming_latency_threshold", 50.0)
        reward = self.rules_config.get("event_streaming_reward", 10)
        if latency < threshold:
            impact = reward * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Event streaming efficiency (<{threshold:g}ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def iot_platform_efficiency(self, cost):
        """Reward IoT platform solutions for device management efficiency"""
        threshold = self.rules_config.get("iot_cost_threshold", 2500)
        reward = self.rules_config.get("iot_efficiency_reward", 7)
        if cost < threshold:
            impact = reward * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"IoT platform efficiency (<${threshold:g})",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(providers=MATCH.providers))
    def multi_cloud_complexity_penalty(self, providers):
        """Penalize multi-cloud solutions for operational complexity"""
        if providers > 1:
            penalty_per_provider = self.rules_config.get("multi_cloud_penalty", -5)
            penalty = penalty_per_provider * (providers - 1)
            impact = penalty * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Multi-cloud complexity penalty ({providers} providers)",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(providers=MATCH.providers, latency=MATCH.latency))
    def regional_colocation_bonus(self, providers, latency):
        """Reward multi-cloud solutions with good latency (indicating regional co-location)"""
        if providers > 1 and latency < self.rules_config.get("colocation_latency_threshold", 12.0):
            reward = self.rules_config.get("colocation_bonus", 8)
            impact = reward * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Regional co-location bonus (<{self.rules_config.get('colocation_latency_threshold', 12.0)}ms)",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(providers=MATCH.providers))
    def vendor_diversification_reward(self, providers):
        """Reward 2-provider solutions for risk diversification without excessive complexity"""
        if providers == 2:
            reward = self.rules_config.get("diversification_reward", 6)
            impact = reward * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Vendor diversification reward (2 providers)",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })


def provider_distribution(config: Dict[str, str]) -> Dict[str, int]:
    dist: Dict[str, int] = {}
    for s in config.values():
        p = s.split(" ")[0]
        dist[p] = dist.get(p, 0) + 1
    return dist


def get_main_provider(config: Dict[str, str]) -> str:
    dist = provider_distribution(config)
    return max(dist.keys(), key=lambda k: dist[k]) if dist else "Unknown"

def calculate_operational_complexity_score(config: Dict[str, str]) -> float:
    """Calculate operational complexity score (0-1, lower is more complex)"""
    providers = provider_distribution(config)
    num_providers = len(providers)
    
    if num_providers == 1:
        return 1.0  # Lowest complexity
    elif num_providers == 2:
        return 0.7  # Moderate complexity
    else:
        return 0.4  # High complexity

def estimate_data_transfer_volume(config: Dict[str, str]) -> float:
    """Estimate monthly data transfer volume based on architecture"""
    # Simple heuristic based on service types
    base_volume = 100  # GB/month baseline
    
    # Services that typically generate high data transfer
    high_transfer_services = ['database', 'storage', 'analytics', 'cdn']
    transfer_multiplier = 1.0
    
    for component, service in config.items():
        if any(ht in component.lower() for ht in high_transfer_services):
            transfer_multiplier += 0.5
    
    return base_volume * transfer_multiplier


def deduplicate_solutions(solutions: List[Solution]) -> List[Solution]:
    """
    Remove duplicate solutions based on their service configuration.
    Two solutions are considered duplicates if they have identical configurations.
    """
    original_count = len(solutions)
    seen_configs = set()
    unique_solutions = []
    
    for sol in solutions:
        # Create a hashable representation of the configuration
        config_tuple = tuple(sorted(sol.configuration.items()))
        
        if config_tuple not in seen_configs:
            seen_configs.add(config_tuple)
            unique_solutions.append(sol)
    
    duplicates_removed = original_count - len(unique_solutions)
    if duplicates_removed > 0:
        print(f"[DEDUP] Removed {duplicates_removed} duplicate solutions (from {original_count} to {len(unique_solutions)})")
    
    return unique_solutions


def evaluate_solutions(solutions: List[Solution], preferences: Preferences, max_budget: Optional[float] = None) -> List[Solution]:
    # Note: Deduplication now happens at the API endpoint level before this function is called
    if not solutions:
        return []
    
    rules_config = EXPERT_RULES_CONFIG
    weights = SCORING_WEIGHTS
    ranked = []
    for sol in solutions:
        main_provider = get_main_provider(sol.configuration)
        engine = SolutionScoringEngine(preferences, rules_config, weights, max_budget)
        # Ensure cost is a valid float
        try:
            cost = float(sol.cost)
            if not (cost or cost == 0):
                cost = 0.0
        except Exception:
            cost = 0.0
        fact = SolutionFact(
            cost=cost,
            latency=sol.latency if sol.latency is not None else 0.0,
            providers=sol.providers if sol.providers is not None else 1,
            main_provider=main_provider,
            preferences=preferences,
        )
        engine.reset()
        engine.declare(fact)
        engine.run()
        # Preserve raw score for explanation accuracy, cap displayed score
        sol.raw_score = engine.final_score
        sol.score = max(0, min(150, engine.final_score))
        sol.evaluationLog = engine.evaluation_log
        ranked.append(sol)
    ranked.sort(key=lambda s: s.score or 0, reverse=True)
    return ranked

# --- Normalization-based scoring ---
def min_max_normalize(values):
    """Normalize values to [0, 1] range using min-max normalization."""
    # Filter out None values
    valid_values = [v for v in values if v is not None]
    if not valid_values:
        # If all values are None, return zeros
        return [0.0] * len(values), 0.0, 0.0
    min_v, max_v = min(valid_values), max(valid_values)
    # Normalize, replacing None with 0
    normalized = []
    for v in values:
        if v is None:
            normalized.append(0.0)
        elif max_v > min_v:
            normalized.append((v - min_v) / (max_v - min_v))
        else:
            normalized.append(0.0)
    return normalized, min_v, max_v


def evaluate_solutions_normalized(solutions: List[Solution], weights=None):
    """
    Evaluate solutions using min-max normalization and weighted scoring.
    Now supports multiple metrics: cost, latency, reliability, security, vendor risk, scalability.
    Note: Deduplication now happens at the API endpoint level before this function is called.
    """
    if not solutions:
        return [], {}
    
    # Default weights (can be customized by user)
    if weights is None:
        weights = {
            "cost": 0.30,
            "latency": 0.20,
            "reliability": 0.20,
            "security": 0.15,
            "vendor_risk": 0.10,  # Lower risk is better
            "scalability": 0.05
        }
    
    # Import and calculate advanced metrics
    try:
        from backend.engines.metrics import enrich_solution_with_metrics
        for sol in solutions:
            enrich_solution_with_metrics(sol)
    except ImportError:
        # Fallback if metrics module not available
        for sol in solutions:
            sol.reliability = 0.95
            sol.security_score = 0.90
            sol.vendor_lockin_risk = 0.3 if sol.providers == 1 else 0.1
            sol.scalability_score = 0.80
    
    # Extract values for normalization
    costs = [float(s.cost) for s in solutions]
    latencies = [float(s.latency) for s in solutions]
    reliabilities = [float(s.reliability) if s.reliability else 0.95 for s in solutions]
    securities = [float(s.security_score) if s.security_score else 0.90 for s in solutions]
    vendor_risks = [float(s.vendor_lockin_risk) if s.vendor_lockin_risk else 0.5 for s in solutions]
    scalabilities = [float(s.scalability_score) if s.scalability_score else 0.80 for s in solutions]
    
    # Normalize all metrics
    norm_cost, cost_min, cost_max = min_max_normalize(costs)
    norm_latency, latency_min, latency_max = min_max_normalize(latencies)
    norm_reliability, reliability_min, reliability_max = min_max_normalize(reliabilities)
    norm_security, security_min, security_max = min_max_normalize(securities)
    norm_vendor_risk, vendor_risk_min, vendor_risk_max = min_max_normalize(vendor_risks)
    norm_scalability, scalability_min, scalability_max = min_max_normalize(scalabilities)
    
    # Calculate weighted scores
    for i, sol in enumerate(solutions):
        sol.norm_cost = norm_cost[i]
        sol.norm_latency = norm_latency[i]
        sol.norm_reliability = norm_reliability[i]
        sol.norm_security = norm_security[i]
        sol.norm_vendor_risk = norm_vendor_risk[i]
        sol.norm_scalability = norm_scalability[i]
        
        # Calculate final score
        # For cost, latency, vendor_risk: lower is better (use 1 - norm)
        # For reliability, security, scalability: higher is better (use norm)
        sol.score = (
            weights.get("cost", 0.30) * (1 - norm_cost[i]) +
            weights.get("latency", 0.20) * (1 - norm_latency[i]) +
            weights.get("reliability", 0.20) * norm_reliability[i] +
            weights.get("security", 0.15) * norm_security[i] +
            weights.get("vendor_risk", 0.10) * (1 - norm_vendor_risk[i]) +
            weights.get("scalability", 0.05) * norm_scalability[i]
        )
    
    solutions.sort(key=lambda s: s.score, reverse=True)
    
    normalization = {
        "cost_min": cost_min,
        "cost_max": cost_max,
        "latency_min": latency_min,
        "latency_max": latency_max,
        "reliability_min": reliability_min,
        "reliability_max": reliability_max,
        "security_min": security_min,
        "security_max": security_max,
        "vendor_risk_min": vendor_risk_min,
        "vendor_risk_max": vendor_risk_max,
        "scalability_min": scalability_min,
        "scalability_max": scalability_max,
        "weights": weights
    }
    
    return solutions, normalization


def calculate_statistics(solutions: List[Solution]) -> Optional[Dict[str, Any]]:
    if not solutions:
        return None

    costs = [s.cost for s in solutions]
    lats = [s.latency for s in solutions]
    scores = [s.score or 0 for s in solutions]

    return {
        "cost": {"min": min(costs), "max": max(costs), "avg": round(sum(costs) / len(costs), 2)},
        "latency": {"min": round(min(lats), 1), "max": round(max(lats), 1), "avg": round(sum(lats) / len(lats), 1)},
        "score": {"min": min(scores), "max": max(scores), "avg": round(sum(scores) / len(scores), 1)},
    }
