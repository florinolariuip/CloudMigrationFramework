"""
Generate figures and tables from experiment results in backend/results/
Outputs publication-ready .png/.csv/.md files.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# 1. Load experiment results (assume CSV format for each algorithm)
def load_results():
    # Example: expects files like nsga2_results.csv, moead_results.csv, baselines_results.csv
    data = {}
    for algo in ['nsga2', 'moead', 'baselines']:
        path = os.path.join(RESULTS_DIR, f'{algo}_results.csv')
        if os.path.exists(path):
            data[algo] = pd.read_csv(path)
    return data

def plot_pareto_frontier(data):
    # Use NSGA-II results as example
    if 'nsga2' not in data:
        return
    df = data['nsga2']
    plt.figure(figsize=(6,4))
    plt.scatter(df['cost'], df['latency'], c='royalblue', label='NSGA-II Pareto')
    plt.xlabel('Cost ($)')
    plt.ylabel('Latency (ms)')
    plt.title('Pareto Frontier (Cost vs Latency)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'pareto_frontier.png'))
    plt.close()

def plot_hypervolume_trend(data):
    # Example: aggregate hypervolume for each algorithm
    algos = []
    hypervolumes = []
    for algo, df in data.items():
        if 'hypervolume' in df.columns:
            algos.append(algo.upper())
            hypervolumes.append(df['hypervolume'].mean())
    if not algos:
        return
    plt.figure(figsize=(6,4))
    plt.bar(algos, hypervolumes, color=['royalblue','seagreen','orange'][:len(algos)])
    plt.ylabel('Hypervolume')
    plt.title('Hypervolume Trend Across Algorithms')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'hypervolume_trend.png'))
    plt.close()

def save_tables_as_markdown(data):
    md = '# Experiment Results\n\n'
    for algo, df in data.items():
        md += f'## {algo.upper()}\n\n'
        md += df.head(10).to_markdown(index=False) + '\n\n'
    with open(os.path.join(RESULTS_DIR, 'experiment_tables.md'), 'w') as f:
        f.write(md)

def save_dynamic_explanations(data):
    """Generate dynamic explanations for experiment results, figures, and tables."""
    lines = [
        '# Experiment Explanations',
        '',
        'This file is dynamically generated to provide explanations for experiment results, figures, and tables. It is updated each time experiments are run.',
        '',
        '---',
        '',
        '### Pricing Data Sources',
        '🔸 **AWS**: [Public Pricing API](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json)',
        '🔸 **Azure**: [Retail Prices API](https://prices.azure.com/api/retail/prices)',
        '🔸 **GCP**: [Public Pricing API](https://cloud.google.com/skus/)',
        '',
        '---',
    ]
    # Pareto frontier explanation
    if 'nsga2' in data and not data['nsga2'].empty:
        df = data['nsga2']
        n_points = len(df)
        min_cost = df['cost'].min()
        min_latency = df['latency'].min()
        lines.append(f"## Pareto Frontier (NSGA-II)")
        lines.append(f"- Number of Pareto-optimal solutions: **{n_points}**.")
        lines.append(f"- Minimum cost found: **${min_cost:,.2f}**.")
        lines.append(f"- Minimum latency found: **{min_latency:.2f} ms**.")
        lines.append(f"- Each point represents a trade-off between cost and latency where no other solution is strictly better in both.")
        lines.append('')
    # Hypervolume trend explanation
    algos = []
    hypervolumes = []
    for algo, df in data.items():
        if 'hypervolume' in df.columns:
            algos.append(algo.upper())
            hypervolumes.append(df['hypervolume'].mean())
    if algos:
        lines.append('## Hypervolume Trend')
        for a, h in zip(algos, hypervolumes):
            lines.append(f'- **{a}** mean hypervolume: **{h:.3f}**')
        lines.append('Higher hypervolume indicates better coverage of the Pareto frontier (more diverse and optimal solutions).')
        lines.append('')
    # Baseline explanation
    if 'baselines' in data and not data['baselines'].empty:
        df = data['baselines']
        lines.append('## Baseline Algorithms')
        for idx, row in df.iterrows():
            lines.append(f"- **{row['algorithm']}**: Cost = ${row['cost']}, Latency = {row['latency']} ms, Success = {row.get('success', 'N/A')}")
        lines.append('Baselines provide reference points for evaluating the optimizer. Lower cost/latency and higher success indicate better performance.')
        lines.append('')
    # General explanation
    lines.append('---')
    lines.append('These explanations are generated based on the latest experiment results. For more details, see the documentation and code comments.')
    with open(os.path.join(RESULTS_DIR, 'experiment_explanations.md'), 'w') as f:
        f.write('\n'.join(lines))

def main():
    data = load_results()
    if not data:
        print("No experiment CSVs found in results/. Skipping figure/table generation.")
        return
    plot_pareto_frontier(data)
    plot_hypervolume_trend(data)
    save_tables_as_markdown(data)
    save_dynamic_explanations(data)
    print("Figures, tables, and explanations generated in backend/results/.")

if __name__ == "__main__":
    main()
