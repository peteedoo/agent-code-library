"""Catalog loading, searching, and filtering — pure stdlib, no dependencies."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "repos.json"


@dataclass(frozen=True)
class Repo:
    id: str
    name: str
    owner: str
    full_name: str
    url: str
    category: str
    language: str
    description: str

    def matches(self, query: str) -> bool:
        """Case-insensitive substring match over the searchable fields."""
        q = query.lower().strip()
        if not q:
            return True
        haystack = " ".join(
            [self.name, self.owner, self.full_name, self.category, self.language, self.description]
        ).lower()
        return q in haystack

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "full_name": self.full_name,
            "url": self.url,
            "category": self.category,
            "language": self.language,
            "description": self.description,
        }


@dataclass
class Catalog:
    repos: list[Repo] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.repos)

    @property
    def categories(self) -> list[str]:
        return sorted({r.category for r in self.repos})

    @property
    def languages(self) -> list[str]:
        return sorted({r.language for r in self.repos})

    def get(self, repo_id: str) -> Repo | None:
        return next((r for r in self.repos if r.id == repo_id), None)

    def search(
        self,
        query: str = "",
        *,
        category: str | None = None,
        language: str | None = None,
    ) -> list[Repo]:
        """Filter by free-text query, exact category, and/or exact language."""
        results = self.repos
        if category:
            results = [r for r in results if r.category.lower() == category.lower()]
        if language:
            results = [r for r in results if r.language.lower() == language.lower()]
        if query:
            results = [r for r in results if r.matches(query)]
        return sorted(results, key=lambda r: r.full_name.lower())

    def by_category(self) -> dict[str, list[Repo]]:
        """Group repos by category, categories in sorted order."""
        grouped: dict[str, list[Repo]] = {c: [] for c in self.categories}
        for repo in sorted(self.repos, key=lambda r: r.full_name.lower()):
            grouped[repo.category].append(repo)
        return grouped

    def stats(self) -> dict:
        by_lang: dict[str, int] = {}
        by_cat: dict[str, int] = {}
        for r in self.repos:
            by_lang[r.language] = by_lang.get(r.language, 0) + 1
            by_cat[r.category] = by_cat.get(r.category, 0) + 1
        return {
            "total": len(self.repos),
            "categories": len(self.categories),
            "languages": len(self.languages),
            "by_language": dict(sorted(by_lang.items(), key=lambda kv: (-kv[1], kv[0]))),
            "by_category": dict(sorted(by_cat.items(), key=lambda kv: (-kv[1], kv[0]))),
        }


def load_catalog(path: str | Path | None = None) -> Catalog:
    """Load the repo catalog from repos.json (defaults to the bundled dataset)."""
    data_path = Path(path) if path else DATA_FILE
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    repos = [Repo(**entry) for entry in payload["repos"]]
    return Catalog(repos=repos)
