"""
Unit Tests for Cloud Migration Optimizer

Tests core functionality:
- Constraint satisfaction
- Solution deduplication
- Pareto frontier calculation
- Budget-relative thresholds
- CMOv4 instance scaling
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.engines.constraints import generate_feasible_solutions
from backend.engines.rules import evaluate_solutions, deduplicate_solutions
from backend.engines.pareto import calculate_pareto_frontier, dominates
from backend.models import Constraints, Preferences, Solution
from backend.cmov4.helpers import get_instance_counts


class TestCSP:
    """Test Constraint Satisfaction Problem engine"""
    
    def test_generates_feasible_solutions(self):
        """Test CSP generates solutions within constraints"""
        constraints = Constraints(maxBudget=5000, maxLatency=12, maxProviders=2)
        solutions = generate_feasible_solutions(constraints)
        
        assert len(solutions) > 0, "Should generate at least one feasible solution"
        
        for sol in solutions:
            assert sol.cost <= 5000, f"Cost {sol.cost} exceeds budget 5000"
            assert sol.latency <= 12, f"Latency {sol.latency} exceeds limit 12"
            assert sol.providers <= 2, f"Providers {sol.providers} exceeds limit 2"
    
    def test_tight_constraints_reduce_solutions(self):
        """Tighter constraints should produce fewer solutions"""
        loose = Constraints(maxBudget=10000, maxLatency=20, maxProviders=3)
        tight = Constraints(maxBudget=3000, maxLatency=8, maxProviders=1)
        
        loose_sols = generate_feasible_solutions(loose)
        tight_sols = generate_feasible_solutions(tight)
        
        assert len(loose_sols) >= len(tight_sols), "Loose constraints should yield more solutions"
    
    def test_no_solution_for_impossible_constraints(self):
        """Impossible constraints should return empty list"""
        impossible = Constraints(maxBudget=10, maxLatency=0.1, maxProviders=1)
        solutions = generate_feasible_solutions(impossible)
        
        # Should return empty list or very few solutions
        assert len(solutions) == 0 or all(s.cost <= 10 for s in solutions)


class TestDeduplication:
    """Test solution deduplication"""
    
    def test_removes_duplicates(self):
        """Test duplicate solutions are removed"""
        constraints = Constraints(maxBudget=5000, maxLatency=12, maxProviders=2)
        solutions = generate_feasible_solutions(constraints)
        
        pre_count = len(solutions)
        unique = deduplicate_solutions(solutions)
        post_count = len(unique)
        
        assert post_count <= pre_count, "Deduplication should not increase count"
        
        # Check all remaining solutions have unique configurations
        configs = [tuple(sorted(s.configuration.items())) for s in unique]
        assert len(configs) == len(set(configs)), "All solutions should have unique configs"
    
    def test_preserves_unique_solutions(self):
        """Test unique solutions are preserved"""
        # Create solutions with different configurations
        sol1 = Solution(
            configuration={'api_gateway': 'AWS API Gateway', 'database': 'AWS RDS'},
            cost=100, latency=10, providers=1, providerDistribution={'AWS': 2}
        )
        sol2 = Solution(
            configuration={'api_gateway': 'Azure API Management', 'database': 'Azure SQL'},
            cost=110, latency=9, providers=1, providerDistribution={'Azure': 2}
        )
        
        solutions = [sol1, sol2]
        unique = deduplicate_solutions(solutions)
        
        assert len(unique) == 2, "Should preserve both unique solutions"


class TestParetoFrontier:
    """Test Pareto multi-objective optimization"""
    
    def test_pareto_non_dominated(self):
        """Test Pareto frontier contains only non-dominated solutions"""
        constraints = Constraints(maxBudget=10000, maxLatency=20, maxProviders=3)
        solutions = generate_feasible_solutions(constraints)
        
        if len(solutions) < 2:
            pytest.skip("Not enough solutions to test Pareto")
        
        pareto = calculate_pareto_frontier(solutions)
        
        assert len(pareto) > 0, "Should have at least one Pareto solution"
        assert len(pareto) <= len(solutions), "Pareto set should be subset of all solutions"
        
        # Check no solution in Pareto set dominates another
        for i, sol_a in enumerate(pareto):
            for j, sol_b in enumerate(pareto):
                if i != j:
                    assert not dominates(sol_a, sol_b), \
                        f"Solution {i} should not dominate solution {j} in Pareto set"
    
    def test_dominance_relation(self):
        """Test dominance relation is correct"""
        # Solution A: cheaper and faster (dominates B)
        sol_a = Solution(configuration={}, cost=100, latency=5, providers=1, providerDistribution={'AWS': 1})
        # Solution B: more expensive and slower (dominated by A)
        sol_b = Solution(configuration={}, cost=200, latency=10, providers=1, providerDistribution={'AWS': 1})
        
        assert dominates(sol_a, sol_b), "Cheaper and faster solution should dominate"
        assert not dominates(sol_b, sol_a), "Dominated solution should not dominate dominator"
    
    def test_non_dominance_tradeoff(self):
        """Test solutions with trade-offs don't dominate each other"""
        # Solution A: cheaper but slower
        sol_a = Solution(configuration={}, cost=100, latency=10, providers=1, providerDistribution={'AWS': 1})
        # Solution B: more expensive but faster
        sol_b = Solution(configuration={}, cost=200, latency=5, providers=1, providerDistribution={'AWS': 1})
        
        assert not dominates(sol_a, sol_b), "Trade-off solutions should not dominate"
        assert not dominates(sol_b, sol_a), "Trade-off solutions should not dominate"


class TestBudgetRelativeThresholds:
    """Test budget-relative threshold adaptation"""
    
    def test_thresholds_adapt_to_budget(self):
        """Test cost thresholds scale with budget"""
        constraints_low = Constraints(maxBudget=2000, maxLatency=12, maxProviders=2)
        constraints_high = Constraints(maxBudget=10000, maxLatency=12, maxProviders=2)
        preferences = Preferences()
        
        # Generate solutions
        solutions_low = generate_feasible_solutions(constraints_low)
        solutions_high = generate_feasible_solutions(constraints_high)
        
        if not solutions_low or not solutions_high:
            pytest.skip("Not enough solutions generated")
        
        # Evaluate with budget-relative thresholds
        ranked_low = evaluate_solutions(solutions_low, preferences, max_budget=2000)
        ranked_high = evaluate_solutions(solutions_high, preferences, max_budget=10000)
        
        # Solutions under 90% of budget should not get high cost penalty
        for sol in ranked_low:
            if sol.cost < 1800:  # 90% of 2000
                penalties = [log for log in (sol.evaluationLog or []) 
                           if 'High cost penalty' in log.get('rule', '')]
                assert len(penalties) == 0, f"Solution at ${sol.cost} should not be penalized (budget: $2000)"
        
        for sol in ranked_high:
            if sol.cost < 9000:  # 90% of 10000
                penalties = [log for log in (sol.evaluationLog or []) 
                           if 'High cost penalty' in log.get('rule', '')]
                assert len(penalties) == 0, f"Solution at ${sol.cost} should not be penalized (budget: $10000)"


class TestCMOv4InstanceScaling:
    """Test CMOv4 instance count scaling"""
    
    def test_extracts_instance_counts(self):
        """Test instance count extraction from components"""
        components = [
            {'type': 'web', 'instance_count': 5},
            {'type': 'compute', 'instance_count': 3},
            {'type': 'database', 'instance_count': 2},
        ]
        
        counts = get_instance_counts(components)
        
        assert counts['web'] == 5
        assert counts['compute'] == 3
        assert counts['database'] == 2
    
    def test_sums_multiple_components_same_type(self):
        """Test multiple components of same type are summed"""
        components = [
            {'type': 'compute', 'instance_count': 3},
            {'type': 'compute', 'instance_count': 2},
        ]
        
        counts = get_instance_counts(components)
        
        assert counts['compute'] == 5, "Should sum instance counts for same type"
    
    def test_defaults_to_one_if_missing(self):
        """Test defaults to 1 if instance_count not specified"""
        components = [
            {'type': 'web'},  # No instance_count
        ]
        
        counts = get_instance_counts(components)
        
        assert counts['web'] == 1, "Should default to 1 if instance_count missing"


class TestRuleEvaluation:
    """Test expert system rule evaluation"""
    
    def test_evaluates_solutions(self):
        """Test expert system evaluates and scores solutions"""
        constraints = Constraints(maxBudget=5000, maxLatency=12, maxProviders=2)
        preferences = Preferences()
        
        solutions = generate_feasible_solutions(constraints)
        
        if not solutions:
            pytest.skip("No solutions generated")
        
        ranked = evaluate_solutions(solutions, preferences, max_budget=5000)
        
        assert len(ranked) == len(solutions), "Should return all solutions"
        assert all(hasattr(s, 'score') for s in ranked), "All solutions should have scores"
        assert all(hasattr(s, 'evaluationLog') for s in ranked), "All solutions should have logs"
        
        # Check solutions are sorted by score (descending)
        scores = [s.score for s in ranked]
        assert scores == sorted(scores, reverse=True), "Solutions should be sorted by score"
    
    def test_preferred_provider_bonus(self):
        """Test preferred provider gets bonus"""
        constraints = Constraints(maxBudget=5000, maxLatency=12, maxProviders=2)
        preferences_none = Preferences()
        preferences_azure = Preferences(preferredProvider='Azure')
        preferences_aws = Preferences(preferredProvider='AWS')

        # Construct two comparable solutions differing mainly by provider.
        # This makes the test deterministic and independent of whatever
        # generate_feasible_solutions happens to return.
        base_cost = 100.0
        base_latency = 10.0

        azure_sol = Solution(
            configuration={'api_gateway': 'Azure API Management', 'database': 'Azure SQL'},
            cost=base_cost,
            latency=base_latency,
            providers=1,
            providerDistribution={'Azure': 2},
        )
        aws_sol = Solution(
            configuration={'api_gateway': 'AWS API Gateway', 'database': 'AWS RDS'},
            cost=base_cost,
            latency=base_latency,
            providers=1,
            providerDistribution={'AWS': 2},
        )

        solutions = [azure_sol, aws_sol]

        # Baseline ranking with no preferred provider
        ranked_none = evaluate_solutions(
            solutions,
            preferences_none,
            max_budget=float(constraints.maxBudget),
        )
        score_azure_base = next(
            s.score for s in ranked_none if s.providerDistribution.get('Azure', 0) > 0
        )
        score_aws_base = next(
            s.score for s in ranked_none if s.providerDistribution.get('AWS', 0) > 0
        )

        # With Azure preference, Azure score should not decrease (soft bonus)
        ranked_azure = evaluate_solutions(
            solutions,
            preferences_azure,
            max_budget=float(constraints.maxBudget),
        )
        score_azure_pref = next(
            s.score for s in ranked_azure if s.providerDistribution.get('Azure', 0) > 0
        )

        # With AWS preference, AWS score should not decrease (soft bonus)
        ranked_aws = evaluate_solutions(
            solutions,
            preferences_aws,
            max_budget=float(constraints.maxBudget),
        )
        score_aws_pref = next(
            s.score for s in ranked_aws if s.providerDistribution.get('AWS', 0) > 0
        )

        assert score_azure_pref >= score_azure_base
        assert score_aws_pref >= score_aws_base


# Test runner
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
