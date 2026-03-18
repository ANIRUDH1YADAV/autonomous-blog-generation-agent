import logging
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def writer_node(state: dict) -> dict:
    """
    Writes one section of the blog. Each writer branch receives
    its own section via Send(), so multiple sections are written
    in parallel. Results accumulate in written_sections via operator.add.
    """
    topic   = state["topic"]
    section = state["section"]
    title   = section["title"]
    subsections = section.get("subsections", [])

    subsection_list = "\n".join(f"  - {s}" for s in subsections)

    prompt = f"""You are a skilled technical writer working on one section of a blog.

Blog Topic: {topic}
Section Title: {title}

Cover these subsections naturally within your writing:
{subsection_list}

Writing rules:
- Do NOT repeat the blog title or introduce the whole article
- Write only this section — assume the reader has context
- Use clear headings for each subsection (### level)
- Be specific and practical, not generic
- Aim for 200-300 words for this section
- Write in a confident, direct tone — like a senior engineer sharing knowledge"""

    llm = get_llm()
    logger.info(f"Writing section: '{title}'")

    content = ""
    try:
        for chunk in llm.stream(prompt):
            token = chunk.content or ""
            content += token

        logger.info(f"Section done: '{title}' ({len(content)} chars)")

        return {
            "written_sections": [f"## {title}\n\n{content}"]
        }

    except Exception as e:
        logger.error(f"Writer failed for section '{title}': {e}")
        # Return placeholder so reducer doesn't silently skip a section
        return {
            "written_sections": [f"## {title}\n\n*Section could not be generated.*"]
        }