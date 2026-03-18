import logging
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def router_node(state: dict) -> dict:
    """
    Looks at the topic and decides whether we need to pull
    fresh information from the web before writing, or if the
    LLM's existing knowledge is sufficient to plan directly.
    """
    topic = state.get("topic", "")

    prompt = f"""You are a research coordinator for a blog writing system.

Decide whether this blog topic requires current internet research,
or if it can be written well from general knowledge alone.

Topic: {topic}

Reply with exactly one word:
- research   (if the topic needs fresh, up-to-date information)
- direct     (if general knowledge is sufficient)

No explanation. Just one word."""

    llm = get_llm()
    result = llm.invoke(prompt).content.strip().lower()

    # Normalize — LLMs sometimes return "research." or "direct."
    mode = "research" if "research" in result else "direct"

    logger.info(f"Router decision for '{topic}': {mode}")

    # Never mutate state directly — return only what changed
    return {"mode": mode}