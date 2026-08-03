"""Tests for the AI/ML Repo Explorer catalog, using the 100 repos as fixtures.

Run with either:
    python -m unittest discover -s tests
    pytest
from the trial/repos-explorer/ directory.
"""
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from repos_explorer.catalog import DATA_FILE, load_catalog  # noqa: E402

EXPECTED_COUNT = 100


class TestDataset(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        self.repos = self.payload["repos"]

    def test_has_exactly_100_repos(self):
        self.assertEqual(len(self.repos), EXPECTED_COUNT)
        self.assertEqual(self.payload["count"], EXPECTED_COUNT)

    def test_ids_are_unique(self):
        ids = [r["id"] for r in self.repos]
        self.assertEqual(len(ids), len(set(ids)))

    def test_full_names_are_unique(self):
        names = [r["full_name"] for r in self.repos]
        self.assertEqual(len(names), len(set(names)))

    def test_every_repo_has_required_fields(self):
        required = {"id", "name", "owner", "full_name", "url", "category", "language", "description"}
        for r in self.repos:
            with self.subTest(repo=r.get("full_name")):
                self.assertEqual(required, set(r), msg=f"field mismatch for {r.get('id')}")
                for key in required:
                    self.assertTrue(str(r[key]).strip(), msg=f"empty {key} in {r.get('id')}")

    def test_urls_are_valid_github_urls(self):
        for r in self.repos:
            with self.subTest(repo=r["full_name"]):
                parsed = urlparse(r["url"])
                self.assertEqual(parsed.scheme, "https")
                self.assertEqual(parsed.netloc, "github.com")
                self.assertEqual(parsed.path, f"/{r['full_name']}")

    def test_full_name_matches_owner_and_name(self):
        for r in self.repos:
            with self.subTest(repo=r["full_name"]):
                self.assertEqual(r["full_name"], f"{r['owner']}/{r['name']}")

    def test_categories_list_matches_repos(self):
        derived = sorted({r["category"] for r in self.repos})
        self.assertEqual(self.payload["categories"], derived)


class TestCatalogAPI(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()

    def test_load_count(self):
        self.assertEqual(len(self.catalog), EXPECTED_COUNT)

    def test_get_by_id(self):
        repo = self.catalog.get("qdrant-qdrant")
        self.assertIsNotNone(repo)
        self.assertEqual(repo.name, "qdrant")
        self.assertEqual(repo.category, "Vector Databases")

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.catalog.get("does-not-exist"))

    def test_search_free_text(self):
        results = self.catalog.search("vector")
        self.assertTrue(results)
        self.assertTrue(all(r.matches("vector") for r in results))
        # qdrant's description mentions "vector similarity search"
        self.assertIn("qdrant-qdrant", [r.id for r in results])

    def test_search_is_case_insensitive(self):
        self.assertEqual(
            [r.id for r in self.catalog.search("AGENT")],
            [r.id for r in self.catalog.search("agent")],
        )

    def test_empty_query_returns_all(self):
        self.assertEqual(len(self.catalog.search("")), EXPECTED_COUNT)

    def test_filter_by_category(self):
        results = self.catalog.search(category="Vector Databases")
        self.assertEqual(len(results), 6)
        self.assertTrue(all(r.category == "Vector Databases" for r in results))

    def test_filter_by_language(self):
        results = self.catalog.search(language="Rust")
        self.assertTrue(results)
        self.assertTrue(all(r.language == "Rust" for r in results))

    def test_combined_query_and_filter(self):
        results = self.catalog.search("db", category="Vector Databases")
        self.assertTrue(all(r.category == "Vector Databases" for r in results))

    def test_results_sorted_by_full_name(self):
        results = self.catalog.search("")
        names = [r.full_name.lower() for r in results]
        self.assertEqual(names, sorted(names))

    def test_by_category_covers_all_repos(self):
        grouped = self.catalog.by_category()
        total = sum(len(v) for v in grouped.values())
        self.assertEqual(total, EXPECTED_COUNT)
        self.assertEqual(set(grouped), set(self.catalog.categories))

    def test_stats(self):
        stats = self.catalog.stats()
        self.assertEqual(stats["total"], EXPECTED_COUNT)
        self.assertEqual(sum(stats["by_category"].values()), EXPECTED_COUNT)
        self.assertEqual(sum(stats["by_language"].values()), EXPECTED_COUNT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
