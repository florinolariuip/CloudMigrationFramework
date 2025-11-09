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
    score: Optional[int] = None
    evaluationLog: Optional[List[Dict[str, Any]]] = None
    # Explainability fields (Priority 3 enhancement)
    constraintProof: Optional[List[Dict[str, Any]]] = None  # Constraint satisfaction evidence
    ruleTrace: Optional[List[Dict[str, Any]]] = None  # Expert rule firing log
    decisionPath: Optional[List[Dict[str, Any]]] = None  # Step-by-step decision process
