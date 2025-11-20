import unittest
from backend.cmov4.benchmark import run_benchmark, SCENARIOS

class TestCMOv4Benchmark(unittest.TestCase):
    def test_preset_scenario_0(self):
        # Run benchmark for the first preset scenario (5 components)
        results = run_benchmark([SCENARIOS[0]])
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        result = results[0]
        self.assertIn('v4', result)
        self.assertIn('v3', result)
        # Check that v4 results contain solutions and metrics
        v4 = result['v4']
        self.assertIn('solutions', v4)
        self.assertIn('metrics', v4)
        self.assertIsInstance(v4['solutions'], list)
        self.assertIsInstance(v4['metrics'], dict)
        # There should be at least one feasible solution
        self.assertGreaterEqual(v4['metrics'].get('feasible_count', 0), 1)

if __name__ == "__main__":
    unittest.main()
