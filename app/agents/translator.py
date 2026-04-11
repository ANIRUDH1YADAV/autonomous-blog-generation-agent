import logging

from app.schemas.llm_outputs import TranslationOutput
from app.services.llm_json import parse_json_to_model
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def translator_node(state: dict) -> dict:
    """
    Translates the full draft blog into target_language while preserving markdown.
    """
    draft_blog = state.get("draft_blog", "")
    target_language = state.get("target_language", "english")

    if not draft_blog:
        logger.warning("Translator received empty draft_blog; skipping translation")
        return {"draft_blog": draft_blog}

    llm = get_llm()
    prompt = f"""Translate the markdown below into {target_language}.

Requirements:
- Preserve markdown headings and structure.
- Preserve code blocks exactly if present.
- Do not add explanations.

Return ONLY valid JSON in this shape:
{{
  "draft_blog": "translated markdown"
}}

No extra keys.

Markdown:
{draft_blog}
"""

    try:
        raw = llm.invoke(prompt).content
        parsed = parse_json_to_model(raw, TranslationOutput)
        translated_blog = parsed.draft_blog.strip()
        if not translated_blog:
            translated_blog = draft_blog

        logger.info("Translation complete for target_language='%s'", target_language)
        return {"draft_blog": translated_blog}

    except Exception as exc:
        logger.error("Translation failed: %s", exc)
        return {"draft_blog": draft_blog}
