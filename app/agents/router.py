from app.services.llm_service import get_llm

llm = get_llm()


def router_node(state: dict):

    topic = state.get("topic")

    prompt = f"""
Decide if this topic needs internet research.

Topic: {topic}

Answer with only one word:
research
or
no_research
"""
    response = llm.invoke(prompt)
    result = response.content.strip().lower()

    if result == "research":
        state["mode"] = "research"
    else:
        state["mode"] = "no_research"

    return state