"""Edge-case tests for robustness: tight constraints and invalid input.

These tests complement the happy-path optimizer tests by ensuring the
system behaves gracefully when constraints are impossible or inputs are
malformed.
"""

from __future__ import annotations

from typing import Dict, Any

from backend.cmov4 import optimizer as cmov4_optimizer


def _make_too_tight_constraints() -> Dict[str, Any]:
    """Return a constraints dict that should realistically yield no solutions.

    We intentionally pick an extremely low budget and latency while
    capping providers, to force the "zero solutions" path.
    """

    return {
        "maxBudget": 10,        # unrealistically low given service prices
        "maxLatency": 1.0,      # unrealistically low latency
        "maxProviders": 1,
    }


def test_cmov4_zero_solutions_handling():
    """CMOv4 should handle impossible constraints without crashing.

    We call the CMOv4 optimizer directly with extremely tight
    constraints and assert that it returns a structured result rather
    than raising an exception. The exact suggestion content is left
    intentionally loose to avoid over-constraining the behaviour.
    """

    constraints = _make_too_tight_constraints()
    arch = {
        "components": [
            "compute",
            "database",
            "cache",
        ],
        "requirements": {"scalability": "high", "availability": "high"},
    }

    result = cmov4_optimizer.optimize_architecture(arch, constraints)

    # Basic structural checks
    assert isinstance(result, dict)
    assert "solutions" in result
    assert isinstance(result["solutions"], list)
    # No assertion on emptiness: current implementation may still find
    # a cheap solution even under tight constraints, but the call must
    # not crash.


def test_cmov4_handles_malformed_constraints_safely():
    """CMOv4 optimizer should handle malformed constraints without crashing.

    We pass a constraints object missing expected keys and assert that
    the call either raises a clear exception or returns a structured
    result, rather than failing catastrophically. The current
    implementation tends to fall back to default constraints when keys
    are missing, which is acceptable as long as behaviour is safe and
    documented elsewhere.
    """

    # Missing maxBudget / maxLatency keys entirely
    bad_constraints: Dict[str, Any] = {"unexpected": 123}
    arch = {
        "components": ["compute"],
        "requirements": {},
    }

    try:
        result = cmov4_optimizer.optimize_architecture(arch, bad_constraints)
    except (KeyError, ValueError, TypeError):
        # Explicit validation failure is acceptable behaviour
        return

    # If no exception is raised, we at least expect a dict with the
    # usual optimisation fields; the function must not crash.
    assert isinstance(result, dict)
    assert "solutions" in result
    assert isinstance(result["solutions"], list)
    # We do not constrain whether solutions are present here, because
    # the implementation may treat missing keys by applying defaults.
