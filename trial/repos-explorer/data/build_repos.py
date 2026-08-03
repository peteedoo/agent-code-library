#!/usr/bin/env python3
"""Source-of-truth builder for the AI/ML Repo Explorer trial dataset.

Defines the 100 AI/ML repos as structured records grouped by category and
emits ``repos.json`` next to this file. Re-run after editing ``SOURCE`` to
regenerate the dataset the app serves and the tests validate.

    python data/build_repos.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# (owner/repo, primary language, one-line description)
# Grouped by category — the category is the dict key.
SOURCE: dict[str, list[tuple[str, str, str]]] = {
    "Agent Frameworks": [
        ("langchain-ai/langgraph", "Python", "Stateful, graph-based orchestration for multi-actor LLM apps."),
        ("pydantic-ai/pydantic-ai", "Python", "Type-safe agent framework built on Pydantic."),
        ("openai/openai-agents-python", "Python", "OpenAI's lightweight multi-agent framework."),
        ("mastra-ai/mastra", "TypeScript", "TypeScript agent framework with workflows and RAG."),
        ("crewAIInc/crewAI", "Python", "Orchestrate role-playing autonomous agent crews."),
        ("microsoft/agent-framework", "Python", "Microsoft's framework for building AI agents."),
        ("langchain-ai/langchain", "Python", "The original framework for building LLM applications."),
        ("run-llama/llama_index", "Python", "Data framework for LLM apps and RAG."),
        ("vercel/ai", "TypeScript", "Vercel AI SDK for building AI-powered UIs."),
        ("deepset-ai/haystack", "Python", "End-to-end framework for LLM/RAG pipelines."),
        ("huggingface/smolagents", "Python", "Minimal library for code-writing agents."),
        ("stanfordnlp/dspy", "Python", "Programming — not prompting — foundation models."),
        ("PrefectHQ/ControlFlow", "Python", "Agentic workflow framework on top of Prefect."),
        ("significant-gravitas/autogpt", "Python", "Autonomous GPT-4 agent platform."),
        ("geekan/metagpt", "Python", "Multi-agent framework that simulates a software company."),
        ("julep-ai/julep", "Python", "Stateful serverless platform for AI agents."),
        ("letta-ai/letta", "Python", "Agents with long-term memory (formerly MemGPT)."),
        ("camel-ai/camel", "Python", "Framework for studying multi-agent communication."),
        ("phidata-ai/phi", "Python", "Build agents with memory, knowledge, and tools."),
        ("microsoft/magentic-one", "Python", "Generalist multi-agent system by Microsoft."),
    ],
    "Structured Output": [
        ("jxnl/instructor", "Python", "Structured LLM outputs via Pydantic."),
        ("dottxt-ai/outlines", "Python", "Structured text generation with constrained decoding."),
        ("microsoft/TypeChat", "TypeScript", "Build natural language interfaces using types."),
        ("guardrails-ai/guardrails-ai", "Python", "Add structure, type, and quality guarantees to LLM output."),
    ],
    "Protocols & Interop": [
        ("modelcontextprotocol/python-sdk", "Python", "Official Python SDK for the Model Context Protocol."),
        ("google-a2a/A2A", "Python", "Agent2Agent protocol for cross-agent communication."),
        ("microsoft/promptflow", "Python", "Build, evaluate, and deploy LLM flows."),
    ],
    "Tools & Integrations": [
        ("composio/composio", "Python", "Tool/integration layer connecting agents to 250+ apps."),
        ("arcadeai/arcade", "Python", "Auth-aware tool-calling platform for agents."),
    ],
    "Browser & Web Automation": [
        ("browser-use/browser-use", "Python", "Let LLMs control a real browser."),
    ],
    "Code Agents & Dev Tools": [
        ("cline/cline", "TypeScript", "Autonomous coding agent in your IDE."),
        ("continue-dev/continue", "TypeScript", "Open-source AI code assistant."),
        ("aider/aider", "Python", "AI pair programming in your terminal."),
        ("All-Hands-AI/OpenHands", "Python", "Autonomous AI software engineer platform."),
        ("princeton-nlp/SWE-agent", "Python", "Agents that fix GitHub issues autonomously."),
        ("sweepai/sweep", "Python", "AI junior developer that resolves issues into PRs."),
        ("openinterpreter/interpreter", "Python", "Natural-language code execution locally."),
    ],
    "Vector Databases": [
        ("chroma-core/chroma", "Python", "Open-source embedding database."),
        ("qdrant/qdrant", "Rust", "High-performance vector similarity search engine."),
        ("weaviate/weaviate", "Go", "AI-native vector database."),
        ("pgvector/pgvector", "C", "Open-source vector similarity search for Postgres."),
        ("milvus-io/milvus", "Go", "Cloud-native vector database for scale."),
        ("lancedb/lancedb", "Rust", "Serverless vector database for AI apps."),
    ],
    "RAG & Search": [
        ("danswer-ai/danswer", "Python", "Enterprise question-answering over your docs."),
        ("infiniflow/ragflow", "Python", "RAG engine with deep document understanding."),
    ],
    "Embeddings & Rerankers": [
        ("UKPLab/sentence-transformers", "Python", "State-of-the-art text and image embeddings."),
        ("huggingface/text-embeddings-inference", "Rust", "Blazing-fast embedding model inference."),
        ("answerdotai/rerankers", "Python", "Unified API for reranking models."),
        ("FlagOpen/FlagEmbedding", "Python", "BGE family of embedding and rerank models."),
    ],
    "Scraping & Ingestion": [
        ("mendableai/firecrawl", "TypeScript", "Turn websites into LLM-ready markdown."),
        ("scrapegraphai/scrapegraph-ai", "Python", "LLM-powered web scraping pipelines."),
        ("unclecode/crawl4ai", "Python", "Open-source LLM-friendly web crawler."),
        ("Unstructured-IO/unstructured", "Python", "Preprocess unstructured docs for LLMs."),
    ],
    "Sandboxes & Execution": [
        ("e2b-dev/e2b", "TypeScript", "Secure cloud sandboxes for AI agent code execution."),
    ],
    "Memory": [
        ("mem0ai/mem0", "Python", "Long-term memory layer for AI agents."),
    ],
    "Observability & Tracing": [
        ("langfuse/langfuse", "TypeScript", "Open-source LLM engineering and observability platform."),
        ("arize-ai/phoenix", "Python", "AI observability and evaluation notebooks."),
        ("braintrustdata/braintrust", "TypeScript", "Eval and observability stack for AI products."),
        ("traceloop/openllmetry", "Python", "OpenTelemetry-based LLM observability."),
        ("open-telemetry/opentelemetry", "Various", "Vendor-neutral observability framework."),
        ("pydantic/logfire", "Python", "Observability built on OpenTelemetry by Pydantic."),
        ("langchain-ai/langsmith-sdk", "Python", "SDK for the LangSmith tracing/eval platform."),
        ("wandb/wandb", "Python", "Experiment tracking and model management."),
        ("mlflow/mlflow", "Python", "Open-source ML lifecycle platform."),
    ],
    "Evaluation & Testing": [
        ("promptfoo/promptfoo", "TypeScript", "Test and evaluate LLM prompts and outputs."),
        ("confident-ai/deepeval", "Python", "The LLM evaluation framework (unit tests for LLMs)."),
        ("explodinggradients/ragas", "Python", "Evaluation toolkit for RAG pipelines."),
        ("UKGovernmentBEIS/inspect-ai", "Python", "Framework for large language model evaluations."),
    ],
    "Guardrails & Safety": [
        ("laiyer-ai/llm-guard", "Python", "Security toolkit for LLM interactions."),
        ("meta-llama/PurpleLlama", "Python", "Meta's tools for LLM safety and security."),
        ("nvidia/nemo-guardrails", "Python", "Add programmable guardrails to LLM apps."),
    ],
    "Workflow & Orchestration": [
        ("inngest/inngest", "TypeScript", "Durable functions and event-driven workflows."),
        ("temporalio/temporal", "Go", "Durable execution platform for reliable workflows."),
        ("hatchet-dev/hatchet", "Go", "Distributed, fault-tolerant task queue."),
        ("windmill-labs/windmill", "Rust", "Developer platform for scripts, workflows, and UIs."),
        ("triggerdotdev/trigger.dev", "TypeScript", "Open-source background jobs and workflows."),
        ("PrefectHQ/prefect", "Python", "Workflow orchestration for data pipelines."),
        ("dagster-io/dagster", "Python", "Data orchestrator for ML and analytics."),
        ("ploomber/ploomber", "Python", "Build data pipelines fast."),
        ("zenml-io/zenml", "Python", "MLOps framework for reproducible pipelines."),
    ],
    "Task Queues & Jobs": [
        ("taskforcesh/bullmq", "TypeScript", "Robust Redis-based queue for Node.js."),
        ("celery/celery", "Python", "Distributed task queue for Python."),
        ("samuelcolvin/arq", "Python", "Fast asyncio Redis job queue."),
    ],
    "Messaging & Infra": [
        ("nats-io/nats-server", "Go", "High-performance cloud-native messaging system."),
        ("redis/redis", "C", "In-memory data store, cache, and message broker."),
        ("apache/kafka", "Java", "Distributed event streaming platform."),
    ],
    "Model Serving & Inference": [
        ("modal-labs/modal", "Python", "Serverless cloud for running AI workloads."),
        ("bentoml/BentoML", "Python", "Build and ship AI model serving APIs."),
        ("BerriAI/litellm", "Python", "Unified API for 100+ LLM providers."),
        ("ollama/ollama", "Go", "Run large language models locally."),
        ("vllm-project/vllm", "Python", "High-throughput, memory-efficient LLM inference."),
        ("open-webui/open-webui", "Python", "Self-hosted web UI for local LLMs."),
        ("sgl-project/sglang", "Python", "Fast serving framework for LLMs and VLMs."),
        ("skypilot-org/skypilot", "Python", "Run AI workloads on any cloud."),
        ("NVIDIA/triton-inference-server", "C++", "NVIDIA's high-performance inference server."),
    ],
    "UI & Frontend": [
        ("Chainlit/chainlit", "Python", "Build conversational AI UIs in minutes."),
        ("langflow-ai/langflow", "Python", "Visual low-code builder for LLM apps."),
        ("FlowiseAI/Flowise", "TypeScript", "Drag-and-drop UI to build LLM flows."),
        ("streamlit/streamlit", "Python", "Turn data scripts into shareable web apps."),
        ("gradio-app/gradio", "Python", "Build ML web demos with a few lines of Python."),
    ],
}


def slugify(owner_repo: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", owner_repo.lower()).strip("-")


def build() -> list[dict]:
    repos: list[dict] = []
    for category, entries in SOURCE.items():
        for owner_repo, language, description in entries:
            owner, repo = owner_repo.split("/", 1)
            repos.append(
                {
                    "id": slugify(owner_repo),
                    "name": repo,
                    "owner": owner,
                    "full_name": owner_repo,
                    "url": f"https://github.com/{owner_repo}",
                    "category": category,
                    "language": language,
                    "description": description,
                }
            )
    return repos


def main() -> None:
    repos = build()
    out = Path(__file__).with_name("repos.json")
    payload = {
        "name": "AI/ML Repo Explorer",
        "count": len(repos),
        "categories": sorted({r["category"] for r in repos}),
        "repos": repos,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(repos)} repos across {len(payload['categories'])} categories -> {out}")


if __name__ == "__main__":
    main()
