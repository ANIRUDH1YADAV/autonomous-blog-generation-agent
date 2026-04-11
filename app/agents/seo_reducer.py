import logging
import re

from app.schemas.llm_outputs import SEOOutput
from app.services.llm_json import parse_json_to_model
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def _fallback_meta(blog_text: str) -> tuple[str, list[str]]:
    plain = re.sub(r"[#*_`\-\n]+", " ", blog_text)
    plain = re.sub(r"\s+", " ", plain).strip()
    meta = (plain[:157] + "...") if len(plain) > 160 else plain

    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", plain.lower())
    unique = []
    for word in words:
        if word not in unique:
            unique.append(word)
        if len(unique) == 8:
            break
    return meta, unique


def seo_reducer_node(state: dict) -> dict:
    """
    Trims and optimizes the generated blog output for SEO metadata.
    """
    title = state.get("title", "Generated Blog")
    draft_blog = state.get("draft_blog", "")

    if not draft_blog:
        logger.warning("SEO reducer received empty draft_blog")
        return {
            "final_blog": f"# {title}\n\nNo content generated.",
            "meta_description": "",
            "keywords": [],
        }

    prompt = f"""You are an SEO reducer agent.

Optimize this markdown blog for clarity and SEO.

Title: {title}

Blog markdown:
{draft_blog}

Return ONLY valid JSON in this shape:
{{
  "final_blog": "optimized markdown blog",
  "meta_description": "max 160 characters",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}

Rules:
- Keep the same meaning.
- Remove repetition and weak filler.
- Keep markdown structure.
- Provide 5-8 concise keywords.
"""

    llm = get_llm()

    try:
        raw = llm.invoke(prompt).content
        parsed = parse_json_to_model(raw, SEOOutput)

        final_blog = parsed.final_blog.strip() or draft_blog
        meta_description = (parsed.meta_description or "").strip()
        keywords = [str(k).strip() for k in parsed.keywords if str(k).strip()]

        if not meta_description:
            meta_description, fallback_keywords = _fallback_meta(final_blog)
            if not keywords:
                keywords = fallback_keywords

        if len(meta_description) > 160:
            meta_description = meta_description[:157].rstrip() + "..."

        if len(keywords) > 8:
            keywords = keywords[:8]

        logger.info("SEO reducer complete with %s keywords", len(keywords))
        return {
            "final_blog": final_blog,
            "meta_description": meta_description,
            "keywords": keywords,
        }

    except Exception as exc:
        logger.error("SEO reducer failed: %s", exc)
        meta_description, keywords = _fallback_meta(draft_blog)
        return {
            "final_blog": draft_blog,
            "meta_description": meta_description,
            "keywords": keywords,
        }
