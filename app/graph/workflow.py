import operator
from typing import Annotated, TypedDict, List

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver

from app.agents.router import router_node
from app.agents.research import research_node
from app.agents.planner import planner_node
from app.agents.writer import writer_node
from app.agents.reducer import reducer_node
from app.agents.image_generator import image_generator_node


# ─────────────────────────────────────────────
# Shared state that flows through the entire graph.
# Each key is either set once (topic, mode, plan)
# or accumulated across parallel branches (written_sections).
# ─────────────────────────────────────────────

class BlogState(TypedDict, total=False):
    topic: str
    mode: str                                        # "research" or "direct"
    evidence: list                                   # filled only in research mode
    plan: dict                                       # output from planner
    section: str                                     # per-writer-branch context
    written_sections: Annotated[List[str], operator.add]  # merged from all writers
    images: list                                     # generated after all writing is done
    final_blog: str                                  # assembled by reducer


# ─────────────────────────────────────────────
# Router decision: should we research first,
# or go straight to planning?
# ─────────────────────────────────────────────

def route_after_router(state: BlogState) -> str:
    if state.get("mode") == "research":
        return "research"
    return "planner"


# ─────────────────────────────────────────────
# Fan-out: once the planner creates sections,
# we send each section to a separate writer branch.
# All branches run in parallel and their outputs
# get merged via operator.add into written_sections.
# ─────────────────────────────────────────────

def expand_sections(state: BlogState):
    sections = state["plan"]["sections"]
    return [
        Send("writer", {
            "topic": state["topic"],
            "section": section
        })
        for section in sections
    ]


# ─────────────────────────────────────────────
# After all parallel writers finish, we check
# if written_sections are ready before moving on.
# This acts as a soft guard before image generation.
# ─────────────────────────────────────────────

def route_after_writer(state: BlogState) -> str:
    if state.get("written_sections"):
        return "image_generator"
    return END


# ─────────────────────────────────────────────
# Graph construction
# ─────────────────────────────────────────────

builder = StateGraph(BlogState)

builder.add_node("router",          router_node)
builder.add_node("research",        research_node)
builder.add_node("planner",         planner_node)
builder.add_node("writer",          writer_node)
builder.add_node("image_generator", image_generator_node)
builder.add_node("reducer",         reducer_node)

# Entry point
builder.add_edge(START, "router")

# Router decides: research first or straight to planning
builder.add_conditional_edges(
    "router",
    route_after_router,
    {
        "research": "research",
        "planner":  "planner"
    }
)

# Research always feeds into planner
builder.add_edge("research", "planner")

# Planner fans out to multiple parallel writer branches
builder.add_conditional_edges(
    "planner",
    expand_sections,
    ["writer"]
)

# After all writers finish, image generation runs ONCE
builder.add_conditional_edges(
    "writer",
    route_after_writer,
    {
        "image_generator": "image_generator",
        END: END
    }
)

# Image generator feeds into reducer which assembles the final blog
builder.add_edge("image_generator", "reducer")
builder.add_edge("reducer",         END)


# ─────────────────────────────────────────────
# Compile with in-memory checkpointing.
# This keeps state alive within a session
# (e.g. if the user pauses mid-generation).
# LangSmith tracing is configured via .env —
# set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY.
# ─────────────────────────────────────────────

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)