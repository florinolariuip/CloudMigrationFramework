"""
Sensitivity Analysis for Academic Paper

Tests how solution quality changes with parameter variations.
Generates data for sensitivity analysis section of the research paper.

Parameters tested:
- Budget constraint (2000, 3000, 5000, 7000, 10000)
- Latency constraint (8, 10, 12, 15, 20)
- Max providers (1, 2, 3)
- Component count (6, 10, 15)

Metrics measured:
- Number of feasible solutions
- Pareto frontier size
- Best solution cost/latency/score
- Execution time
- Pruning efficiency
"""
import json
import time
import os
from datetime import datetime

from backend.engines.constraints import generate_feasible_solutions
from backend.engines.rules import evaluate_solutions, deduplicate_solutions
from backend.engines.pareto import calculate_pareto_frontier, calculate_pareto_metrics
from backend.models import Constraints, Preferences


def run_sensitivity_analysis():
    """
    Run comprehensive sensitivity analysis across key parameters.
    """
    print("=" * 80)
    print("SENSITIVITY ANALYSIS - Cloud Migration Optimizer")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    results = []
    
    # 1. BUDGET SENSITIVITY
    print("1. BUDGET SENSITIVITY ANALYSIS")
    print("-" * 80)
    budgets = [2000, 3000, 5000, 7000, 10000]
    for budget in budgets:
        print(f"Testing budget: ${budget}...")
        start = time.time()
        
        constraints = Constraints(maxBudget=budget, maxLatency=12, maxProviders=2)
        preferences = Preferences()
        
        # Generate and deduplicate
        solutions = generate_feasible_solutions(constraints)
        pre_dedup = len(solutions)
        solutions = deduplicate_solutions(solutions)
        post_dedup = len(solutions)
        
        # Evaluate
        ranked = evaluate_solutions(solutions, preferences, max_budget=budget)
        
        # Pareto
        pareto = calculate_pareto_frontier(solutions) if solutions else []
        
        duration = time.time() - start
        
        result = {
            'parameter': 'budget',
            'value': budget,
            'feasible_pre_dedup': pre_dedup,
            'feasible_post_dedup': post_dedup,
            'duplicates_removed': pre_dedup - post_dedup,
            'pareto_size': len(pareto),
            'best_cost': ranked[0].cost if ranked else None,
            'best_latency': ranked[0].latency if ranked else None,
            'best_score': ranked[0].score if ranked else None,
            'best_providers': ranked[0].providers if ranked else None,
            'execution_time_ms': round(duration * 1000, 2),
        }
        results.append(result)
        
        best_cost_str = f"${result['best_cost']:.2f}" if result['best_cost'] else "$0"
        best_lat_str = f"{result['best_latency']:.1f}ms" if result['best_latency'] else "0ms"
        print(f"  Feasible: {post_dedup} | Pareto: {len(pareto)} | "
              f"Best: {best_cost_str}, {best_lat_str} | "
              f"Time: {result['execution_time_ms']:.0f}ms")
    
    print()
    
    # 2. LATENCY SENSITIVITY
    print("2. LATENCY SENSITIVITY ANALYSIS")
    print("-" * 80)
    latencies = [8, 10, 12, 15, 20]
    for latency in latencies:
        print(f"Testing max latency: {latency}ms...")
        start = time.time()
        
        constraints = Constraints(maxBudget=5000, maxLatency=latency, maxProviders=2)
        preferences = Preferences()
        
        solutions = generate_feasible_solutions(constraints)
        pre_dedup = len(solutions)
        solutions = deduplicate_solutions(solutions)
        post_dedup = len(solutions)
        
        ranked = evaluate_solutions(solutions, preferences, max_budget=5000)
        pareto = calculate_pareto_frontier(solutions) if solutions else []
        
        duration = time.time() - start
        
        result = {
            'parameter': 'latency',
            'value': latency,
            'feasible_pre_dedup': pre_dedup,
            'feasible_post_dedup': post_dedup,
            'duplicates_removed': pre_dedup - post_dedup,
            'pareto_size': len(pareto),
            'best_cost': ranked[0].cost if ranked else None,
            'best_latency': ranked[0].latency if ranked else None,
            'best_score': ranked[0].score if ranked else None,
            'best_providers': ranked[0].providers if ranked else None,
            'execution_time_ms': round(duration * 1000, 2),
        }
        results.append(result)
        
        best_cost_str = f"${result['best_cost']:.2f}" if result['best_cost'] else "$0"
        best_lat_str = f"{result['best_latency']:.1f}ms" if result['best_latency'] else "0ms"
        print(f"  Feasible: {post_dedup} | Pareto: {len(pareto)} | "
              f"Best: {best_cost_str}, {best_lat_str} | "
              f"Time: {result['execution_time_ms']:.0f}ms")
    
    print()
    
    # 3. PROVIDER COUNT SENSITIVITY
    print("3. MAX PROVIDERS SENSITIVITY ANALYSIS")
    print("-" * 80)
    provider_counts = [1, 2, 3]
    for max_providers in provider_counts:
        print(f"Testing max providers: {max_providers}...")
        start = time.time()
        
        constraints = Constraints(maxBudget=5000, maxLatency=12, maxProviders=max_providers)
        preferences = Preferences()
        
        solutions = generate_feasible_solutions(constraints)
        pre_dedup = len(solutions)
        solutions = deduplicate_solutions(solutions)
        post_dedup = len(solutions)
        
        ranked = evaluate_solutions(solutions, preferences, max_budget=5000)
        pareto = calculate_pareto_frontier(solutions) if solutions else []
        
        duration = time.time() - start
        
        result = {
            'parameter': 'max_providers',
            'value': max_providers,
            'feasible_pre_dedup': pre_dedup,
            'feasible_post_dedup': post_dedup,
            'duplicates_removed': pre_dedup - post_dedup,
            'pareto_size': len(pareto),
            'best_cost': ranked[0].cost if ranked else None,
            'best_latency': ranked[0].latency if ranked else None,
            'best_score': ranked[0].score if ranked else None,
            'best_providers': ranked[0].providers if ranked else None,
            'execution_time_ms': round(duration * 1000, 2),
        }
        results.append(result)
        
        best_cost_str = f"${result['best_cost']:.2f}" if result['best_cost'] else "$0"
        best_lat_str = f"{result['best_latency']:.1f}ms" if result['best_latency'] else "0ms"
        print(f"  Feasible: {post_dedup} | Pareto: {len(pareto)} | "
              f"Best: {best_cost_str}, {best_lat_str} | "
              f"Time: {result['execution_time_ms']:.0f}ms")
    
    print()
    
    # 4. COMPONENT COUNT SENSITIVITY
    print("4. COMPONENT COUNT SENSITIVITY ANALYSIS")
    print("-" * 80)
    component_sets = [
        (6, ['api_gateway', 'application_server', 'database', 'cache', 'monitoring', 'storage']),
        (10, ['api_gateway', 'application_server', 'database', 'cache', 'monitoring', 
              'storage', 'message_queue', 'load_balancer', 'backup', 'encryption']),
        (15, None),  # All 15 components
    ]
    
    for count, components in component_sets:
        print(f"Testing {count} components...")
        start = time.time()
        
        constraints = Constraints(
            maxBudget=5000, 
            maxLatency=12, 
            maxProviders=2,
            selected_components=components
        )
        preferences = Preferences()
        
        solutions = generate_feasible_solutions(constraints)
        pre_dedup = len(solutions)
        solutions = deduplicate_solutions(solutions)
        post_dedup = len(solutions)
        
        ranked = evaluate_solutions(solutions, preferences, max_budget=5000)
        pareto = calculate_pareto_frontier(solutions) if solutions else []
        
        duration = time.time() - start
        
        result = {
            'parameter': 'component_count',
            'value': count,
            'feasible_pre_dedup': pre_dedup,
            'feasible_post_dedup': post_dedup,
            'duplicates_removed': pre_dedup - post_dedup,
            'pareto_size': len(pareto),
            'best_cost': ranked[0].cost if ranked else None,
            'best_latency': ranked[0].latency if ranked else None,
            'best_score': ranked[0].score if ranked else None,
            'best_providers': ranked[0].providers if ranked else None,
            'execution_time_ms': round(duration * 1000, 2),
        }
        results.append(result)
        
        best_cost_str = f"${result['best_cost']:.2f}" if result['best_cost'] else "$0"
        best_lat_str = f"{result['best_latency']:.1f}ms" if result['best_latency'] else "0ms"
        print(f"  Feasible: {post_dedup} | Pareto: {len(pareto)} | "
              f"Best: {best_cost_str}, {best_lat_str} | "
              f"Time: {result['execution_time_ms']:.0f}ms")
    
    print()
    print("=" * 80)
    print("SENSITIVITY ANALYSIS COMPLETE")
    print("=" * 80)
    
    # Save results
    output_dir = 'backend/results'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'sensitivity_analysis.json')
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_experiments': len(results),
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Total experiments: {len(results)}")
    
    # Generate summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    for param in ['budget', 'latency', 'max_providers', 'component_count']:
        param_results = [r for r in results if r['parameter'] == param]
        if param_results:
            print(f"\n{param.upper().replace('_', ' ')}:")
            print(f"  Experiments: {len(param_results)}")
            print(f"  Avg feasible solutions: {sum(r['feasible_post_dedup'] for r in param_results) / len(param_results):.1f}")
            print(f"  Avg Pareto size: {sum(r['pareto_size'] for r in param_results) / len(param_results):.1f}")
            print(f"  Avg execution time: {sum(r['execution_time_ms'] for r in param_results) / len(param_results):.0f}ms")
    
    return results


if __name__ == '__main__':
    results = run_sensitivity_analysis()
    print("\n✅ Sensitivity analysis complete!")
    print("Use the generated JSON file for paper figures and tables.")
