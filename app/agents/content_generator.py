import logging

from app.schemas.llm_outputs import ContentDraftOutput
from app.services.llm_json import parse_json_to_model
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def content_generator_node(state: dict) -> dict:
    """
    Generates the full blog article in one pass from title and headings.
    """
    topic = state["topic"]
    title = state.get("title", topic.title())
    headings = state.get("headings", [])
    evidence = state.get("evidence", [])

    heading_block = "\n".join(f"- {heading}" for heading in headings)
    evidence_block = "\n".join(
        f"- {item.get('title', '')}: {item.get('content', '')[:200]}"
        for item in evidence[:5]
    )

    prompt = f"""You are a content generation agent.

Write a full technical blog in markdown.

Blog title: {title}
Topic: {topic}

Required section headings:
{heading_block}

Evidence:
{evidence_block}

Rules:
- Start with a concise intro paragraph.
- Use exactly the provided headings as H2 sections.
- Add practical details, examples, and clear explanations.
- Keep the tone professional and direct.
- Produce 900-1400 words.

Return ONLY valid JSON in this shape:
{{
    "draft_blog": "full markdown blog"
}}

No commentary and no extra keys.
"""

    llm = get_llm()

    try:
        raw = llm.invoke(prompt).content
        parsed = parse_json_to_model(raw, ContentDraftOutput)
        draft_blog = parsed.draft_blog.strip()
        if not draft_blog:
            raise ValueError("Empty content generated")
        logger.info("Content generation complete (%s chars)", len(draft_blog))
        return {"draft_blog": draft_blog}

    except Exception as exc:
        logger.error("Content generation failed: %s", exc)
        fallback_sections = "\n\n".join(
            f"## {heading}\n\nContent for this section could not be generated in this run."
            for heading in headings
        )
        fallback_blog = f"# {title}\n\n{fallback_sections}" if fallback_sections else f"# {title}\n\nContent could not be generated in this run."
        return {"draft_blog": fallback_blog}
