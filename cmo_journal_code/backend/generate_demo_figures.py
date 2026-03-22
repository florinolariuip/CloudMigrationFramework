import os
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

# Example Pareto Frontier plot
def plot_pareto_frontier():
    # Dummy data for demonstration
    costs = np.array([170, 200, 226, 255, 300])
    latencies = np.array([11.2, 10.8, 10.2, 10.0, 9.8])
    plt.figure(figsize=(6,4))
    plt.plot(costs, latencies, 'o-', color='royalblue', label='Pareto Frontier')
    plt.xlabel('Cost ($)')
    plt.ylabel('Latency (ms)')
    plt.title('Pareto Frontier (Cost vs Latency)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'pareto_frontier.png'))
    plt.close()

# Example Hypervolume Trend plot
def plot_hypervolume_trend():
    # Dummy data for demonstration
    algorithms = ['Random', 'Greedy', 'NSGA-II', 'MOEA/D']
    hypervolumes = [400, 600, 1200, 1180]
    plt.figure(figsize=(6,4))
    plt.bar(algorithms, hypervolumes, color=['gray','orange','royalblue','seagreen'])
    plt.ylabel('Hypervolume')
    plt.title('Hypervolume Trend Across Algorithms')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'hypervolume_trend.png'))
    plt.close()

if __name__ == "__main__":
    plot_pareto_frontier()
    plot_hypervolume_trend()
    print("Demo figures generated in backend/results/")
