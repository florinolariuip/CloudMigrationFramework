"""
CMOv4 Validation Logic
- Smart selection rules for components
"""

from typing import List
from .models import Component, Architecture
from .pricing import PricingManager


def validate_architecture(arch: Architecture) -> List[str]:
    """
    Validates architecture against smart selection rules, stack-aware constraints, and pricing coverage.
    """
    errors = []
    # Smart selection rules (stub)
    for rule in arch.selection_rules:
        # To be implemented: apply architecture-level selection rules
        pass
    for c in arch.components:
        for rule in getattr(c, 'selection_rules', []):
            # To be implemented: apply component-level selection rules
            pass
    # Rule 1: At least one database
    if not any(c.type == 'database' for c in arch.components):
        errors.append('At least one database component is required.')
    # Rule 2: At least one compute/container
    if not any(c.type in ['compute', 'container'] for c in arch.components):
        errors.append('At least one compute or container component is required.')
    # Rule 3: At least one web/frontend
    if not any(c.type == 'web' for c in arch.components):
        errors.append('At least one web/frontend component is required.')
    # Rule 4: No duplicate databases unless multi-tenancy
    dbs = [c for c in arch.components if c.type == 'database']
    if len(dbs) > 1 and not arch.multi_tenancy:
        errors.append('Multiple databases detected; enable multi-tenancy if required.')
    # Rule 5: Dependency enforcement
    for c in arch.components:
        for dep in c.dependencies:
            if not any(x.name == dep for x in arch.components):
                errors.append(f'Component {c.name} requires missing dependency: {dep}')
    # Rule 6: Dynamic pricing validation
    pricing_manager = PricingManager(getattr(arch.pricing, 'pricing_data', None))
    for c in arch.components:
        for provider in pricing_manager.cache.cache.keys():
            # For each tech stack key in component, check price exists
            for stack_key, stack_value in c.tech_stack.items():
                price = pricing_manager.get_price(provider, stack_value)
                if price is None:
                    errors.append(f"Missing price for {c.type} '{stack_value}' on provider '{provider}' for component '{c.name}'")
    # If no providers found, check user-supplied pricing
    if not pricing_manager.cache.cache.keys() and arch.pricing:
        for provider, services in arch.pricing.pricing_data.items():
            for c in arch.components:
                for stack_key, stack_value in c.tech_stack.items():
                    if stack_value not in services.get(c.type, {}):
                        errors.append(f"Missing price for {c.type} '{stack_value}' on provider '{provider}' for component '{c.name}'")
    if not arch.pricing:
        errors.append('Pricing data is required for architecture.')
    return errors
