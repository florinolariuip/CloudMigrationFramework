#!/usr/bin/env python3
"""
CMO Experiment Runner — portable bootstrap script
==================================================
Run this from the root of 'journalimplementationver2 5' with:

    python3 run_experiments.py [--quick]

Options:
    --quick   Use 5 seeds instead of 30 (faster, for testing)

Requirements:
    pip install experta==1.9.4 networkx==3.3 numpy pandas

This script patches the Python 3.10+ collections compatibility issue
automatically before importing any CMO modules.
"""

import sys, os, collections, collections.abc

# ── Compatibility patch (Python 3.10+) ────────────────────────────────────
for _n in ('Mapping', 'MutableMapping', 'Sequence', 'Callable',
           'Iterator', 'Iterable', 'MutableSet', 'MutableSequence'):
    if not hasattr(collections, _n):
        setattr(collections, _n, getattr(collections.abc, _n))

# ── Path setup ─────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# If a .venv exists alongside the code, append its site-packages so that
# system numpy takes precedence over the bundled one (avoids ABI mismatch).
venv_sp = os.path.join(ROOT, '.venv', 'lib', 'python3.13', 'site-packages')
if os.path.isdir(venv_sp):
    sys.path.append(venv_sp)

# ── Verify key imports ─────────────────────────────────────────────────────
import importlib, textwrap
missing = []
for pkg in ('numpy', 'experta', 'networkx', 'pandas'):
    try:
        importlib.import_module(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"[ERROR] Missing packages: {', '.join(missing)}")
    print("Install with:  pip install " + ' '.join(missing))
    sys.exit(1)

print("✓ All dependencies found\n")

# ── Run experiments ────────────────────────────────────────────────────────
quick = '--quick' in sys.argv
runs  = '5' if quick else '30'

experiments = [
    ('Multi-run (30 seeds)',     'experiments/multi_run_experiment.py',     ['--runs', runs]),
    ('Statistical tests',        'experiments/statistical_tests.py',        []),
    ('Netflix GA + MCDA',        'experiments/netflix_ga_mcda_experiment.py', []),
    ('GA convergence analysis',  'experiments/ga_convergence_experiment.py', []),
    ('Pareto summary',           'experiments/pareto_summary_experiment.py', []),
]

import runpy, time

for name, script_rel, args in experiments:
    script = os.path.join(ROOT, script_rel)
    if not os.path.exists(script):
        print(f"[SKIP] {name} — script not found: {script_rel}")
        continue
    print(f"{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")
    sys.argv = [script] + args
    t0 = time.time()
    try:
        runpy.run_path(script, run_name='__main__')
        elapsed = time.time() - t0
        print(f"\n✓ {name} completed in {elapsed:.1f}s\n")
    except SystemExit:
        pass
    except Exception as e:
        print(f"\n[WARNING] {name} raised an exception: {e}")
        print("Continuing with next experiment...\n")

print("\n" + "="*60)
print("ALL EXPERIMENTS DONE")
print(f"Results saved in:  {os.path.join(ROOT, 'experiments', 'results')}")
print("="*60)
