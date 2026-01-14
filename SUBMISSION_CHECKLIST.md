# Submission Checklist

Minimal checklist to validate the implementation and experiments before
sharing this repository or submitting an associated paper.

## 1. Tests & Health Checks

Run these from the project root:

- **Backend tests**  
  Ensures pricing, optimization, explainability, and API behaviour are
  consistent with the documentation.

  ```bash
  cd "/Users/florinolariu/Downloads/journalimplementationver2 5"
  python3 -m pytest backend/tests -q
  ```

- **Experiment smoke tests**  
  Ensures experiment harnesses still run and emit the core artefacts
  used in the paper and markdown docs.

  ```bash
  cd "/Users/florinolariu/Downloads/journalimplementationver2 5"
  python3 -m pytest experiments/tests -q
  ```

Both commands should complete with all tests passing (1 backend test is
expected to be skipped).

## 2. Regenerating Experiment Artefacts (Optional but Recommended)

If you want to fully regenerate all tables/plots before submission:

- **Run all experiments (full run)**

  ```bash
  cd "/Users/florinolariu/Downloads/journalimplementationver2 5"
  python3 experiments/run_all_experiments.py
  ```

  This will (re)generate:
  - Multi-run statistics and LaTeX tables
  - GA convergence data and plots
  - Statistical tests tables
  - NSGA-II / MOEA/D CSV outputs (when pymoo is available)

  Note: this can take several hours; use the smoke tests above for quick
  validation.

## 3. Mapping Docs to Paper Sections

Use these documents when wiring code/results into the paper:

- **System overview, API, and pipeline**  
  `backend/EXPLANATION.md`

- **Baselines and 30-run multi-experiment results**  
  `backend/BASELINE_IMPLEMENTATION.md`

- **Scalability analysis and GA convergence/plateau justification**  
  `backend/SCALABILITY_IMPLEMENTATION.md`

- **Pareto frontier, NSGA-II / MOEA/D / Oracle snapshot**  
  `backend/PARETO_IMPLEMENTATION.md`

- **Experiment scripts, outputs, and test mapping**  
  `experiments/README.md`

## 4. Final Pre-Submission Sanity Checks

- Backend starts and main flows are functional:
  - Start via `frontend/start.sh` and load `http://localhost:8080`.
  - Run a CMOv3 and a CMOv4 optimization with the default constraints
    (budget 5000, latency 150ms, providers 3) and ensure results are
    returned with explanations.
- Key experiment result files exist (if not regenerated):
  - `experiments/results/multi_run_statistics.csv`
  - `experiments/results/table_multi_run.tex`
  - `experiments/results/statistical_tests.csv`
  - `experiments/results/table_statistical_tests.tex`
  - `experiments/results/ga_convergence_data.csv`
  - `experiments/results/ga_plateau_analysis.txt`

If all checklist items are satisfied, this branch can be considered
ready for review or submission from a tests + experiments +
documentation standpoint.
