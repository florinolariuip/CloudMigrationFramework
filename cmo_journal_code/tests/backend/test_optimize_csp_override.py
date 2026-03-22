import os
import json
import unittest

# Ensure heavy experiment generation is skipped in tests
os.environ['SKIP_EXPERIMENTS'] = '1'
os.environ['FLASK_ENV'] = 'testing'

from backend.app import app, CSP_CONFIG  # noqa: E402


class OptimizeCSPOverrideTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Reset config to defaults to start clean
        self.client.post('/api/config/reset')

    def test_save_and_get_csp_config(self):
        # Save new CSP config
        payload = {
            "csp": {"search_strategy": "heuristic", "sample_size": 50}
        }
        r = self.client.post('/api/config/rules', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(r.status_code, 200)
        # Get config and verify
        r = self.client.get('/api/config/rules')
        self.assertEqual(r.status_code, 200)
        cfg = r.get_json()
        self.assertIn('csp', cfg)
        self.assertEqual(cfg['csp']['search_strategy'], 'heuristic')
        self.assertEqual(cfg['csp']['sample_size'], 50)

    def test_optimize_per_request_override_and_restore(self):
        # Ensure global stays 'heuristic'
        r = self.client.get('/api/config/rules')
        self.assertEqual(r.status_code, 200)
        global_strategy_before = r.get_json()['csp']['search_strategy']

        # Run optimize with per-request override to random_sample on tiny component subset
        optimize_payload = {
            "constraints": {
                "maxBudget": 999999,
                "maxLatency": 999,
                "maxProviders": 3,
                # limit combinatorics to keep test fast and safe
                "selected_components": ["api_gateway", "database"]
            },
            "preferences": {},
            "csp": {"search_strategy": "random_sample", "sample_size": 2}
        }
        r = self.client.post('/api/optimize', data=json.dumps(optimize_payload), content_type='application/json')
        self.assertEqual(r.status_code, 200, msg=r.data)
        data = r.get_json()
        self.assertIn('metrics', data)
        # Verify that reported strategy reflects per-run override
        self.assertEqual(data['metrics']['config_snapshot']['csp_strategy'], 'random_sample')

        # Verify global config was restored (unchanged)
        r = self.client.get('/api/config/rules')
        self.assertEqual(r.status_code, 200)
        global_strategy_after = r.get_json()['csp']['search_strategy']
        self.assertEqual(global_strategy_after, global_strategy_before)


if __name__ == '__main__':
    unittest.main()
