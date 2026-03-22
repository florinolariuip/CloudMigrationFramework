import os
import unittest

# Skip heavy experiment generation
os.environ['SKIP_EXPERIMENTS'] = '1'
os.environ['FLASK_ENV'] = 'testing'

from backend.app import app  # noqa: E402


class DocsEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_serve_existing_markdown(self):
        r = self.client.get('/api/docs/EXPLANATION.md')
        # In case file name differs, fall back to NORMALIZED_MCDA.md
        if r.status_code == 404:
            r = self.client.get('/api/docs/NORMALIZED_MCDA.md')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/markdown', r.content_type)

    def test_reject_non_markdown(self):
        r = self.client.get('/api/docs/app.py')
        # Some servers may respond 400 for invalid extension; accept 400 or 404 as rejection
        self.assertIn(r.status_code, (400, 404))

    def test_missing_markdown(self):
        r = self.client.get('/api/docs/DOES_NOT_EXIST.md')
        self.assertEqual(r.status_code, 404)


if __name__ == '__main__':
    unittest.main()
