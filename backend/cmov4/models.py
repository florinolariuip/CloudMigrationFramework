"""
CMOv4 Data Models
- Component: type, name, instance_count, tech_stack, dependencies
- Architecture: logical relationships, multi-tenancy, grouping
"""
from typing import List, Dict, Optional


class Component:
    """
    Represents a single architecture component.
    Supports smart selection rules and stack-aware validation.
    """
    def __init__(self, name: str, type: str, instance_count: int = 1, tech_stack: Optional[Dict[str, any]] = None, dependencies: Optional[List[str]] = None, selection_rules: Optional[List[Dict]] = None):
        self.name = name
        self.type = type
        self.instance_count = instance_count
        self.tech_stack = tech_stack or {}
        self.dependencies = dependencies or []
        self.selection_rules = selection_rules or []

    def apply_selection_rules(self, context: Dict) -> None:
        """
        Apply smart selection logic based on context.
        Adjusts tech stack, instance count, etc. based on workload requirements.
        """
        # Basic selection rules for demonstration
        workload_size = context.get('workload_size', 'medium')
        
        if workload_size == 'large':
            self.instance_count = max(self.instance_count, 3)
        elif workload_size == 'small':
            self.instance_count = min(self.instance_count, 1)
            
        # Apply tech stack preferences
        if context.get('prefer_managed', True):
            if self.type == 'database':
                self.tech_stack['managed'] = True


class Pricing:
    def __init__(self, pricing_data: Dict[str, Dict[str, Dict[str, float]]]):
        """
        pricing_data: {
            'AWS': {'database': {'SQL Server': 0.25}, 'compute': {'.NET': 0.10}, ...},
            'Azure': {...},
            'GCP': {...}
        }
        """
        self.pricing_data = pricing_data


class Architecture:
    """
    Represents the full architecture, including components, relationships, patterns, and pricing.
    Supports advanced schema and smart selection rules.
    """
    def __init__(self, components: List[Component], relationships: Optional[List[Dict]] = None, multi_tenancy: bool = False, architecture_pattern: Optional[str] = None, pricing: Optional[Pricing] = None, selection_rules: Optional[List[Dict]] = None):
        self.components = components
        self.relationships = relationships or []
        self.multi_tenancy = multi_tenancy
        self.architecture_pattern = architecture_pattern
        self.pricing = pricing
        self.selection_rules = selection_rules or []

    def apply_selection_rules(self, context: Dict) -> None:
        """
        Apply architecture-level smart selection logic.
        Configures patterns, relationships, and global settings.
        """
        # Apply architecture pattern rules
        if self.architecture_pattern == 'microservices':
            # Ensure load balancer and service mesh components
            has_lb = any(c.type == 'load_balancer' for c in self.components)
            if not has_lb and len(self.components) > 3:
                # Would add load balancer component in production
                pass
                
        # Apply multi-tenancy rules
        if context.get('tenant_count', 1) > 1:
            self.multi_tenancy = True
