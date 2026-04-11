import logging

from app.schemas.llm_outputs import LLMKnowledgeOutput
from app.services.llm_json import parse_json_to_model
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def llm_knowledge_node(state: dict) -> dict:
    """
    Builds internal-knowledge evidence when web search is not required.
    """
    topic = state["topic"]

    prompt = f"""You are a research assistant.

Topic: {topic}

Generate exactly 5 concise evidence items from stable general knowledge.

Return ONLY valid JSON in this shape:
{{
    "evidence": [
        {{"title": "Knowledge Point 1", "url": "", "content": "..."}},
        {{"title": "Knowledge Point 2", "url": "", "content": "..."}}
    ]
}}

Rules:
- exactly 5 evidence items
- each content field must be one practical fact
- no markdown and no commentary
"""

    llm = get_llm()

    try:
        raw = llm.invoke(prompt).content
        parsed = parse_json_to_model(raw, LLMKnowledgeOutput)

        evidence = []
        for i, item in enumerate(parsed.evidence[:5]):
            content = item.content.strip()[:500]
            if not content:
                continue

            title = item.title.strip() or f"Knowledge Point {i + 1}"
            evidence.append(
                {
                    "title": title,
                    "url": item.url.strip(),
                    "content": content,
                }
            )

        if not evidence:
            evidence = [
                {
                    "title": "Knowledge Point 1",
                    "url": "",
                    "content": f"General background context for {topic}.",
                }
            ]

        logger.info("LLM knowledge node produced %s evidence entries", len(evidence))
        return {"evidence": evidence}

    except Exception as exc:
        logger.error("LLM knowledge node failed: %s", exc)
        return {
            "evidence": [
                {
                    "title": "Knowledge Point 1",
                    "url": "",
                    "content": f"General background context for {topic}.",
                }
            ]
        }
