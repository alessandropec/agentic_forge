"""Example Python implementations used by the declarative tool forge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from langgraph.types import Command
except ImportError:  # pragma: no cover - keep the example runnable without langgraph
    @dataclass
    class Command:
        """Minimal fallback compatible with the example workflow."""

        update: dict[str, Any] = field(default_factory=dict)


class DemoDbConnector:
    """Small fake connector used to show resource injection."""

    def __init__(self, dataset: str) -> None:
        self.dataset = dataset

    def search(self, query: str, limit: int = 5) -> list[str]:
        return [f"{self.dataset}:{query}:{index}" for index in range(1, limit + 1)]


def build_demo_db_connector(dataset: str) -> DemoDbConnector:
    """Build a connector once at forge time."""
    return DemoDbConnector(dataset=dataset)


def search_documents(query: str, limit: int = 5, category: str | None = None) -> dict:
    """Return a deterministic payload that makes the wiring easy to verify."""
    return {
        "query": query,
        "category": category,
        "limit": limit,
        "results": [f"{query}-result-{index}" for index in range(1, limit + 1)],
    }


def summarize_text(text: str, style: str = "brief") -> dict:
    """Fake summarizer used for smoke tests and examples."""
    summary = text if style == "full" else text[:40]
    return {
        "style": style,
        "summary": summary,
        "original_length": len(text),
    }


def search_with_db(query: str, db: DemoDbConnector, limit: int = 5) -> dict:
    """Use an injected shared connector instead of recreating it on each call."""
    return {
        "query": query,
        "limit": limit,
        "source": db.dataset,
        "results": db.search(query=query, limit=limit),
    }


def remember_topic(topic: str, state: dict[str, Any]) -> Command:
    """Return an explicit command carrying both output and state patch."""
    visited_topics = list(state.get("visited_topics", []))
    visited_topics.append(topic)

    return Command(
        update={
            "last_topic": topic,
            "visited_topics": visited_topics,
        },
    )


def answer_with_memory(question: str, state: dict[str, Any]) -> dict:
    """Read an injected state snapshot to tailor the response."""
    topic = state.get("last_topic")
    if topic:
        answer = f"For '{question}' I am also considering the stored context: {topic}."
    else:
        answer = f"For '{question}' there is no stored topic in state yet."

    return {
        "question": question,
        "known_topic": topic,
        "answer": answer,
    }
