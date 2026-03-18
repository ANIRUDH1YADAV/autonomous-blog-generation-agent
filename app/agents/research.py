import logging
from langchain_tavily import TavilySearch

logger = logging.getLogger(__name__)

# One shared search tool — no need to recreate per call
search_tool = TavilySearch(max_results=5)


def research_node(state: dict) -> dict:
    """
    Searches the web for relevant information about the topic.
    Stores clean evidence (title, url, summary) for the planner
    to use when structuring the blog outline.
    """
    topic = state["topic"]

    logger.info(f"Researching topic: '{topic}'")

    try:
        response = search_tool.invoke(topic)
        results = response.get("results", [])

        # Keep only what downstream agents actually need
        evidence = [
            {
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": r.get("content", "")[:500]  # trim long pages
            }
            for r in results
            if r.get("content")  # skip empty results
        ]

        logger.info(f"Research found {len(evidence)} useful sources")

        return {"evidence": evidence}

    except Exception as e:
        logger.error(f"Research failed for topic '{topic}': {e}")
        # Return empty evidence so the graph can continue gracefully
        return {"evidence": []}