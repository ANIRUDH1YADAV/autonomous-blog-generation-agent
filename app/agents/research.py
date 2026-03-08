from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

search_tool = TavilySearch(max_results=3)


def research_node(state: dict):

    topic = state["topic"]

    response = search_tool.invoke(topic)

    results = response.get("results", [])

    evidence = []

    for r in results:
        evidence.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")
        })

    state["evidence"] = evidence

    return state