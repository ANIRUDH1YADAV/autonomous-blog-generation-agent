from dotenv import load_dotenv
load_dotenv()


from langchain_community.tools.tavily_search import TavilySearchResults

search_tool = TavilySearchResults(max_results=3)

def research_node(state: dict):

    topic = state["topic"]

    results = search_tool.invoke({
        "query": topic
    })

    evidence = []

    for r in results:
        evidence.append({
            "title": r["title"],
            "url": r["url"],
            "content": r["content"]
        })

    return {
        "evidence": evidence
    }