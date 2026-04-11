import logging

from app.schemas.llm_outputs import RouterDecision
from app.services.llm_json import parse_json_to_model
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)

ENGLISH_ALIASES = {
    "",
    "english",
    "en",
    "en-us",
    "en-gb",
}


def router_node(state: dict) -> dict:
    """
    Decides whether web search is needed and whether translation
    will be needed later in the workflow.
    """
    topic = state.get("topic", "")
    target_language = (state.get("target_language") or "english").strip().lower()

    prompt = f"""You are a workflow router for a blog writing system.

Decide whether this topic requires internet web search.

Topic: {topic}

Return ONLY valid JSON in this shape:
{{
  "decision": "search"
}}

Rules:
- decision must be either "search" or "direct"
- no extra keys
- no markdown or commentary"""

    try:
        llm = get_llm()
        raw = llm.invoke(prompt).content
        decision = parse_json_to_model(raw, RouterDecision).decision
    except Exception as exc:
        logger.error("Router LLM decision failed for '%s': %s", topic, exc)
        # Fall back to direct mode to keep the pipeline connected.
        decision = "direct"

    needs_web_search = decision == "search"
    needs_translation = target_language not in ENGLISH_ALIASES

    logger.info(
        "Router decision for '%s': needs_web_search=%s, needs_translation=%s",
        topic,
        needs_web_search,
        needs_translation,
    )

    return {
        "target_language": target_language or "english",
        "needs_web_search": needs_web_search,
        "needs_translation": needs_translation,
    }