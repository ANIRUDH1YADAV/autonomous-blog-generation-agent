import operator
from typing import Annotated

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from app.agents.router import router_node
from app.agents.research import research_node
from app.agents.planner import planner_node
from app.agents.writer import writer_node
from app.agents.reducer import reducer_node


class BlogState(TypedDict, total=False):
    topic: str
    mode: str
    evidence: list
    plan: dict
    section: str
    written_sections: Annotated[List[str], operator.add]
    final_blog: str


def route_decision(state: BlogState):
    if state["mode"] == "research":
        return "research"
    return "planner"


def expand_sections(state: BlogState):

    sections = state["plan"]["sections"]

    return [
        Send(
            "writer",
            {
                "topic": state["topic"],
                "section": section
            }
        )
        for section in sections
    ]


builder = StateGraph(BlogState)

builder.add_node("router", router_node)
builder.add_node("research", research_node)
builder.add_node("planner", planner_node)
builder.add_node("writer", writer_node)
builder.add_node("reducer", reducer_node)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    route_decision,
    {
        "research": "research",
        "planner": "planner"
    }
)

builder.add_edge("research", "planner")

builder.add_conditional_edges(
    "planner",
    expand_sections,
    ["writer"]
)

builder.add_edge("writer", "reducer")

builder.add_edge("reducer", END)

graph = builder.compile()