import operator
import sqlite3
from typing import Annotated, TypedDict, List

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.sqlite import SqliteSaver

from app.agents.router import router_node
from app.agents.research import research_node
from app.agents.planner import planner_node
from app.agents.writer import writer_node
from app.agents.reducer import reducer_node
from app.agents.image_generator import image_generator_node


# ── Shared state ──────────────────────────────────────────────────────────────
# Every key here flows through the entire graph.
# total=False means no key is required upfront — nodes add them as they run.

class BlogState(TypedDict, total=False):
    topic: str
    mode: str                                             # "research" or "direct"
    evidence: list                                        # filled by research_node
    plan: dict                                            # filled by planner_node
    section: str                                          # per-branch context for writer
    written_sections: Annotated[List[str], operator.add] # merged from parallel writers
    images: list                                          # filled by image_generator_node
    final_blog: str                                       # assembled by reducer_node


# ── Routing: should we research first or plan directly? ───────────────────────

def route_after_router(state: BlogState) -> str:
    if state.get("mode") == "research":
        return "research"
    return "planner"


# ── Fan-out: send each section to a separate writer branch ────────────────────
# All branches run in parallel. Their outputs merge into written_sections
# automatically via operator.add.

def expand_sections(state: BlogState):
    sections = state["plan"]["sections"]
    return [
        Send("writer", {"topic": state["topic"], "section": section})
        for section in sections
    ]


# ── Guard: only move to image generation if writing produced content ──────────

def route_after_writer(state: BlogState) -> str:
    if state.get("written_sections"):
        return "image_generator"
    return END


# ── Graph construction ────────────────────────────────────────────────────────

builder = StateGraph(BlogState)

builder.add_node("router",          router_node)
builder.add_node("research",        research_node)
builder.add_node("planner",         planner_node)
builder.add_node("writer",          writer_node)
builder.add_node("image_generator", image_generator_node)
builder.add_node("reducer",         reducer_node)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    route_after_router,
    {
        "research": "research",
        "planner":  "planner"
    }
)

builder.add_edge("research", "planner")

builder.add_conditional_edges(
    "planner",
    expand_sections,
    ["writer"]
)

builder.add_conditional_edges(
    "writer",
    route_after_writer,
    {
        "image_generator": "image_generator",
        END: END
    }
)

builder.add_edge("image_generator", "reducer")
builder.add_edge("reducer",         END)


# ── Persistence ───────────────────────────────────────────────────────────────
# SqliteSaver needs a raw sqlite3 connection — not from_conn_string()
# which returns a context manager and cannot be passed to compile() directly.
# memory.db stores every graph step on disk so sessions survive app restarts.

conn = sqlite3.connect("memory.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

graph = builder.compile(checkpointer=checkpointer)