"""CLI entrypoint for the AI/ML Repo Explorer.

    python -m repos_explorer list
    python -m repos_explorer search "vector database"
    python -m repos_explorer search agent --category "Agent Frameworks"
    python -m repos_explorer categories
    python -m repos_explorer stats
    python -m repos_explorer serve --port 8100
"""
from __future__ import annotations

import argparse

from .catalog import Repo, load_catalog


def _print_repos(repos: list[Repo]) -> None:
    if not repos:
        print("no matches")
        return
    for r in repos:
        print(f"  {r.full_name:<45} [{r.language:<10}] {r.category}")
        print(f"      {r.description}")
    print(f"\n{len(repos)} repo(s)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="repos_explorer", description="Browse a catalog of AI/ML repos.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="free-text search over the catalog")
    p_search.add_argument("query", nargs="?", default="")
    p_search.add_argument("--category")
    p_search.add_argument("--language")

    sub.add_parser("list", help="list all repos")

    sub.add_parser("categories", help="list categories and languages")
    sub.add_parser("stats", help="show catalog statistics")

    p_serve = sub.add_parser("serve", help="run the web app + JSON API")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8100)

    args = parser.parse_args(argv)
    catalog = load_catalog()

    if args.cmd == "search":
        _print_repos(catalog.search(args.query, category=args.category, language=args.language))
    elif args.cmd == "list":
        _print_repos(sorted(catalog.repos, key=lambda r: r.full_name.lower()))
    elif args.cmd == "categories":
        print("Categories:")
        for c in catalog.categories:
            print(f"  {c}")
        print("\nLanguages:")
        print("  " + ", ".join(catalog.languages))
    elif args.cmd == "stats":
        s = catalog.stats()
        print(f"Total repos : {s['total']}")
        print(f"Categories  : {s['categories']}")
        print(f"Languages   : {s['languages']}")
        print("\nBy language:")
        for lang, n in s["by_language"].items():
            print(f"  {lang:<12} {n}")
        print("\nBy category:")
        for cat, n in s["by_category"].items():
            print(f"  {cat:<28} {n}")
    elif args.cmd == "serve":
        from .server import serve

        serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
