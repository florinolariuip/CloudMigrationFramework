"""
CMOv4 Helper Functions

Utility functions for CMOv4 optimizer including instance count scaling,
component mapping, and cost calculations.
"""
from typing import Dict, List


def get_instance_counts(components: list) -> Dict[str, int]:
    """
    Extract instance counts from CMOv4 components.
    
    Args:
        components: List of Component dicts with 'type' and 'instance_count'
    
    Returns:
        Dict mapping component type to instance count
        Example: {'web': 5, 'compute': 3, 'database': 2}
    """
    counts = {}
    for comp in components:
        comp_type = comp.get('type', '').lower()
        count = comp.get('instance_count', 1)
        # If multiple components of same type, sum them
        counts[comp_type] = counts.get(comp_type, 0) + count
    return counts


def calculate_cost_with_instances(base_cost: float, 
                                  service_type: str, 
                                  instance_counts: Dict[str, int]) -> float:
    """
    Scale cost by instance count.
    
    Args:
        base_cost: Base monthly cost for service
        service_type: Type of service (api_gateway, application_server, etc.)
        instance_counts: Dict of instance counts per type
    
    Returns:
        Scaled cost: base_cost * instance_count
    """
    # Map CMOv3 service types to CMOv4 component types
    type_mapping = {
        'api_gateway': 'web',
        'application_server': 'compute',
        'database': 'database',
        'cache': 'cache',
        'monitoring': 'monitoring',
        'message_queue': 'message_queue',
        'storage': 'storage',
        'load_balancer': 'load_balancer',
        'backup': 'backup',
        'encryption': 'encryption',
        'cdn': 'cdn',
        'analytics': 'analytics',
        'containers': 'containers',
        'serverless_compute': 'serverless_compute',
        'identity_management': 'security',
    }
    
    comp_type = type_mapping.get(service_type, service_type)
    count = instance_counts.get(comp_type, 1)
    
    return base_cost * count


def get_total_instance_count(components: list) -> int:
    """
    Get total number of instances across all components.
    
    Args:
        components: List of Component dicts
    
    Returns:
        Total instance count
    """
    return sum(comp.get('instance_count', 1) for comp in components)


def get_components_by_type(components: list) -> Dict[str, List[dict]]:
    """
    Group components by type.
    
    Args:
        components: List of Component dicts
    
    Returns:
        Dict mapping type to list of components of that type
    """
    grouped = {}
    for comp in components:
        comp_type = comp.get('type', '').lower()
        if comp_type not in grouped:
            grouped[comp_type] = []
        grouped[comp_type].append(comp)
    return grouped
