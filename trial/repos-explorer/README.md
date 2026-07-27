# AI/ML Repo Explorer — trial app

A small, self-contained trial app that catalogs **100 AI/ML repositories**
(agent frameworks, RAG, vector DBs, serving, observability, orchestration, …)
and lets you browse, search, and filter them from a web UI, a JSON API, or the
CLI. The 100-repo list doubles as the test fixture.

No third-party dependencies — pure Python standard library + a static frontend.

## Layout

```
trial/repos-explorer/
  data/
    build_repos.py     # source-of-truth list of the 100 repos (regenerates repos.json)
    repos.json         # generated dataset the app serves + tests validate
  repos_explorer/
    catalog.py         # load / search / filter / stats (no deps)
    server.py          # stdlib http.server: JSON API + static web UI
    __main__.py        # CLI: search, list, categories, stats, serve
  web/                 # index.html + style.css + app.js (dark, monospace)
  tests/
    test_catalog.py    # dataset + catalog-logic tests (the 100 repos as fixtures)
    test_server.py     # in-process HTTP API smoke tests
```

## Run it

```bash
cd trial/repos-explorer

# CLI
python -m repos_explorer list
python -m repos_explorer search "vector database"
python -m repos_explorer search agent --category "Agent Frameworks"
python -m repos_explorer search --language Rust
python -m repos_explorer categories
python -m repos_explorer stats

# Web app + JSON API
python -m repos_explorer serve --port 8100
# then open http://127.0.0.1:8100
```

## JSON API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/repos?q=&category=&language=` | Filtered repo list |
| GET | `/api/repos/{id}` | Single repo (id = slug of `owner/name`) |
| GET | `/api/categories` | Category + language lists |
| GET | `/api/stats` | Aggregate counts |
| GET | `/healthz` | Health check |
| GET | `/` | Web UI |

```bash
curl 'http://127.0.0.1:8100/api/repos?q=rerank'
curl 'http://127.0.0.1:8100/api/repos?category=Vector%20Databases'
curl  http://127.0.0.1:8100/api/stats
```

## Tests

The 100 repos are the fixtures — tests assert the dataset is well-formed
(exactly 100, unique ids, valid GitHub URLs, complete fields) and that search,
filtering, grouping, and the HTTP API behave.

```bash
cd trial/repos-explorer
python -m unittest discover -s tests -v
# or, if pytest is available:
pytest
```

## Dataset

`data/repos.json` is generated from `data/build_repos.py`. Edit the `SOURCE`
dict there (grouped by category) and re-run to regenerate:

```bash
python data/build_repos.py
```

Each repo record:

```json
{
  "id": "qdrant-qdrant",
  "name": "qdrant",
  "owner": "qdrant",
  "full_name": "qdrant/qdrant",
  "url": "https://github.com/qdrant/qdrant",
  "category": "Vector Databases",
  "language": "Rust",
  "description": "High-performance vector similarity search engine."
}
```

100 repos across 20 categories: Agent Frameworks, Structured Output, Protocols
& Interop, Tools & Integrations, Browser & Web Automation, Code Agents & Dev
Tools, Vector Databases, RAG & Search, Embeddings & Rerankers, Scraping &
Ingestion, Sandboxes & Execution, Memory, Observability & Tracing, Evaluation &
Testing, Guardrails & Safety, Workflow & Orchestration, Task Queues & Jobs,
Messaging & Infra, Model Serving & Inference, UI & Frontend.
