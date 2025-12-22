"""
Multi-Run Experiment for Journal Publication

Runs CMOv4 and all 5 baseline algorithms 30 times with different random seeds
to compute statistical measures (mean ± std dev) as required for academic rigor.

This addresses reviewer concern: "Single-run results lack statistical rigor"

Output:
- experiments/results/multi_run_results.csv (raw data)
- experiments/results/multi_run_statistics.csv (summary statistics)
- experiments/results/table_multi_run.tex (LaTeX table)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import time
import json
from typing import Dict, Any

from backend.models import Constraints
from backend.engines.baselines import (
    baseline_random,
    baseline_greedy_cost,
    baseline_greedy_latency,
    baseline_genetic_algorithm,
    baseline_weighted_sum
)


def run_cmov4_experiment(seed: int, constraints: Constraints) -> Dict[str, Any]:
    """Run CMOv4 with specific seed"""
    np.random.seed(seed)
    
    # Import here to ensure seed is set first
    from backend.cmov4.optimizer import optimize_architecture
    
    start_time = time.time()
    
    # Standard architecture with 18 components
    arch = {
        'components': [
            'compute', 'database', 'cache', 'storage', 'cdn',
            'load_balancer', 'message_queue', 'event_streaming',
            'serverless_compute', 'monitoring', 'backup', 'security',
            'containers', 'analytics', 'identity', 'iot_platform',
            'nosql_database', 'api_gateway'
        ],
        'requirements': {
            'scalability': 'high',
            'availability': 'high'
        }
    }
    
    constraint_dict = {
        'maxBudget': constraints.maxBudget,
        'maxLatency': constraints.maxLatency,
        'maxProviders': constraints.maxProviders
    }
    
    try:
        result = optimize_architecture(arch, constraint_dict)
        execution_time = (time.time() - start_time) * 1000  # ms
        
        # Extract best solution from solutions list (ranked by score)
        solutions = result.get('solutions', [])
        pareto_frontier = result.get('pareto_frontier', [])
        
        # CMOv4 returns success if we got any feasible solutions
        success = len(solutions) > 0
        
        if success:
            # Use the best solution (first in ranked list)
            best_solution = solutions[0]
            return {
                'seed': seed,
                'algorithm': 'CMOv4',
                'cost': best_solution.get('cost', 0),
                'latency': best_solution.get('latency', 0),
                'providers': best_solution.get('providers', 0),
                'time_ms': execution_time,
                'pareto_size': len(pareto_frontier),
                'success': True
            }
        else:
            return {
                'seed': seed,
                'algorithm': 'CMOv4',
                'cost': 0,
                'latency': 0,
                'providers': 0,
                'time_ms': execution_time,
                'pareto_size': len(pareto_frontier),
                'success': False
            }
    except Exception as e:
        print(f"  ✗ CMOv4 seed {seed} failed: {e}")
        return {
            'seed': seed,
            'algorithm': 'CMOv4',
            'cost': 0,
            'latency': 0,
            'providers': 0,
            'time_ms': 0,
            'pareto_size': 0,
            'success': False
        }


def run_baseline_experiment(algorithm_name: str, seed: int, constraints: Constraints) -> Dict[str, Any]:
    """Run baseline algorithm with specific seed"""
    np.random.seed(seed)
    
    try:
        if algorithm_name == "Random":
            result = baseline_random(constraints, max_attempts=1000)
        elif algorithm_name == "GreedyCost":
            result = baseline_greedy_cost(constraints)
        elif algorithm_name == "GreedyLatency":
            result = baseline_greedy_latency(constraints)
        elif algorithm_name == "GA":
            result = baseline_genetic_algorithm(
                constraints,
                population_size=50,
                generations=100,
                mutation_rate=0.1,
                crossover_rate=0.7
            )
        elif algorithm_name == "WeightedSum":
            result = baseline_weighted_sum(constraints, cost_weight=0.5, latency_weight=0.5)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm_name}")
        
        solution = result.solution
        
        return {
            'seed': seed,
            'algorithm': algorithm_name,
            'cost': solution.cost if solution else 0,
            'latency': solution.latency if solution else 0,
            'providers': len(solution.providerDistribution) if solution else 0,
            'time_ms': result.execution_time_ms,
            'pareto_size': 0,  # Baselines don't generate Pareto frontier
            'success': result.success
        }
    except Exception as e:
        print(f"  ✗ {algorithm_name} seed {seed} failed: {e}")
        return {
            'seed': seed,
            'algorithm': algorithm_name,
            'cost': 0,
            'latency': 0,
            'providers': 0,
            'time_ms': 0,
            'pareto_size': 0,
            'success': False
        }


def run_multi_experiment(n_runs: int = 30) -> tuple:
    """Run all algorithms n_runs times"""
    
    print("="*80)
    print("MULTI-RUN EXPERIMENT FOR JOURNAL PUBLICATION")
    print("="*80)
    print(f"Runs per algorithm: {n_runs}")
    print(f"Total experiments: {n_runs * 6} (6 algorithms)")
    print("="*80)
    
    # Standard constraints
    constraints = Constraints(
        maxBudget=5000,
        maxLatency=150,
        maxProviders=3
    )
    
    print(f"\nConstraints: Budget=${constraints.maxBudget}, Latency={constraints.maxLatency}ms, Providers={constraints.maxProviders}")
    
    algorithms = ["CMOv4", "GA", "GreedyCost", "GreedyLatency", "Random", "WeightedSum"]
    
    results = []
    
    for algorithm in algorithms:
        print(f"\n{'='*80}")
        print(f"Running {algorithm} - {n_runs} runs")
        print(f"{'='*80}")
        
        for seed in range(n_runs):
            print(f"  Run {seed+1}/{n_runs}...", end=' ', flush=True)
            
            if algorithm == "CMOv4":
                result = run_cmov4_experiment(seed, constraints)
            else:
                result = run_baseline_experiment(algorithm, seed, constraints)
            
            results.append(result)
            
            if result['success']:
                print(f"✓ Cost: ${result['cost']:.2f}, Latency: {result['latency']:.2f}ms, Time: {result['time_ms']:.2f}ms")
            else:
                print(f"✗ Failed")
    
    # Create results directory
    os.makedirs('experiments/results', exist_ok=True)
    
    # Save raw results
    df = pd.DataFrame(results)
    df.to_csv('experiments/results/multi_run_results.csv', index=False)
    print(f"\n✓ Raw results saved: experiments/results/multi_run_results.csv")
    
    # Compute statistics
    stats = compute_statistics(df)
    
    return df, stats


def compute_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean, std, min, max for each algorithm"""
    
    print("\n" + "="*80)
    print("STATISTICAL SUMMARY (Mean ± Std Dev)")
    print("="*80)
    
    # Group by algorithm and compute statistics
    stats = df.groupby('algorithm').agg({
        'cost': ['mean', 'std', 'min', 'max', 'count'],
        'latency': ['mean', 'std', 'min', 'max'],
        'time_ms': ['mean', 'std', 'min', 'max'],
        'pareto_size': ['mean', 'std'],
        'success': 'sum'
    }).round(2)
    
    # Print formatted table
    print(f"\n{'Algorithm':<15} {'Cost (Mean±Std)':<25} {'Latency (Mean±Std)':<25} {'Time (Mean±Std)':<25} {'Success Rate'}")
    print("-"*110)
    
    for algorithm in stats.index:
        cost_mean = stats.loc[algorithm, ('cost', 'mean')]
        cost_std = stats.loc[algorithm, ('cost', 'std')]
        lat_mean = stats.loc[algorithm, ('latency', 'mean')]
        lat_std = stats.loc[algorithm, ('latency', 'std')]
        time_mean = stats.loc[algorithm, ('time_ms', 'mean')]
        time_std = stats.loc[algorithm, ('time_ms', 'std')]
        success_count = stats.loc[algorithm, ('success', 'sum')]
        total_runs = stats.loc[algorithm, ('cost', 'count')]
        
        print(f"{algorithm:<15} ${cost_mean:.2f} ± {cost_std:.2f}{'':>8} {lat_mean:.2f} ± {lat_std:.2f}ms{'':>8} {time_mean:.2f} ± {time_std:.2f}ms{'':>8} {success_count}/{total_runs}")
    
    # Save to file
    stats.to_csv('experiments/results/multi_run_statistics.csv')
    print(f"\n✓ Statistics saved: experiments/results/multi_run_statistics.csv")
    
    return stats


def generate_latex_table(stats: pd.DataFrame):
    """Generate LaTeX table with statistics for paper"""
    
    latex = r"""\begin{table}[htbp]
\centering
\caption{Multi-Run Performance Statistics (30 independent runs)}
\label{tab:multi-run-stats}
\begin{tabular}{lcccc}
\toprule
\textbf{Algorithm} & \textbf{Cost (\$)} & \textbf{Latency (ms)} & \textbf{Time (ms)} & \textbf{Success Rate} \\
\midrule
"""
    
    for algorithm in ['CMOv4', 'GA', 'GreedyCost', 'GreedyLatency', 'Random', 'WeightedSum']:
        if algorithm in stats.index:
            cost_mean = stats.loc[algorithm, ('cost', 'mean')]
            cost_std = stats.loc[algorithm, ('cost', 'std')]
            lat_mean = stats.loc[algorithm, ('latency', 'mean')]
            lat_std = stats.loc[algorithm, ('latency', 'std')]
            time_mean = stats.loc[algorithm, ('time_ms', 'mean')]
            time_std = stats.loc[algorithm, ('time_ms', 'std')]
            success = stats.loc[algorithm, ('success', 'sum')]
            total = stats.loc[algorithm, ('cost', 'count')]
            
            latex += f"{algorithm} & ${cost_mean:.2f} \\pm {cost_std:.2f}$ & ${lat_mean:.2f} \\pm {lat_std:.2f}$ & ${time_mean:.2f} \\pm {time_std:.2f}$ & {int(success)}/{int(total)} \\\\\n"
    
    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""
    
    with open('experiments/results/table_multi_run.tex', 'w') as f:
        f.write(latex)
    
    print(f"✓ LaTeX table generated: experiments/results/table_multi_run.tex")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run multi-run experiment for journal publication')
    parser.add_argument('--runs', type=int, default=30, help='Number of runs per algorithm (default: 30)')
    args = parser.parse_args()
    
    start_time = time.time()
    
    df, stats = run_multi_experiment(n_runs=args.runs)
    generate_latex_table(stats)
    
    total_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("✓ MULTI-RUN EXPERIMENT COMPLETE!")
    print("="*80)
    print(f"Total runtime: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Results saved in: experiments/results/")
    print(f"  - multi_run_results.csv (raw data)")
    print(f"  - multi_run_statistics.csv (summary statistics)")
    print(f"  - table_multi_run.tex (LaTeX table for paper)")
    print("="*80)
