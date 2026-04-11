import logging

from app.schemas.llm_outputs import BrainstormingOutput
from app.services.llm_json import parse_json_to_model
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def brainstorming_node(state: dict) -> dict:
    """
    Produces the final blog title and section headings.
    """
    topic = state["topic"]
    evidence = state.get("evidence", [])

    evidence_block = ""
    if evidence:
        snippets = "\n".join(
            f"- {item.get('title', 'Source')}: {item.get('content', '')[:180]}"
            for item in evidence[:5]
        )
        evidence_block = f"\n\nReference evidence:\n{snippets}"

    prompt = f"""You are a blog brainstorming agent.

Topic: {topic}{evidence_block}

Return ONLY valid JSON in this shape:
{{
  "title": "Compelling blog title",
  "headings": [
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Heading 4",
    "Heading 5"
  ]
}}

Rules:
- Exactly 5 headings.
- Headings must be specific and non-generic.
- No markdown or commentary.
"""

    llm = get_llm()

    try:
        raw = llm.invoke(prompt).content
        parsed = parse_json_to_model(raw, BrainstormingOutput)

        title = parsed.title.strip() or f"{topic.title()}: Practical Guide"
        headings = [str(h).strip() for h in parsed.headings if str(h).strip()]

        if len(headings) < 5:
            fallback = [
                "Core Concepts",
                "Current Landscape",
                "Implementation Strategy",
                "Common Pitfalls",
                "Actionable Next Steps",
            ]
            headings = (headings + fallback)[:5]
        else:
            headings = headings[:5]

        plan = {
            "title": title,
            "sections": [{"title": h, "subsections": []} for h in headings],
        }

        logger.info("Brainstorming complete: '%s' with %s headings", title, len(headings))
        return {"title": title, "headings": headings, "plan": plan}

    except Exception as exc:
        logger.error("Brainstorming failed: %s", exc)
        headings = [
            "Core Concepts",
            "Current Landscape",
            "Implementation Strategy",
            "Common Pitfalls",
            "Actionable Next Steps",
        ]
        title = f"{topic.title()}: Practical Guide"
        return {
            "title": title,
            "headings": headings,
            "plan": {
                "title": title,
                "sections": [{"title": h, "subsections": []} for h in headings],
            },
        }
