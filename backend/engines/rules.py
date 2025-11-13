from __future__ import annotations

from typing import List, Dict, Any, Optional

from backend.models import Preferences, Solution
from backend.config import EXPERT_RULES_CONFIG, SCORING_WEIGHTS

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
    def __init__(self, preferences, rules_config, weights):
        super().__init__()
        self.preferences = preferences
        self.rules_config = rules_config
        self.weights = weights
        self.final_score = 100
        self.evaluation_log = []

    @Rule(SolutionFact(cost=MATCH.cost))
    def high_cost_penalty(self, cost):
        if cost > self.rules_config["cost_high_threshold"]:
            impact = self.rules_config["cost_high_penalty"] * self.weights["cost_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"High cost penalty (>${self.rules_config['cost_high_threshold']})",
                "impact": round(impact, 1),
                "weight": self.weights["cost_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def moderate_cost_penalty(self, cost):
        if cost > self.rules_config["cost_moderate_threshold"] and cost <= self.rules_config["cost_high_threshold"]:
            impact = self.rules_config["cost_moderate_penalty"] * self.weights["cost_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Moderate cost penalty (>${self.rules_config['cost_moderate_threshold']})",
                "impact": round(impact, 1),
                "weight": self.weights["cost_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def low_cost_reward(self, cost):
        if cost < self.rules_config["cost_low_threshold"]:
            impact = self.rules_config["cost_low_reward"] * self.weights["cost_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": f"Low cost reward (<${self.rules_config['cost_low_threshold']})",
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
        if latency < 8.0:  # Cache typically reduces latency significantly
            impact = 8 * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Caching performance boost (<8ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(latency=MATCH.latency))
    def cdn_latency_reduction(self, latency):
        """Reward CDN usage for content delivery optimization"""
        if latency < 9.0:  # CDN edge locations reduce latency
            impact = 6 * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "CDN latency reduction (<9ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def monitoring_overhead_penalty(self, cost):
        """Penalize excessive monitoring costs"""
        if cost > 2700:  # Monitoring adds operational costs
            impact = -8 * self.weights["cost_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Monitoring overhead penalty (>$2700)",
                "impact": round(impact, 1),
                "weight": self.weights["cost_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def backup_redundancy_reward(self, cost):
        """Reward solutions with backup services for data protection"""
        if cost < 2900:  # Backup services with reasonable cost
            impact = 7 * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Backup redundancy reward (<$2900)",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(providers=MATCH.providers))
    def encryption_compliance_bonus(self, providers):
        """Reward encryption services for security compliance"""
        impact = 9 * self.weights["strategic_weight"]
        self.final_score += impact
        self.evaluation_log.append({
            "rule": "Encryption compliance bonus",
            "impact": round(impact, 1),
            "weight": self.weights["strategic_weight"],
        })

    @Rule(SolutionFact(cost=MATCH.cost, latency=MATCH.latency))
    def container_orchestration_balance(self, cost, latency):
        """Reward container solutions with balanced cost/performance"""
        if cost < 2800 and latency < 10.5:
            impact = 10 * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Container orchestration balance (<$2800, <10.5ms)",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(latency=MATCH.latency))
    def serverless_efficiency(self, latency):
        """Reward serverless compute for efficiency and scalability"""
        if latency < 9.5:
            impact = 7 * self.weights["performance_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Serverless efficiency (<9.5ms)",
                "impact": round(impact, 1),
                "weight": self.weights["performance_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def message_queue_reliability(self, cost):
        """Reward message queue inclusion for decoupled architecture"""
        if cost < 2600:
            impact = 6 * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Message queue reliability (<$2600)",
                "impact": round(impact, 1),
                "weight": self.weights["strategic_weight"],
            })

    @Rule(SolutionFact(cost=MATCH.cost))
    def load_balancer_availability(self, cost):
        """Reward load balancer for high availability"""
        if cost < 2750:
            impact = 8 * self.weights["strategic_weight"]
            self.final_score += impact
            self.evaluation_log.append({
                "rule": "Load balancer availability (<$2750)",
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
    return max(dist.keys(), key=lambda k: dist[k])



def evaluate_solutions(solutions: List[Solution], preferences: Preferences) -> List[Solution]:
    rules_config = EXPERT_RULES_CONFIG
    weights = SCORING_WEIGHTS
    ranked = []
    for sol in solutions:
        main_provider = get_main_provider(sol.configuration)
        engine = SolutionScoringEngine(preferences, rules_config, weights)
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
        sol.score = max(0, min(150, engine.final_score))
        sol.evaluationLog = engine.evaluation_log
        ranked.append(sol)
    ranked.sort(key=lambda s: s.score or 0, reverse=True)
    return ranked

# --- Normalization-based scoring ---
def min_max_normalize(values):
    min_v, max_v = min(values), max(values)
    return [(v - min_v) / (max_v - min_v) if max_v > min_v else 0.0 for v in values], min_v, max_v

def evaluate_solutions_normalized(solutions: List[Solution], weights=None):
    if not solutions:
        return [], {}
    if weights is None:
        weights = {"cost": 0.5, "latency": 0.3, "reliability": 0.2}
    costs = [float(s.cost) for s in solutions]
    latencies = [float(s.latency) for s in solutions]
    # For demo, use reliability as 0.95 for all (or add to Solution)
    reliabilities = [getattr(s, "reliability", 0.95) for s in solutions]
    norm_cost, cost_min, cost_max = min_max_normalize(costs)
    norm_latency, latency_min, latency_max = min_max_normalize(latencies)
    norm_reliability, reliability_min, reliability_max = min_max_normalize(reliabilities)
    for i, sol in enumerate(solutions):
        sol.norm_cost = norm_cost[i]
        sol.norm_latency = norm_latency[i]
        sol.norm_reliability = norm_reliability[i]
        # For cost/latency, lower is better; reliability, higher is better
        sol.score = (
            weights["cost"] * (1 - norm_cost[i]) +
            weights["latency"] * (1 - norm_latency[i]) +
            weights["reliability"] * norm_reliability[i]
        )
    solutions.sort(key=lambda s: s.score, reverse=True)
    normalization = {
        "cost_min": cost_min,
        "cost_max": cost_max,
        "latency_min": latency_min,
        "latency_max": latency_max,
        "reliability_min": reliability_min,
        "reliability_max": reliability_max,
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
