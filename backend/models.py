from __future__ import annotations


from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class Constraints:
    maxBudget: int
    maxLatency: float
    maxProviders: int
    selected_components: Optional[List[str]] = None  # List of selected architecture components


@dataclass(frozen=True)
class Preferences:
    preferredProvider: Optional[str] = None
    prioritizeCost: bool = False
    prioritizePerformance: bool = False


@dataclass
class Solution:
    configuration: Dict[str, str]
    cost: int
    latency: float
    providers: int
    providerDistribution: Dict[str, int]
    score: Optional[float] = None  # Changed from int to float for normalization support
    raw_score: Optional[float] = None  # Uncapped score for explanation accuracy validation
    evaluationLog: Optional[List[Dict[str, Any]]] = None
    # Explainability fields (Priority 3 enhancement)
    constraintProof: Optional[List[Dict[str, Any]]] = None  # Constraint satisfaction evidence
    ruleTrace: Optional[List[Dict[str, Any]]] = None  # Expert rule firing log
    decisionPath: Optional[List[Dict[str, Any]]] = None  # Step-by-step decision process
    # Normalization fields (for transparent scoring)
    reliability: Optional[float] = None  # Reliability metric (0-1 scale)
    norm_cost: Optional[float] = None  # Normalized cost (0-1 scale)
    norm_latency: Optional[float] = None  # Normalized latency (0-1 scale)
    norm_reliability: Optional[float] = None  # Normalized reliability (0-1 scale)
    # Advanced metrics
    security_score: Optional[float] = None  # Security score (0-1 scale)
    vendor_lockin_risk: Optional[float] = None  # Vendor lock-in risk (0-1, lower is better)
    scalability_score: Optional[float] = None  # Scalability potential (0-1 scale)
    norm_security: Optional[float] = None  # Normalized security
    norm_vendor_risk: Optional[float] = None  # Normalized vendor risk
