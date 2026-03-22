"""
CMOv4 Validation Logic
- Smart selection rules for components
"""

from typing import List, Dict, Any
from .models import Component, Architecture
from .pricing import PricingManager


def _validate_arch_selection_rules(arch: Architecture) -> List[str]:
    """Validate architecture-level selection rules (e.g., min_components)."""
    errors: List[str] = []
    for rule in arch.selection_rules:
        rule_type = rule.get("type", "")
        if rule_type == "min_components" and len(arch.components) < rule.get("value", 3):
            errors.append(
                f"Architecture requires at least {rule.get('value', 3)} components"
            )
    return errors


def _validate_component_selection_rules(arch: Architecture) -> List[str]:
    """Validate component-level selection rules (e.g., min_instances)."""
    errors: List[str] = []
    for c in arch.components:
        for rule in getattr(c, "selection_rules", []):
            rule_type = rule.get("type", "")
            if rule_type == "min_instances" and c.instance_count < rule.get("value", 1):
                errors.append(
                    f"Component {c.name} requires at least {rule.get('value', 1)} instances"
                )
    return errors


def _validate_required_component_types(arch: Architecture) -> List[str]:
    """Ensure mandatory component types (db/compute/web) are present."""
    errors: List[str] = []
    if not any(c.type == "database" for c in arch.components):
        errors.append("At least one database component is required.")
    if not any(c.type in ["compute", "container"] for c in arch.components):
        errors.append("At least one compute or container component is required.")
    if not any(c.type == "web" for c in arch.components):
        errors.append("At least one web/frontend component is required.")
    return errors


def _validate_database_multiplicity(arch: Architecture) -> List[str]:
    """Ensure multiple databases only allowed when multi-tenancy is enabled."""
    errors: List[str] = []
    dbs = [c for c in arch.components if c.type == "database"]
    if len(dbs) > 1 and not arch.multi_tenancy:
        errors.append("Multiple databases detected; enable multi-tenancy if required.")
    return errors


def _validate_dependencies(arch: Architecture) -> List[str]:
    """Validate that all declared component dependencies are present."""
    errors: List[str] = []
    component_names = {c.name for c in arch.components}
    for c in arch.components:
        for dep in c.dependencies:
            if dep not in component_names:
                errors.append(f"Component {c.name} requires missing dependency: {dep}")
    return errors


def _validate_dynamic_pricing_coverage(arch: Architecture) -> List[str]:
    """Validate that dynamic pricing has entries for all tech stacks/providers.

    This mirrors the previous PricingManager-based validation but is isolated for clarity.
    """
    errors: List[str] = []
    pricing_manager = PricingManager(getattr(arch.pricing, "pricing_data", None))

    for c in arch.components:
        for provider in pricing_manager.cache.cache.keys():
            for stack_key, stack_value in c.tech_stack.items():
                price = pricing_manager.get_price(provider, stack_value)
                if price is None:
                    errors.append(
                        f"Missing price for {c.type} '{stack_value}' on provider '{provider}' for component '{c.name}'"
                    )
    return errors


def _validate_user_supplied_pricing(arch: Architecture) -> List[str]:
    """Validate any explicit user-supplied pricing_data structures."""
    errors: List[str] = []
    if arch.pricing and hasattr(arch.pricing, "pricing_data"):
        for provider, services in arch.pricing.pricing_data.items():
            for c in arch.components:
                for stack_key, stack_value in c.tech_stack.items():
                    if isinstance(services, dict) and c.type in services:
                        if stack_value not in services.get(c.type, {}):
                            errors.append(
                                f"Missing price for {c.type} '{stack_value}' on provider '{provider}' for component '{c.name}'"
                            )
    return errors


def validate_architecture(arch: Architecture) -> List[str]:
    """Validate architecture against selection rules and pricing coverage.

    Behaviour is equivalent to the previous inline implementation but split into
    smaller helpers for clarity and lower cyclomatic complexity.
    """
    errors: List[str] = []

    errors.extend(_validate_arch_selection_rules(arch))
    errors.extend(_validate_component_selection_rules(arch))
    errors.extend(_validate_required_component_types(arch))
    errors.extend(_validate_database_multiplicity(arch))
    errors.extend(_validate_dependencies(arch))
    errors.extend(_validate_dynamic_pricing_coverage(arch))
    errors.extend(_validate_user_supplied_pricing(arch))

    # Pricing validation is optional for testing scenarios; we intentionally do
    # not add errors when pricing is missing but components exist. This
    # preserves the original behaviour where such cases were allowed.
    return errors
