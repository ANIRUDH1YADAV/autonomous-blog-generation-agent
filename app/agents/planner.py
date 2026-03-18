import json
import re
import logging

from app.services.llm_service import get_llm
from app.schemas.blog_schema import BlogPlan

logger = logging.getLogger(__name__)


def planner_node(state: dict) -> dict:
    """
    Builds a structured blog outline from the topic.
    If research evidence exists, it shapes the sections
    around real findings rather than generic ideas.
    """
    topic = state["topic"]
    evidence = state.get("evidence", [])

    # Weave research findings into the prompt when available
    evidence_block = ""
    if evidence:
        summaries = "\n".join(
            f"- [{item['title']}]: {item['content'][:200]}"
            for item in evidence
        )
        evidence_block = f"\n\nBase your outline on these research findings:\n{summaries}"

    prompt = f"""You are a senior technical blog planner.

Create a structured, engaging outline for a blog post.

Topic: {topic}{evidence_block}

Return ONLY valid JSON — no markdown, no explanation, nothing else.

{{
  "title": "A specific, compelling blog title",
  "sections": [
    {{
      "title": "Section Title",
      "subsections": ["Subtopic 1", "Subtopic 2"]
    }}
  ]
}}

Requirements:
- Exactly 5 sections
- Exactly 2 subsections per section
- Titles must be specific, not generic placeholders
- Write for a technically literate audience"""

    llm = get_llm()
    logger.info(f"Planning blog for topic: '{topic}'")

    try:
        raw = llm.invoke(prompt).content
        match = re.search(r"\{[\s\S]*\}", raw)

        if not match:
            logger.error(f"No JSON found in planner response:\n{raw}")
            raise ValueError("Planner did not return valid JSON")

        plan_dict = json.loads(match.group())
        plan = BlogPlan(**plan_dict)

        logger.info(f"Plan ready: '{plan.title}' — {len(plan.sections)} sections")

        return {"plan": plan.model_dump()}

    except json.JSONDecodeError as e:
        logger.error(f"Planner JSON parse error: {e}")
        raise ValueError(f"Malformed JSON from planner: {e}") from e