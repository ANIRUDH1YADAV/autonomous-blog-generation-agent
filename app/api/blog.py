import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.graph.workflow import graph

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class BlogRequest(BaseModel):
    topic: str


class BlogResponse(BaseModel):
    title: str
    final_blog: str
    images: list[dict]


# ── Main generation endpoint ──────────────────────────────────────────────────

@router.post("/generate", response_model=BlogResponse)
async def generate_blog(request: BlogRequest):
    """
    Accepts a topic, runs it through the full LangGraph pipeline:
    router -> research/planner -> writers (parallel) -> image_generator -> reducer.

    Returns the assembled blog post with title and image paths.
    Each run is checkpointed to memory.db via SqliteSaver,
    and traced to LangSmith if LANGCHAIN_TRACING_V2=true.
    """
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    topic = request.topic.strip()
    logger.info(f"Blog generation requested for topic: '{topic}'")

    try:
        # thread_id ties this invocation to a checkpoint in memory.db.
        # Using the topic as thread_id means re-running the same topic
        # resumes from the last checkpoint rather than starting over.
        config = {
            "configurable": {
                "thread_id": topic[:60]
            }
        }

        result = await graph.ainvoke({"topic": topic}, config=config)

        logger.info(f"Blog generation complete: '{result['plan']['title']}'")

        return BlogResponse(
            title=result["plan"]["title"],
            final_blog=result["final_blog"],
            images=result.get("images", [])
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


# ── Plan-only endpoint (for debugging) ───────────────────────────────────────

@router.post("/plan")
async def plan_only(request: BlogRequest):
    """
    Runs the graph only up to the planner and returns the outline.
    Useful for verifying agent connections without waiting for full generation.
    """
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    try:
        config = {"configurable": {"thread_id": f"plan-{request.topic[:40]}"}}
        result = await graph.ainvoke(
            {"topic": request.topic.strip()},
            config=config
        )
        return {
            "title":    result["plan"]["title"],
            "sections": result["plan"]["sections"]
        }

    except Exception as e:
        logger.error(f"Plan-only run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))