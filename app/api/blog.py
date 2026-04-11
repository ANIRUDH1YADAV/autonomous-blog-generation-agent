import asyncio
import json
import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.graph.workflow import ainvoke_graph, astream_graph
from app.agents.router import router_node
from app.agents.research import research_node
from app.agents.llm_knowledge import llm_knowledge_node
from app.agents.brainstorming import brainstorming_node

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class BlogRequest(BaseModel):
    topic: str
    target_language: str = Field(default="english")


class BlogResponse(BaseModel):
    title: str
    final_blog: str
    images: list[dict]
    meta_description: str | None = None
    keywords: list[str] = Field(default_factory=list)


NODE_PROGRESS_MESSAGES = {
    "router": "Router agent deciding web search and translation path...",
    "web_search": "Web search agent collecting fresh evidence...",
    "llm_knowledge": "LLM knowledge agent building background evidence...",
    "brainstorming": "Brainstorming agent creating title and headings...",
    "content_generation": "Content generation agent drafting the blog...",
    "image_generator": "Image generator creating supporting visuals...",
    "translator": "Translator agent converting content to target language...",
    "seo_reducer": "SEO reducer refining quality, meta description, and keywords...",
    "save_memory": "Saving run state to memory database...",
}


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _clean_markdown_output(text: str) -> str:
    """
    Remove standalone underline-style separator lines like '=====' that
    sometimes appear in model output and look noisy in the rendered blog.
    """
    if not text:
        return text

    cleaned = re.sub(r"(?m)^[ \t]*={3,}[ \t]*(?:\n|$)", "", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ── Main generation endpoint ──────────────────────────────────────────────────

async def _run_generation(request: BlogRequest) -> BlogResponse:
    """
    Accepts a topic, runs it through the LangGraph pipeline:
    router -> web_search/llm_knowledge -> brainstorming -> content_generation ->
    image_generator -> optional translator -> seo_reducer -> save_memory.

    Returns the assembled blog post with title and image paths.
    Each run is checkpointed to memory.db via AsyncSqliteSaver,
    and traced to LangSmith if LANGCHAIN_TRACING_V2=true.
    """
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    topic = request.topic.strip()
    target_language = (request.target_language or "english").strip()
    logger.info(
        "Blog generation requested for topic='%s', target_language='%s'",
        topic,
        target_language,
    )

    try:
        # thread_id ties this invocation to a checkpoint in memory.db.
        # Using the topic as thread_id means re-running the same topic
        # resumes from the last checkpoint rather than starting over.
        config = {
            "configurable": {
                "thread_id": topic[:60]
            },
            "run_name": "generate_blog",
            "tags": ["blog-generation", "fastapi", "langgraph"],
            "metadata": {
                "topic": topic,
                "target_language": target_language,
            },
        }

        result = await ainvoke_graph(
            {
                "topic": topic,
                "target_language": target_language,
            },
            config=config,
        )

        title = result.get("title") or result["plan"]["title"]
        final_blog = _clean_markdown_output(result["final_blog"])
        logger.info("Blog generation complete: '%s'", title)

        return BlogResponse(
            title=title,
            final_blog=final_blog,
            images=result.get("images", []),
            meta_description=result.get("meta_description"),
            keywords=result.get("keywords", []),
        )

    except KeyError as e:
        # A node didn't return the expected state key
        logger.error(f"Missing state key after graph run: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error — missing field: {e}"
        )

    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate_blog", response_model=BlogResponse)
async def generate_blog(request: BlogRequest):
    return await _run_generation(request)


@router.post("/generate_blog/stream")
async def generate_blog_stream(request: BlogRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    topic = request.topic.strip()
    target_language = (request.target_language or "english").strip()

    config = {
        "configurable": {
            "thread_id": topic[:60],
        },
        "run_name": "generate_blog_stream",
        "tags": ["blog-generation", "fastapi", "langgraph", "streaming"],
        "metadata": {
            "topic": topic,
            "target_language": target_language,
        },
    }

    async def event_stream():
        latest_state: dict[str, Any] = {}
        latest_images: list[dict] = []

        try:
            yield _sse(
                "progress",
                {
                    "stage": "start",
                    "message": "Starting workflow...",
                },
            )

            async for update in astream_graph(
                {
                    "topic": topic,
                    "target_language": target_language,
                },
                config=config,
                stream_mode="updates",
            ):
                if not isinstance(update, dict):
                    continue

                for node_name, node_output in update.items():
                    if not isinstance(node_output, dict):
                        continue

                    latest_state.update(node_output)

                    yield _sse(
                        "progress",
                        {
                            "stage": node_name,
                            "message": NODE_PROGRESS_MESSAGES.get(
                                node_name,
                                f"{node_name} completed.",
                            ),
                        },
                    )

                    if "title" in node_output and node_output["title"]:
                        yield _sse("title", {"title": node_output["title"]})

                    if "images" in node_output and isinstance(node_output["images"], list):
                        latest_images = node_output["images"]
                        yield _sse("images", {"images": latest_images})

            title = (
                latest_state.get("title")
                or latest_state.get("plan", {}).get("title")
                or "Generated Blog"
            )
            final_blog = latest_state.get("final_blog", "")
            images = latest_state.get("images", latest_images)
            meta_description = latest_state.get("meta_description")
            keywords = latest_state.get("keywords", [])

            final_blog = _clean_markdown_output(final_blog)

            if not final_blog:
                raise ValueError("Pipeline completed without final blog content.")

            yield _sse(
                "progress",
                {
                    "stage": "streaming_output",
                    "message": "Streaming final blog content word by word...",
                },
            )

            for word_chunk in re.findall(r"\S+\s*", final_blog):
                yield _sse("word", {"text": word_chunk})
                await asyncio.sleep(0.02)

            yield _sse(
                "done",
                {
                    "title": title,
                    "images": images,
                    "meta_description": meta_description,
                    "keywords": keywords,
                },
            )

        except Exception as exc:
            logger.exception("Streaming generation failed: %s", exc)
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate", response_model=BlogResponse)
async def generate_blog_legacy(request: BlogRequest):
    return await _run_generation(request)


# ── Plan-only endpoint (for debugging) ───────────────────────────────────────

@router.post("/plan")
async def plan_only(request: BlogRequest):
    """
    Runs only the early workflow path and returns brainstormed title/headings.
    Useful for quick validation without content/image generation latency.
    """
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    try:
        state: dict[str, Any] = {
            "topic": request.topic.strip(),
            "target_language": (request.target_language or "english").strip(),
        }

        state.update(router_node(state))

        if state.get("needs_web_search"):
            state.update(research_node(state))
        else:
            state.update(llm_knowledge_node(state))

        state.update(brainstorming_node(state))

        plan = state.get("plan", {})
        return {
            "title": state.get("title") or plan.get("title"),
            "headings": state.get("headings", []),
            "sections": plan.get("sections", []),
        }

    except Exception as e:
        logger.error(f"Plan-only run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))