"""Pareto/NSGA-II/MOEA-D/Oracle summary experiment.

Runs the Pareto-based experiments for N = 5, 10, 15 components
and saves a compact CSV/Markdown summary that can be used to
update `backend/PARETO_IMPLEMENTATION.md` tables.

NOTE: This is a scaffold; you still need to plug in the actual
NSGA-II/MOEA-D/Oracle experiment calls where indicated.
"""

from __future__ import annotations

import os
import csv
from dataclasses import dataclass, asdict
from typing import List

# TODO: import your real experiment functions here when available
# from experiments.nsga_experiment import run_nsga_experiment
# from experiments.moead_experiment import run_moead_experiment
# from experiments.oracle_exhaustive import run_oracle_exhaustive


@dataclass
class ParetoSummaryRow:
    n_components: int
    algorithm: str
    min_cost: float
    min_latency: float
    balanced_cost: float
    pareto_solutions: int


def ensure_results_dir() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(root, "experiments", "results")
    os.makedirs(results_dir, exist_ok=True)
    return results_dir


def run_pareto_summaries() -> List[ParetoSummaryRow]:
    """Run NSGA-II, MOEA/D, and Oracle for N = 5,10,15 and collect summary.

    This currently uses placeholder values that match the existing
    tables in `backend/PARETO_IMPLEMENTATION.md` so that you can
    wire in the real experiment calls incrementally without
    breaking the documentation.
    """

    # Placeholder: mirrors current markdown values so the script is
    # non-destructive until real experiment functions are connected.
    rows: List[ParetoSummaryRow] = [
        ParetoSummaryRow(5, "NSGA-II", 170.77, 10.00, 226.01, 7),
        ParetoSummaryRow(5, "MOEA/D", 170.77, 10.00, 226.01, 7),
        ParetoSummaryRow(5, "Oracle", 170.77, 10.00, 226.01, 7),
        ParetoSummaryRow(10, "NSGA-II", 530.87, 9.50, 543.79, 3),
        ParetoSummaryRow(10, "MOEA/D", 530.87, 9.50, 543.79, 3),
        ParetoSummaryRow(10, "Oracle", 530.87, 9.50, 543.79, 3),
        ParetoSummaryRow(15, "NSGA-II", 676.37, 9.00, 676.37, 1),
        ParetoSummaryRow(15, "MOEA/D", 676.37, 9.00, 676.37, 1),
        ParetoSummaryRow(15, "Oracle", 676.37, 9.00, 676.37, 1),
    ]

    # Example of where real calls would go:
    # for n in [5, 10, 15]:
    #     nsga_res = run_nsga_experiment(n)
    #     rows.append(ParetoSummaryRow(
    #         n_components=n,
    #         algorithm="NSGA-II",
    #         min_cost=nsga_res.min_cost,
    #         min_latency=nsga_res.min_latency,
    #         balanced_cost=nsga_res.balanced_cost,
    #         pareto_solutions=nsga_res.pareto_count,
    #     ))
    #     ... similarly for MOEA/D and Oracle ...

    return rows


def save_csv(rows: List[ParetoSummaryRow], path: str) -> None:
    fieldnames = [
        "n_components",
        "algorithm",
        "min_cost",
        "min_latency",
        "balanced_cost",
        "pareto_solutions",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def save_markdown(rows: List[ParetoSummaryRow], path: str) -> None:
    """Generate a Markdown table snippet matching PARETO_IMPLEMENTATION.md."""
    header = "| N | Algorithm | Min Cost | Min Latency | Balanced | Pareto Solutions |\n"
    sep = "|---:|---|---:|---:|---:|---:|\n"
    lines = [header, sep]

    for row in rows:
        lines.append(
            f"| {row.n_components} | {row.algorithm} | "
            f"{row.min_cost:.2f} | {row.min_latency:.2f} | "
            f"{row.balanced_cost:.2f} | {row.pareto_solutions} |\n"
        )

    with open(path, "w") as f:
        f.writelines(lines)


def main() -> None:
    results_dir = ensure_results_dir()
    rows = run_pareto_summaries()

    csv_path = os.path.join(results_dir, "pareto_summary.csv")
    md_path = os.path.join(results_dir, "pareto_summary_table.md")

    save_csv(rows, csv_path)
    save_markdown(rows, md_path)

    print(f"Saved Pareto summary CSV to: {csv_path}")
    print(f"Saved Pareto summary Markdown table to: {md_path}")
    print("\nYou can copy the Markdown table into `backend/PARETO_IMPLEMENTATION.md` when you\nreplace the placeholder values with real experiment outputs.")


if __name__ == "__main__":
    main()
