"""
Master Experiment Runner for Journal Publication

Runs all three experiments in sequence:
1. Multi-run experiment (30 seeds) - ~2-4 hours
2. GA convergence analysis - ~1-2 hours  
3. Statistical tests - ~1 minute

Usage:
    python experiments/run_all_experiments.py [--quick]

Options:
    --quick: Run with reduced parameters for testing (3 runs instead of 30)
"""

import sys
import os
import time
import argparse

def check_dependencies():
    """Check if required packages are installed"""
    missing = []
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        from scipy import stats
    except ImportError:
        missing.append("scipy")
    
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")
    
    if missing:
        print("="*80)
        print("⚠ WARNING: Missing Required Dependencies")
        print("="*80)
        print(f"Please install: {', '.join(missing)}")
        print(f"\nInstall command:")
        print(f"  pip install {' '.join(missing)}")
        print("="*80)
        return False
    
    return True


def run_multi_run_experiment(n_runs: int):
    """Run multi-run experiment"""
    print("\n" + "="*80)
    print(f"STEP 1/3: MULTI-RUN EXPERIMENT ({n_runs} runs per algorithm)")
    print("="*80)
    
    # Add experiments directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    
    import multi_run_experiment
    
    df, stats = multi_run_experiment.run_multi_experiment(n_runs=n_runs)
    multi_run_experiment.generate_latex_table(stats)
    
    print(f"\n✓ Step 1 complete: Multi-run experiment with {n_runs} runs")


def run_ga_convergence():
    """Run GA convergence analysis"""
    print("\n" + "="*80)
    print("STEP 2/3: GA CONVERGENCE ANALYSIS")
    print("="*80)
    
    # Add experiments directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    
    import ga_convergence_experiment
    
    all_results, df = ga_convergence_experiment.test_ga_configurations()
    plateau_df = ga_convergence_experiment.analyze_plateau(df)
    ga_convergence_experiment.plot_convergence(df)
    
    print("\n✓ Step 2 complete: GA convergence analysis")


def run_statistical_tests():
    """Run statistical significance tests"""
    print("\n" + "="*80)
    print("STEP 3/3: STATISTICAL SIGNIFICANCE TESTS")
    print("="*80)
    
    # Add experiments directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    
    import statistical_tests
    
    df = statistical_tests.load_multi_run_results()
    test_df = statistical_tests.paired_t_test(df)
    
    if not test_df.empty:
        effect_df = statistical_tests.effect_size_analysis(df)
        statistical_tests.generate_latex_table(test_df, effect_df)
    
    print("\n✓ Step 3 complete: Statistical tests")


def main():
    parser = argparse.ArgumentParser(
        description='Run all experiments for journal publication'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test mode (3 runs instead of 30)'
    )
    parser.add_argument(
        '--skip-multi-run',
        action='store_true',
        help='Skip multi-run experiment (use existing results)'
    )
    parser.add_argument(
        '--skip-ga',
        action='store_true',
        help='Skip GA convergence analysis'
    )
    parser.add_argument(
        '--skip-stats',
        action='store_true',
        help='Skip statistical tests'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("MASTER EXPERIMENT RUNNER FOR JOURNAL PUBLICATION")
    print("="*80)
    print("\nThis will run all three experiments:")
    print("  1. Multi-run experiment (30 seeds × 6 algorithms)")
    print("  2. GA convergence analysis (3 configurations)")
    print("  3. Statistical significance tests (t-tests + Cohen's d)")
    print("\nEstimated total runtime: 3-6 hours")
    
    if args.quick:
        print("\n⚡ QUICK MODE: Running with 3 runs instead of 30")
        print("  (For testing only - not suitable for publication)")
    
    print("="*80)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot proceed without required dependencies")
        return 1
    
    # Create results directory
    os.makedirs('experiments/results', exist_ok=True)
    
    start_time = time.time()
    
    try:
        # Step 1: Multi-run experiment
        if not args.skip_multi_run:
            n_runs = 3 if args.quick else 30
            run_multi_run_experiment(n_runs)
        else:
            print("\n⏭ Skipping multi-run experiment (using existing results)")
        
        # Step 2: GA convergence
        if not args.skip_ga:
            run_ga_convergence()
        else:
            print("\n⏭ Skipping GA convergence analysis")
        
        # Step 3: Statistical tests
        if not args.skip_stats:
            run_statistical_tests()
        else:
            print("\n⏭ Skipping statistical tests")
        
        total_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("✓ ALL EXPERIMENTS COMPLETE!")
        print("="*80)
        print(f"Total runtime: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"\nResults saved in: experiments/results/")
        print(f"  📄 multi_run_results.csv")
        print(f"  📄 multi_run_statistics.csv")
        print(f"  📄 table_multi_run.tex")
        print(f"  📄 ga_convergence_data.csv")
        print(f"  📊 ga_convergence_plot.png")
        print(f"  📊 ga_convergence_latency.png")
        print(f"  📄 ga_plateau_analysis.txt")
        print(f"  📄 statistical_tests.csv")
        print(f"  📄 effect_sizes.csv")
        print(f"  📄 table_statistical_tests.tex")
        print("\n🎓 Ready for journal submission!")
        print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during experiment execution:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
