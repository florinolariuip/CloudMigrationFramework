"""
GA Convergence Analysis for Journal Publication

Tests Genetic Algorithm with different evaluation budgets (5K, 10K, 20K) 
to prove that GA plateaus and justify the 5K baseline choice.

This addresses reviewer concern: "Is the GA baseline too weak with only 5K evaluations?"

Output:
- experiments/results/ga_convergence_data.csv (convergence history)
- experiments/results/ga_convergence_plot.png (cost convergence)
- experiments/results/ga_convergence_latency.png (latency convergence)
- experiments/results/ga_plateau_analysis.txt (plateau detection)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import time
from typing import Dict, List, Any

from backend.models import Constraints
from backend.engines.baselines import baseline_genetic_algorithm


def run_ga_with_tracking(
    constraints: Constraints,
    population_size: int,
    generations: int,
    config_name: str
) -> Dict[str, Any]:
    """
    Run GA and track convergence history by modifying the baseline GA
    to return generation-by-generation statistics
    """
    
    print(f"\n{'='*60}")
    print(f"Running {config_name}")
    print(f"  Population: {population_size}, Generations: {generations}")
    print(f"  Total evaluations: {population_size * generations}")
    print(f"{'='*60}")
    
    # We need to modify the baseline GA to track convergence
    # For now, let's run multiple times with increasing generations
    convergence_history = []
    
    # Run GA with incremental generations to simulate convergence tracking
    checkpoint_gens = list(range(10, generations + 1, 10))  # Check every 10 generations
    
    for gen_limit in checkpoint_gens:
        print(f"  Checkpoint: generation {gen_limit}...", end=' ', flush=True)
        
        result = baseline_genetic_algorithm(
            constraints,
            population_size=population_size,
            generations=gen_limit,
            mutation_rate=0.1,
            crossover_rate=0.7
        )
        
        if result.success and result.solution:
            convergence_history.append({
                'config': config_name,
                'generation': gen_limit,
                'evaluations': population_size * gen_limit,
                'best_cost': result.solution.cost,
                'best_latency': result.solution.latency,
                'time_ms': result.execution_time_ms
            })
            print(f"✓ Cost: ${result.solution.cost:.2f}")
        else:
            print(f"✗ Failed")
    
    return {
        'config_name': config_name,
        'final_cost': convergence_history[-1]['best_cost'] if convergence_history else None,
        'final_latency': convergence_history[-1]['best_latency'] if convergence_history else None,
        'convergence_history': convergence_history
    }


def test_ga_configurations():
    """Test GA with different evaluation budgets"""
    
    print("="*80)
    print("GA CONVERGENCE ANALYSIS FOR JOURNAL PUBLICATION")
    print("="*80)
    
    constraints = Constraints(
        maxBudget=5000,
        maxLatency=150,
        maxProviders=3
    )
    
    print(f"\nConstraints: Budget=${constraints.maxBudget}, Latency={constraints.maxLatency}ms, Providers={constraints.maxProviders}")
    
    configurations = [
        {'pop': 50, 'gen': 100, 'name': 'GA-5K (baseline)'},    # 5,000 evals
        {'pop': 100, 'gen': 100, 'name': 'GA-10K'},             # 10,000 evals
        {'pop': 200, 'gen': 100, 'name': 'GA-20K'},             # 20,000 evals
    ]
    
    all_results = {}
    all_convergence = []
    
    for config in configurations:
        result = run_ga_with_tracking(
            constraints,
            population_size=config['pop'],
            generations=config['gen'],
            config_name=config['name']
        )
        
        all_results[config['name']] = result
        all_convergence.extend(result['convergence_history'])
        
        if result['final_cost']:
            print(f"\n  Final result: Cost=${result['final_cost']:.2f}, Latency={result['final_latency']:.2f}ms")
    
    # Create results directory
    os.makedirs('experiments/results', exist_ok=True)
    
    # Save convergence data
    df = pd.DataFrame(all_convergence)
    df.to_csv('experiments/results/ga_convergence_data.csv', index=False)
    print(f"\n✓ Convergence data saved: experiments/results/ga_convergence_data.csv")
    
    return all_results, df


def analyze_plateau(df: pd.DataFrame):
    """Detect when GA plateaus (improvement < 1%)"""
    
    print("\n" + "="*80)
    print("PLATEAU ANALYSIS")
    print("="*80)
    
    plateau_report = []
    
    for config_name in df['config'].unique():
        config_df = df[df['config'] == config_name].sort_values('generation')
        
        # Calculate improvement rate
        config_df = config_df.copy()
        config_df['cost_improvement'] = config_df['best_cost'].diff().abs()
        config_df['improvement_pct'] = (config_df['cost_improvement'] / config_df['best_cost']) * 100
        
        # Find plateau point (where improvement drops below 0.5%)
        plateau_rows = config_df[config_df['improvement_pct'] < 0.5]
        
        if len(plateau_rows) > 0:
            plateau_gen = plateau_rows.iloc[0]['generation']
            plateau_evals = plateau_rows.iloc[0]['evaluations']
            final_cost = config_df.iloc[-1]['best_cost']
            plateau_cost = plateau_rows.iloc[0]['best_cost']
            
            print(f"\n{config_name}:")
            print(f"  Plateaus at: Generation {plateau_gen} ({plateau_evals} evaluations)")
            print(f"  Cost at plateau: ${plateau_cost:.2f}")
            print(f"  Final cost: ${final_cost:.2f}")
            print(f"  Improvement after plateau: ${plateau_cost - final_cost:.2f} ({((plateau_cost - final_cost)/plateau_cost * 100):.2f}%)")
            
            # Calculate average improvement in last 20% of generations
            last_20pct_idx = int(len(config_df) * 0.8)
            late_improvements = config_df.iloc[last_20pct_idx:]['improvement_pct'].mean()
            print(f"  Average improvement in last 20% of runs: {late_improvements:.4f}%")
            
            plateau_report.append({
                'config': config_name,
                'plateau_generation': plateau_gen,
                'plateau_evaluations': plateau_evals,
                'cost_at_plateau': plateau_cost,
                'final_cost': final_cost,
                'improvement_after_plateau_pct': ((plateau_cost - final_cost)/plateau_cost * 100)
            })
        else:
            print(f"\n{config_name}: Still improving significantly")
            plateau_report.append({
                'config': config_name,
                'plateau_generation': None,
                'plateau_evaluations': None,
                'cost_at_plateau': None,
                'final_cost': config_df.iloc[-1]['best_cost'],
                'improvement_after_plateau_pct': None
            })
    
    # Save plateau analysis
    plateau_df = pd.DataFrame(plateau_report)
    
    with open('experiments/results/ga_plateau_analysis.txt', 'w') as f:
        f.write("="*80 + "\n")
        f.write("GA PLATEAU ANALYSIS\n")
        f.write("="*80 + "\n\n")
        f.write(plateau_df.to_string(index=False))
        f.write("\n\n")
        f.write("INTERPRETATION:\n")
        f.write("- Plateau = point where improvement drops below 0.5% per generation\n")
        f.write("- If GA-5K plateaus before 5000 evals, our baseline is justified\n")
        f.write("- Minimal improvement after plateau validates evaluation budget choice\n")
    
    print(f"\n✓ Plateau analysis saved: experiments/results/ga_plateau_analysis.txt")
    
    return plateau_df


def plot_convergence(df: pd.DataFrame):
    """Generate convergence plots"""
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠ Warning: matplotlib not installed. Skipping plots.")
        print("  Install with: pip install matplotlib")
        return
    
    print("\nGenerating convergence plots...")
    
    # Cost convergence plot
    plt.figure(figsize=(12, 6))
    
    for config_name in ['GA-5K (baseline)', 'GA-10K', 'GA-20K']:
        config_df = df[df['config'] == config_name].sort_values('evaluations')
        if len(config_df) > 0:
            plt.plot(config_df['evaluations'], config_df['best_cost'], 
                    label=config_name, linewidth=2, marker='o', markersize=4)
    
    plt.xlabel('Number of Evaluations', fontsize=12)
    plt.ylabel('Best Cost Found ($)', fontsize=12)
    plt.title('GA Convergence Analysis: Impact of Evaluation Budget', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11, loc='upper right')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    plt.savefig('experiments/results/ga_convergence_plot.png', dpi=300, bbox_inches='tight')
    print("✓ Cost convergence plot saved: experiments/results/ga_convergence_plot.png")
    plt.close()
    
    # Latency convergence plot
    plt.figure(figsize=(12, 6))
    
    for config_name in ['GA-5K (baseline)', 'GA-10K', 'GA-20K']:
        config_df = df[df['config'] == config_name].sort_values('evaluations')
        if len(config_df) > 0:
            plt.plot(config_df['evaluations'], config_df['best_latency'], 
                    label=config_name, linewidth=2, marker='s', markersize=4)
    
    plt.xlabel('Number of Evaluations', fontsize=12)
    plt.ylabel('Best Latency Found (ms)', fontsize=12)
    plt.title('GA Convergence Analysis: Latency Optimization', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11, loc='upper right')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    plt.savefig('experiments/results/ga_convergence_latency.png', dpi=300, bbox_inches='tight')
    print("✓ Latency convergence plot saved: experiments/results/ga_convergence_latency.png")
    plt.close()


if __name__ == "__main__":
    start_time = time.time()
    
    all_results, df = test_ga_configurations()
    plateau_df = analyze_plateau(df)
    plot_convergence(df)
    
    total_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("✓ GA CONVERGENCE ANALYSIS COMPLETE!")
    print("="*80)
    print(f"Total runtime: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Results saved in: experiments/results/")
    print(f"  - ga_convergence_data.csv (convergence history)")
    print(f"  - ga_convergence_plot.png (cost convergence)")
    print(f"  - ga_convergence_latency.png (latency convergence)")
    print(f"  - ga_plateau_analysis.txt (plateau detection)")
    print("\nKEY FINDINGS:")
    for _, row in plateau_df.iterrows():
        if row['plateau_evaluations']:
            print(f"  {row['config']}: Plateaus at {row['plateau_evaluations']} evaluations")
    print("="*80)
