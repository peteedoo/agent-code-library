"""Smoke tests for the HTTP API, driven against a live in-process server."""
import json
import sys
import unittest
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from http.server import ThreadingHTTPServer  # noqa: E402

from repos_explorer.server import Handler  # noqa: E402


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def _get(self, path):
        with urlopen(f"http://127.0.0.1:{self.port}{path}") as resp:
            return resp.status, json.loads(resp.read().decode())

    def test_healthz(self):
        status, body = self._get("/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["repos"], 100)

    def test_list_all_repos(self):
        _, body = self._get("/api/repos")
        self.assertEqual(body["count"], 100)

    def test_search_query(self):
        _, body = self._get("/api/repos?q=agent")
        self.assertTrue(body["count"] > 0)
        self.assertTrue(body["count"] < 100)

    def test_filter_category(self):
        _, body = self._get("/api/repos?category=Vector%20Databases")
        self.assertEqual(body["count"], 6)

    def test_single_repo(self):
        _, body = self._get("/api/repos/ollama-ollama")
        self.assertEqual(body["name"], "ollama")

    def test_missing_repo_404(self):
        with self.assertRaises(Exception):
            self._get("/api/repos/nope")

    def test_categories_endpoint(self):
        _, body = self._get("/api/categories")
        self.assertIn("Vector Databases", body["categories"])
        self.assertIn("Python", body["languages"])

    def test_stats_endpoint(self):
        _, body = self._get("/api/stats")
        self.assertEqual(body["total"], 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
