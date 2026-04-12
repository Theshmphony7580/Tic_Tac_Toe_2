"""
graph.py — Assembles LangGraph nodes into a compiled state machine.

The graph is compiled once at module import time and reused
by every Celery task — stateless and thread-safe.
"""

from langgraph import StateGraph, END

from app.nodes import (
    call_parser,
    call_normalizer,
    store_in_db,
    call_matcher,
    handle_error,
    route_after_parse,
    route_after_normalize,
    route_after_store,
)
from app.state import ResumeProcessingState


def build_graph():
    """Build and compile the resume processing state machine."""
    g = StateGraph(ResumeProcessingState)

    # ── Register nodes ──────────────────────────────────────────────────────
    g.add_node("parse",        call_parser)
    g.add_node("normalize",    call_normalizer)
    g.add_node("store",        store_in_db)
    g.add_node("match",        call_matcher)
    g.add_node("handle_error", handle_error)

    # ── Entry point ─────────────────────────────────────────────────────────
    g.set_entry_point("parse")

    # ── Conditional edges ────────────────────────────────────────────────────
    g.add_conditional_edges(
        "parse",
        route_after_parse,
        {
            "normalize":    "normalize",
            "parse":        "parse",        # Self-loop for retries
            "handle_error": "handle_error",
        },
    )

    g.add_conditional_edges(
        "normalize",
        route_after_normalize,
        {
            "store":     "store",
            "normalize": "normalize",       # Self-loop for retries
        },
    )

    g.add_conditional_edges(
        "store",
        route_after_store,
        {
            "match": "match",
            "END":  END,
        },
    )

    # ── Terminal edges ───────────────────────────────────────────────────────
    g.add_edge("match",        END)
    g.add_edge("handle_error", END)

    return g.compile()


# Compiled once at module import — reused by all Celery worker tasks.
# LangGraph compiled graphs are stateless and safe to share across calls.
resume_graph = build_graph()
