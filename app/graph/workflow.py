from collections.abc import AsyncIterator
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.agents.router import router_node
from app.agents.research import research_node
from app.agents.llm_knowledge import llm_knowledge_node
from app.agents.brainstorming import brainstorming_node
from app.agents.content_generator import content_generator_node
from app.agents.translator import translator_node
from app.agents.seo_reducer import seo_reducer_node
from app.agents.memory_persist import memory_persist_node
from app.agents.image_generator import image_generator_node




class BlogState(TypedDict, total=False):
    topic: str
    target_language: str
    needs_web_search: bool
    needs_translation: bool
    evidence: list
    title: str
    headings: list[str]
    plan: dict
    draft_blog: str
    images: list
    final_blog: str
    meta_description: str
    keywords: list[str]
    saved_to_memory: bool


# Routing: web search branch selection 

def route_after_router(state: BlogState) -> str:
    if state.get("needs_web_search"):
        return "web_search"
    return "llm_knowledge"


#  Routing: translation branch after image generation 

def route_after_image_generation(state: BlogState) -> str:
    if state.get("needs_translation"):
        return "translator"
    return "seo_reducer"


#  Graph construction 

builder = StateGraph(BlogState)

builder.add_node("router",          router_node)
builder.add_node("web_search",      research_node)
builder.add_node("llm_knowledge",   llm_knowledge_node)
builder.add_node("brainstorming",   brainstorming_node)
builder.add_node("content_generation", content_generator_node)
builder.add_node("image_generator", image_generator_node)
builder.add_node("translator",      translator_node)
builder.add_node("seo_reducer",     seo_reducer_node)
builder.add_node("save_memory",     memory_persist_node)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    route_after_router,
    {
        "web_search": "web_search",
        "llm_knowledge": "llm_knowledge",
    }
)

builder.add_edge("web_search", "brainstorming")
builder.add_edge("llm_knowledge", "brainstorming")
builder.add_edge("brainstorming", "content_generation")
builder.add_edge("content_generation", "image_generator")

builder.add_conditional_edges(
    "image_generator",
    route_after_image_generation,
    {
        "translator": "translator",
        "seo_reducer": "seo_reducer",
    }
)

builder.add_edge("translator", "seo_reducer")
builder.add_edge("seo_reducer", "save_memory")
builder.add_edge("save_memory", END)


# Persistence 
# AsyncSqliteSaver supports async graph execution (ainvoke/astream) and stores
# checkpoints in memory.db so sessions survive app restarts.

graph = builder.compile()


async def ainvoke_graph(initial_state: BlogState, config: dict | None = None):
    async with AsyncSqliteSaver.from_conn_string("memory.db") as checkpointer:
        graph_with_checkpointer = builder.compile(checkpointer=checkpointer)
        return await graph_with_checkpointer.ainvoke(initial_state, config=config)


async def astream_graph(
    initial_state: BlogState,
    config: dict | None = None,
    stream_mode: str = "updates",
) -> AsyncIterator[dict]:
    async with AsyncSqliteSaver.from_conn_string("memory.db") as checkpointer:
        graph_with_checkpointer = builder.compile(checkpointer=checkpointer)
        async for event in graph_with_checkpointer.astream(
            initial_state,
            config=config,
            stream_mode=stream_mode,
        ):
            yield event