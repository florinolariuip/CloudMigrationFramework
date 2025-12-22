"""
Statistical Significance Tests for Journal Publication

Performs paired t-tests and Cohen's d effect size calculations to prove
that CMOv4 is statistically significantly better than baselines.

This addresses reviewer concern: "No statistical tests, just point comparisons"

Requires: multi_run_results.csv from multi-run experiment

Output:
- experiments/results/statistical_tests.csv (t-test results)
- experiments/results/effect_sizes.csv (Cohen's d values)
- experiments/results/table_statistical_tests.tex (LaTeX table)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from typing import Dict, List


def load_multi_run_results() -> pd.DataFrame:
    """Load results from multi-run experiment"""
    
    results_file = 'experiments/results/multi_run_results.csv'
    
    if not os.path.exists(results_file):
        raise FileNotFoundError(
            f"Multi-run results not found: {results_file}\n"
            f"Please run: python experiments/multi_run_experiment.py first"
        )
    
    df = pd.read_csv(results_file)
    print(f"✓ Loaded {len(df)} results from {results_file}")
    print(f"  Algorithms: {df['algorithm'].unique().tolist()}")
    print(f"  Runs per algorithm: {df.groupby('algorithm').size().iloc[0]}")
    
    return df


def paired_t_test(df: pd.DataFrame) -> pd.DataFrame:
    """Perform paired t-tests between CMOv4 and baselines"""
    
    try:
        from scipy import stats
    except ImportError:
        print("⚠ Warning: scipy not installed. Cannot perform t-tests.")
        print("  Install with: pip install scipy")
        return pd.DataFrame()
    
    print("\n" + "="*80)
    print("PAIRED T-TEST RESULTS (CMOv4 vs Baselines)")
    print("="*80)
    
    # Get CMOv4 results
    cmov4_data = df[df['algorithm'] == 'CMOv4']
    
    if len(cmov4_data) == 0:
        raise ValueError("No CMOv4 results found in dataset")
    
    cmov4_cost = cmov4_data['cost'].values
    cmov4_latency = cmov4_data['latency'].values
    
    algorithms = ['GA', 'GreedyCost', 'GreedyLatency', 'Random', 'WeightedSum']
    
    print(f"\n{'Algorithm':<20} {'Metric':<10} {'t-statistic':<15} {'p-value':<15} {'Significant?':<15} {'Direction'}")
    print("-"*100)
    
    test_results = []
    
    for alg in algorithms:
        alg_data = df[df['algorithm'] == alg]
        
        if len(alg_data) == 0:
            print(f"{alg}: No data found")
            continue
        
        alg_cost = alg_data['cost'].values
        alg_latency = alg_data['latency'].values
        
        # Ensure same length
        min_len = min(len(cmov4_cost), len(alg_cost))
        
        # Cost comparison (lower is better, so CMOv4 should be lower)
        t_cost, p_cost = stats.ttest_rel(cmov4_cost[:min_len], alg_cost[:min_len])
        sig_cost = "✓ Yes (p<0.05)" if p_cost < 0.05 else "✗ No"
        direction_cost = "CMOv4 better" if np.mean(cmov4_cost) < np.mean(alg_cost) else "Baseline better"
        
        # Latency comparison (lower is better, so CMOv4 should be lower)
        t_lat, p_lat = stats.ttest_rel(cmov4_latency[:min_len], alg_latency[:min_len])
        sig_lat = "✓ Yes (p<0.05)" if p_lat < 0.05 else "✗ No"
        direction_lat = "CMOv4 better" if np.mean(cmov4_latency) < np.mean(alg_latency) else "Baseline better"
        
        print(f"{alg:<20} {'Cost':<10} {t_cost:<15.3f} {p_cost:<15.6f} {sig_cost:<15} {direction_cost}")
        print(f"{'':<20} {'Latency':<10} {t_lat:<15.3f} {p_lat:<15.6f} {sig_lat:<15} {direction_lat}")
        
        test_results.append({
            'algorithm': alg,
            'metric': 'cost',
            't_statistic': t_cost,
            'p_value': p_cost,
            'significant': p_cost < 0.05,
            'cmov4_mean': np.mean(cmov4_cost),
            'baseline_mean': np.mean(alg_cost),
            'difference': np.mean(cmov4_cost) - np.mean(alg_cost)
        })
        
        test_results.append({
            'algorithm': alg,
            'metric': 'latency',
            't_statistic': t_lat,
            'p_value': p_lat,
            'significant': p_lat < 0.05,
            'cmov4_mean': np.mean(cmov4_latency),
            'baseline_mean': np.mean(alg_latency),
            'difference': np.mean(cmov4_latency) - np.mean(alg_latency)
        })
    
    test_df = pd.DataFrame(test_results)
    test_df.to_csv('experiments/results/statistical_tests.csv', index=False)
    print(f"\n✓ Statistical tests saved: experiments/results/statistical_tests.csv")
    
    return test_df


def cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size
    
    Interpretation:
    - |d| < 0.2: Negligible
    - 0.2 <= |d| < 0.5: Small
    - 0.5 <= |d| < 0.8: Medium  
    - |d| >= 0.8: Large
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    
    # Cohen's d
    d = (np.mean(group1) - np.mean(group2)) / pooled_std
    
    return d


def interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d value"""
    d_abs = abs(d)
    if d_abs < 0.2:
        return "Negligible"
    elif d_abs < 0.5:
        return "Small"
    elif d_abs < 0.8:
        return "Medium"
    else:
        return "Large"


def effect_size_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Cohen's d effect sizes"""
    
    print("\n" + "="*80)
    print("EFFECT SIZE ANALYSIS (Cohen's d)")
    print("="*80)
    
    cmov4_data = df[df['algorithm'] == 'CMOv4']
    cmov4_cost = cmov4_data['cost'].values
    cmov4_latency = cmov4_data['latency'].values
    
    algorithms = ['GA', 'GreedyCost', 'GreedyLatency', 'Random', 'WeightedSum']
    
    print(f"\n{'Algorithm':<20} {'Cost d':<15} {'Interpretation':<15} {'Latency d':<15} {'Interpretation'}")
    print("-"*80)
    
    effect_sizes = []
    
    for alg in algorithms:
        alg_data = df[df['algorithm'] == alg]
        
        if len(alg_data) == 0:
            continue
        
        alg_cost = alg_data['cost'].values
        alg_latency = alg_data['latency'].values
        
        # Ensure same length
        min_len = min(len(cmov4_cost), len(alg_cost))
        
        # Negative d means CMOv4 is better (lower cost/latency)
        d_cost = cohens_d(cmov4_cost[:min_len], alg_cost[:min_len])
        d_lat = cohens_d(cmov4_latency[:min_len], alg_latency[:min_len])
        
        interpret_cost = interpret_cohens_d(d_cost)
        interpret_lat = interpret_cohens_d(d_lat)
        
        print(f"{alg:<20} {d_cost:<15.3f} {interpret_cost:<15} {d_lat:<15.3f} {interpret_lat}")
        
        effect_sizes.append({
            'algorithm': alg,
            'cost_cohens_d': d_cost,
            'cost_interpretation': interpret_cost,
            'latency_cohens_d': d_lat,
            'latency_interpretation': interpret_lat,
            'cmov4_better_cost': d_cost < 0,  # Negative means CMOv4 lower
            'cmov4_better_latency': d_lat < 0
        })
    
    effect_df = pd.DataFrame(effect_sizes)
    effect_df.to_csv('experiments/results/effect_sizes.csv', index=False)
    print(f"\n✓ Effect sizes saved: experiments/results/effect_sizes.csv")
    
    return effect_df


def generate_latex_table(test_df: pd.DataFrame, effect_df: pd.DataFrame):
    """Generate LaTeX table with statistical tests for paper"""
    
    latex = r"""\begin{table}[htbp]
\centering
\caption{Statistical Significance Tests (CMOv4 vs Baselines, $n=30$, paired t-test)}
\label{tab:statistical-tests}
\begin{tabular}{lccccc}
\toprule
\textbf{Algorithm} & \textbf{Metric} & \textbf{t-statistic} & \textbf{p-value} & \textbf{Cohen's d} & \textbf{Effect Size} \\
\midrule
"""
    
    for alg in ['GA', 'GreedyCost', 'GreedyLatency', 'Random', 'WeightedSum']:
        # Cost row
        t_cost_row = test_df[(test_df['algorithm'] == alg) & (test_df['metric'] == 'cost')]
        e_cost_row = effect_df[effect_df['algorithm'] == alg]
        
        if len(t_cost_row) > 0 and len(e_cost_row) > 0:
            t_stat = t_cost_row.iloc[0]['t_statistic']
            p_val = t_cost_row.iloc[0]['p_value']
            cohens = e_cost_row.iloc[0]['cost_cohens_d']
            interp = e_cost_row.iloc[0]['cost_interpretation']
            
            # Add significance stars
            sig_marker = "***" if p_val < 0.001 else \
                         "**" if p_val < 0.01 else \
                         "*" if p_val < 0.05 else ""
            
            latex += f"{alg} & Cost & {t_stat:.2f} & {p_val:.4f}{sig_marker} & {cohens:.2f} & {interp} \\\\\n"
            
        # Latency row
        t_lat_row = test_df[(test_df['algorithm'] == alg) & (test_df['metric'] == 'latency')]
        
        if len(t_lat_row) > 0 and len(e_cost_row) > 0:
            t_stat = t_lat_row.iloc[0]['t_statistic']
            p_val = t_lat_row.iloc[0]['p_value']
            cohens = e_cost_row.iloc[0]['latency_cohens_d']
            interp = e_cost_row.iloc[0]['latency_interpretation']
            
            sig_marker = "***" if p_val < 0.001 else \
                         "**" if p_val < 0.01 else \
                         "*" if p_val < 0.05 else ""
            
            latex += f"{'':<5} & Latency & {t_stat:.2f} & {p_val:.4f}{sig_marker} & {cohens:.2f} & {interp} \\\\\n"
        
        latex += "\\midrule\n"
    
    latex = latex.rstrip("\\midrule\n") + "\n"  # Remove last midrule
    
    latex += r"""\bottomrule
\multicolumn{6}{l}{\footnotesize $^{*}p<0.05$, $^{**}p<0.01$, $^{***}p<0.001$. Negative d indicates CMOv4 is better (lower cost/latency).} \\
\end{tabular}
\end{table}
"""
    
    with open('experiments/results/table_statistical_tests.tex', 'w') as f:
        f.write(latex)
    
    print(f"✓ LaTeX table generated: experiments/results/table_statistical_tests.tex")


if __name__ == "__main__":
    import time
    
    start_time = time.time()
    
    print("="*80)
    print("STATISTICAL SIGNIFICANCE ANALYSIS FOR JOURNAL PUBLICATION")
    print("="*80)
    
    # Load multi-run results
    df = load_multi_run_results()
    
    # Perform statistical tests
    test_df = paired_t_test(df)
    
    if not test_df.empty:
        effect_df = effect_size_analysis(df)
        generate_latex_table(test_df, effect_df)
    
    total_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("✓ STATISTICAL ANALYSIS COMPLETE!")
    print("="*80)
    print(f"Total runtime: {total_time:.2f} seconds")
    print(f"Results saved in: experiments/results/")
    print(f"  - statistical_tests.csv (t-test results)")
    print(f"  - effect_sizes.csv (Cohen's d values)")
    print(f"  - table_statistical_tests.tex (LaTeX table for paper)")
    print("\nKEY INTERPRETATION:")
    print("  - p < 0.05: Statistically significant difference")
    print("  - Cohen's d: Effect size (|d| >= 0.8 = large effect)")
    print("  - Negative d: CMOv4 is better (lower cost/latency)")
    print("="*80)
