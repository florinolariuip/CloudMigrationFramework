import matplotlib.pyplot as plt

# Data from your results
points = [
    # Algorithm, Cost, Latency, Color, Marker, Label
    ("MOEA/D", 676.37, 9.0, "blue", "o", "MOEA/D"),
    ("NSGA-II", 676.37, 9.0, "green", "o", "NSGA-II"),
    ("Random Selection", 2097.99, 9.53, "red", "x", "Random"),
    ("Greedy-Cost", 577.73, 9.4, "purple", "s", "Greedy-Cost"),
    ("Greedy-Latency", 676.37, 9.0, "orange", "s", "Greedy-Latency"),
    ("Genetic Algorithm", 638.41, 9.13, "cyan", "D", "GA"),
    ("Weighted Sum", 624.1, 9.0, "magenta", "D", "Weighted Sum"),
]

# Offsets to avoid exact overlap (latency jitter in ms, cost jitter in $)
offsets = {
    "MOEA/D": (0.03, 0.0),         # shift slightly right
    "NSGA-II": (-0.03, 0.0),       # shift slightly left
    "Greedy-Latency": (0.0, 0.0),  # keep original
}

plt.figure(figsize=(8, 6))
for alg, cost, latency, color, marker, label in points:
    dx, dy = offsets.get(label, (0.0, 0.0))
    x = latency + dx
    y = cost + dy
    plt.scatter(
        x, y,
        color=color,
        marker=marker,
        s=140,
        edgecolors="black",
        linewidths=0.8,
        alpha=0.95,
        zorder=3 if label in ("MOEA/D", "NSGA-II") else 2,
        label=label
    )
    # Annotate points to ensure visibility
    plt.annotate(
        label,
        (x, y),
        textcoords="offset points",
        xytext=(6, -10),
        fontsize=9,
        color=color,
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, lw=0.6, alpha=0.7)
    )

plt.xlabel("Latency (ms)", fontsize=14)
plt.ylabel("Cost ($)", fontsize=14)
plt.title("Conceptual Pareto Front: Cost vs. Latency (N=15)", fontsize=16)
plt.gca().invert_yaxis()  # Cost decreases from top to bottom
# Place legend below the plot to avoid covering points
plt.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.12),
    ncol=3,
    fontsize=9,
    framealpha=0.85
)
plt.grid(True, linestyle='--', alpha=0.6)
# Add extra bottom margin for the legend row
plt.tight_layout(rect=[0, 0.15, 1, 1])
plt.savefig("pareto_frontier.png", dpi=300)
plt.show()
