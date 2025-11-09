"""
Sankey Diagram Data Generator

This module generates Sankey diagram data for visualizing cloud migration solution flows.
Sankey diagrams show the distribution of cost, latency, and resource allocation across
components and providers.

Key visualizations:
- Provider allocation (which providers are used for which components)
- Cost distribution (how cost flows from providers to components)
- Latency contributions (which components and providers contribute most to latency)
"""

from typing import Dict, List, Any
from models import Solution


def generate_sankey_data(solution: Solution, services_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Sankey diagram data from a solution.
    
    Args:
        solution: The cloud migration solution
        services_data: Service pricing and latency data
        
    Returns:
        Dictionary with nodes and links for Sankey diagram visualization
    """
    nodes = []
    links = []
    node_index = {}
    
    # Extract configuration and pricing data
    config = solution.configuration
    costs = services_data.get('costs', {})
    latencies = services_data.get('latency', {})
    
    # Create provider nodes
    providers = set()
    for service in config.values():
        provider = service.split('_')[0].upper()  # Extract provider from service name
        providers.add(provider)
    
    for provider in sorted(providers):
        idx = len(nodes)
        node_index[f"provider_{provider}"] = idx
        nodes.append({"name": f"{provider} Provider", "color": get_provider_color(provider)})
    
    # Create component category nodes
    categories = {
        'Compute': ['api_gateway', 'application_server', 'containers', 'serverless_compute'],
        'Data': ['database', 'storage', 'cache', 'analytics'],
        'Network': ['cdn', 'load_balancer', 'message_queue'],
        'Security': ['identity_management', 'encryption'],
        'Operations': ['monitoring', 'backup']
    }
    
    for category in categories:
        idx = len(nodes)
        node_index[f"category_{category}"] = idx
        nodes.append({"name": category, "color": get_category_color(category)})
    
    # Create links from providers to categories
    # Track cost and latency contributions
    provider_to_category = {}
    
    for component, service in config.items():
        provider = service.split('_')[0].upper()
        
        # Find which category this component belongs to
        category = None
        for cat, comps in categories.items():
            if component in comps:
                category = cat
                break
        
        if category:
            key = (provider, category)
            if key not in provider_to_category:
                provider_to_category[key] = {
                    'cost': 0,
                    'latency': 0,
                    'count': 0
                }
            
            provider_to_category[key]['cost'] += costs.get(service, 0)
            provider_to_category[key]['latency'] += latencies.get(service, 0)
            provider_to_category[key]['count'] += 1
    
    # Create links with cost as the flow value
    for (provider, category), data in provider_to_category.items():
        source_idx = node_index[f"provider_{provider}"]
        target_idx = node_index[f"category_{category}"]
        
        links.append({
            "source": source_idx,
            "target": target_idx,
            "value": data['cost'],
            "label": f"${data['cost']:.2f}/mo",
            "color": get_provider_color(provider, alpha=0.4)
        })
    
    return {
        "nodes": nodes,
        "links": links,
        "metadata": {
            "total_cost": solution.cost,
            "total_latency": solution.latency,
            "providers_count": len(providers),
            "visualization_type": "cost_flow"
        }
    }


def generate_latency_sankey(solution: Solution, services_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Sankey diagram showing latency contributions.
    
    Args:
        solution: The cloud migration solution
        services_data: Service pricing and latency data
        
    Returns:
        Dictionary with nodes and links showing latency flow
    """
    nodes = []
    links = []
    node_index = {}
    
    config = solution.configuration
    latencies = services_data.get('latency', {})
    
    # Create provider nodes
    providers = set()
    for service in config.values():
        provider = service.split('_')[0].upper()
        providers.add(provider)
    
    for provider in sorted(providers):
        idx = len(nodes)
        node_index[f"provider_{provider}"] = idx
        nodes.append({"name": f"{provider}", "color": get_provider_color(provider)})
    
    # Create component nodes (individual components)
    for component in sorted(config.keys()):
        idx = len(nodes)
        node_index[f"component_{component}"] = idx
        nodes.append({"name": component.replace('_', ' ').title(), "color": "#888888"})
    
    # Create links showing latency contribution
    for component, service in config.items():
        provider = service.split('_')[0].upper()
        latency = latencies.get(service, 0)
        
        if latency > 0:
            source_idx = node_index[f"provider_{provider}"]
            target_idx = node_index[f"component_{component}"]
            
            links.append({
                "source": source_idx,
                "target": target_idx,
                "value": latency,
                "label": f"{latency:.2f}ms",
                "color": get_latency_color(latency, alpha=0.4)
            })
    
    return {
        "nodes": nodes,
        "links": links,
        "metadata": {
            "total_latency": solution.latency,
            "avg_latency": solution.latency,
            "visualization_type": "latency_flow"
        }
    }


def get_provider_color(provider: str, alpha: float = 1.0) -> str:
    """Get color for a provider."""
    colors = {
        'AWS': f'rgba(255, 153, 0, {alpha})',      # Orange
        'AZURE': f'rgba(0, 120, 212, {alpha})',    # Blue
        'GCP': f'rgba(66, 133, 244, {alpha})',     # Google Blue
    }
    return colors.get(provider, f'rgba(128, 128, 128, {alpha})')


def get_category_color(category: str) -> str:
    """Get color for a component category."""
    colors = {
        'Compute': '#3B82F6',     # Blue
        'Data': '#8B5CF6',        # Purple
        'Network': '#10B981',     # Green
        'Security': '#EF4444',    # Red
        'Operations': '#F59E0B',  # Yellow
    }
    return colors.get(category, '#6B7280')


def get_latency_color(latency: float, alpha: float = 1.0) -> str:
    """Get color based on latency value (gradient from green to red)."""
    if latency < 5:
        return f'rgba(34, 197, 94, {alpha})'   # Green - fast
    elif latency < 10:
        return f'rgba(234, 179, 8, {alpha})'   # Yellow - medium
    else:
        return f'rgba(239, 68, 68, {alpha})'   # Red - slow
