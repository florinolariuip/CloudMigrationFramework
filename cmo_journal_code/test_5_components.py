#!/usr/bin/env python3
"""Test 5-component optimization performance"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models import Constraints, Preferences
from engines.constraints import generate_feasible_solutions
from engines.rules import evaluate_solutions

def test_5_components():
    print("Testing 5-component optimization...")
    
    # Simple constraints
    constraints = Constraints(
        maxBudget=5000,
        maxLatency=150,
        maxProviders=3,
        selected_components=['api_gateway', 'database', 'application_server', 'storage', 'cache']
    )
    
    preferences = Preferences(
        preferredProvider=None,
        prioritizeCost=True,
        prioritizePerformance=False
    )
    
    print(f"Components: {constraints.selected_components}")
    print(f"Budget: ${constraints.maxBudget}, Latency: {constraints.maxLatency}ms")
    
    # Test CSP phase
    print("\n1. CSP Phase...")
    start = time.time()
    feasible = generate_feasible_solutions(constraints)
    csp_time = time.time() - start
    print(f"   Found {len(feasible)} feasible solutions in {csp_time:.2f}s")
    
    if len(feasible) == 0:
        print("   ERROR: No feasible solutions found!")
        return
    
    # Test Expert phase
    print("\n2. Expert System Phase...")
    start = time.time()
    ranked = evaluate_solutions(feasible, preferences, constraints.maxBudget)
    expert_time = time.time() - start
    print(f"   Ranked {len(ranked)} solutions in {expert_time:.2f}s")
    
    # Show top solution
    if ranked:
        top = ranked[0]
        print(f"\n3. Top Solution:")
        print(f"   Cost: ${top.cost:.2f}")
        print(f"   Latency: {top.latency:.2f}ms")
        print(f"   Score: {top.score}")
        print(f"   Providers: {top.providers}")
    
    total_time = csp_time + expert_time
    print(f"\nTotal time: {total_time:.2f}s")
    
    if total_time < 1:
        print("EXCELLENT: Sub-second optimization")
    elif total_time < 5:
        print("GOOD: Fast optimization")
    else:
        print("SLOW: Optimization taking too long")

if __name__ == "__main__":
    test_5_components()