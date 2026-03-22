"""
CMOv4 Test Suite
- Unit tests for models, validation, optimizer, search, and benchmarking
"""
import unittest
from .models import Component, Architecture, Pricing
from .validation import validate_architecture
from .optimizer import optimize_architecture
from .search import heuristic_search, exhaustive_search

class TestCMOv4(unittest.TestCase):
    def test_component_creation(self):
        c = Component(name='AppServer', type='compute', instance_count=2, tech_stack={'language': 'Python'}, dependencies=['Database'])
        self.assertEqual(c.name, 'AppServer')
        self.assertEqual(c.type, 'compute')
        self.assertEqual(c.instance_count, 2)
        self.assertEqual(c.tech_stack['language'], 'Python')
        self.assertIn('Database', c.dependencies)

    def test_architecture_validation(self):
        components = [
            Component(name='Frontend', type='web'),
            Component(name='AppServer', type='compute'),
            Component(name='Database', type='database')
        ]
        pricing_data = {'AWS': {'web': {'Frontend': 0.01}, 'compute': {'AppServer': 0.02}, 'database': {'Database': 0.03}}}
        from .models import Pricing
        arch = Architecture(components, pricing=Pricing(pricing_data))
        errors = validate_architecture(arch)
        self.assertEqual(errors, [])

    def test_optimizer_output(self):
        components = [
            Component(name='Frontend', type='web'),
            Component(name='AppServer', type='compute'),
            Component(name='Database', type='database')
        ]
        arch = Architecture(components)
        constraints = {'maxBudget': 1000}
        result = optimize_architecture(arch, constraints)
        self.assertIn('solutions', result)
        self.assertIn('pareto_frontier', result)
        self.assertIn('explanations', result)

    def test_search_algorithms(self):
        components = [
            Component(name='Frontend', type='web'),
            Component(name='AppServer', type='compute'),
            Component(name='Database', type='database')
        ]
        arch = Architecture(components)
        constraints = {'maxBudget': 1000}
        heur = heuristic_search(arch, constraints)
        exhau = exhaustive_search(arch, constraints)
        self.assertIsInstance(heur, list)
        self.assertIsInstance(exhau, list)

if __name__ == '__main__':
    unittest.main()
