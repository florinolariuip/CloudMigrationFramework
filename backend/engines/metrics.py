"""
Advanced metrics calculation for cloud migration solutions.
Includes reliability, security, vendor lock-in risk, and other quality attributes.
"""

from typing import Dict, List
from backend.models import Solution

# Provider SLA/Uptime percentages (based on industry standards)
PROVIDER_SLAS = {
    "AWS": 0.9999,  # 99.99% uptime
    "Azure": 0.9995,  # 99.95% uptime
    "GCP": 0.9999,  # 99.99% uptime
}

# Service type reliability multipliers
SERVICE_RELIABILITY = {
    "database": 1.0,  # Critical - high reliability
    "storage": 0.98,  # High reliability
    "compute": 0.97,  # Good reliability
    "cache": 0.96,  # Good reliability
    "api_gateway": 0.99,  # High reliability
    "cdn": 0.98,  # High reliability
    "monitoring": 0.95,  # Lower impact if down
    "backup": 0.97,  # Important but not critical
}

# Security features by provider and service
SECURITY_FEATURES = {
    "AWS": {"encryption": 1.0, "compliance": 0.98, "identity": 0.99},
    "Azure": {"encryption": 0.99, "compliance": 0.97, "identity": 0.98},
    "GCP": {"encryption": 0.98, "compliance": 0.96, "identity": 0.97},
}


def calculate_reliability(solution: Solution) -> float:
    """
    Calculate reliability score based on:
    - Provider SLAs
    - Service types
    - Multi-cloud redundancy (diversity bonus)
    - Number of providers (redundancy)
    
    Returns: float in range [0, 1] where 1 is highest reliability
    """
    if not solution.configuration:
        return 0.95  # Default fallback
    
    # Get provider distribution
    providers = []
    service_reliabilities = []
    
    for service_name, service_choice in solution.configuration.items():
        # Extract provider from service choice (e.g., "AWS EC2" -> "AWS")
        provider = service_choice.split()[0] if service_choice else "AWS"
        providers.append(provider)
        
        # Get service type reliability
        service_type = service_name.lower()
        base_reliability = SERVICE_RELIABILITY.get(service_type, 0.95)
        
        # Get provider SLA
        provider_sla = PROVIDER_SLAS.get(provider, 0.999)
        
        # Combined reliability for this service
        service_reliability = base_reliability * provider_sla
        service_reliabilities.append(service_reliability)
    
    # Base reliability: average of all services
    if service_reliabilities:
        base_score = sum(service_reliabilities) / len(service_reliabilities)
    else:
        base_score = 0.95
    
    # Multi-cloud bonus: diversity reduces single-point-of-failure risk
    unique_providers = len(set(providers))
    if unique_providers > 1:
        diversity_bonus = min(0.05 * (unique_providers - 1), 0.1)  # Max 10% bonus
        base_score = min(1.0, base_score + diversity_bonus)
    
    # Redundancy bonus: more providers = higher availability
    if solution.providers >= 2:
        redundancy_bonus = 0.02 * (solution.providers - 1)
        base_score = min(1.0, base_score + redundancy_bonus)
    
    return round(base_score, 4)


def calculate_security_score(solution: Solution) -> float:
    """
    Calculate security score based on:
    - Provider security features
    - Encryption services
    - Identity management
    - Compliance capabilities
    
    Returns: float in range [0, 1] where 1 is highest security
    """
    if not solution.configuration:
        return 0.90  # Default
    
    security_scores = []
    has_encryption = False
    has_identity = False
    
    for service_name, service_choice in solution.configuration.items():
        provider = service_choice.split()[0] if service_choice else "AWS"
        
        # Check for security services
        service_lower = service_name.lower()
        if "encryption" in service_lower or "kms" in service_lower:
            has_encryption = True
        if "identity" in service_lower or "iam" in service_lower or "ad" in service_lower:
            has_identity = True
        
        # Get provider security features
        provider_security = SECURITY_FEATURES.get(provider, {"encryption": 0.95, "compliance": 0.95, "identity": 0.95})
        avg_security = sum(provider_security.values()) / len(provider_security)
        security_scores.append(avg_security)
    
    # Base security score
    base_score = sum(security_scores) / len(security_scores) if security_scores else 0.90
    
    # Bonuses for security services
    if has_encryption:
        base_score = min(1.0, base_score + 0.05)
    if has_identity:
        base_score = min(1.0, base_score + 0.03)
    
    return round(base_score, 4)


def calculate_vendor_lockin_risk(solution: Solution) -> float:
    """
    Calculate vendor lock-in risk based on provider diversity.
    Lower is better (less risk).
    
    Returns: float in range [0, 1] where 0 is lowest risk (multi-cloud)
    """
    if not solution.configuration or solution.providers == 0:
        return 0.5  # Medium risk
    
    # Single provider = high lock-in risk
    if solution.providers == 1:
        return 1.0
    
    # Multi-cloud reduces risk
    # 2 providers = 0.5 risk
    # 3 providers = 0.33 risk
    risk = 1.0 / solution.providers
    
    return round(risk, 4)


def calculate_scalability_score(solution: Solution) -> float:
    """
    Calculate scalability potential based on:
    - Serverless services (highly scalable)
    - Container services (scalable)
    - Auto-scaling capabilities
    
    Returns: float in range [0, 1] where 1 is highest scalability
    """
    if not solution.configuration:
        return 0.80  # Default
    
    scalability_points = 0.0
    total_services = len(solution.configuration)
    
    for service_name, service_choice in solution.configuration.items():
        service_lower = service_choice.lower()
        
        # Serverless = highest scalability
        if any(term in service_lower for term in ["lambda", "functions", "serverless", "cloud run"]):
            scalability_points += 1.0
        # Containers = high scalability
        elif any(term in service_lower for term in ["eks", "aks", "gke", "kubernetes", "containers"]):
            scalability_points += 0.9
        # Load balancers = enables scaling
        elif "load" in service_lower or "alb" in service_lower:
            scalability_points += 0.85
        # Standard compute
        elif any(term in service_lower for term in ["ec2", "vm", "compute"]):
            scalability_points += 0.7
        # Other services
        else:
            scalability_points += 0.6
    
    if total_services > 0:
        return round(scalability_points / total_services, 4)
    return 0.80


def enrich_solution_with_metrics(solution: Solution) -> Solution:
    """
    Add all advanced metrics to a solution.
    """
    solution.reliability = calculate_reliability(solution)
    solution.security_score = calculate_security_score(solution)
    solution.vendor_lockin_risk = calculate_vendor_lockin_risk(solution)
    solution.scalability_score = calculate_scalability_score(solution)
    
    return solution
