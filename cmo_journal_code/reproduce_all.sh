#!/bin/bash
# Reproduce all experiments, aggregate results, and generate figures/tables
set -e

# Activate venv if exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Install requirements
pip install -r backend/requirements.txt

# Run all experiments (Python script should orchestrate all baselines, pymoo, oracle, etc.)
python backend/run_all_experiments.py

# Generate figures and tables (assume script outputs to backend/results/)
python backend/generate_figures_tables.py

echo "All experiments reproduced. Results in backend/results/"
