from unittest import result

from app.services.llm_service import get_llm

llm = get_llm()

def router_node(state: dict):

    topic = state["topic"]

    prompt = f"""
Decide if this topic needs internet research.

Topic: {topic}

Answer with only one word:
research
or
no_research
"""

    result = llm.invoke(prompt).content.strip().lower()

   if result == "research":
        return {"mode" : "research"}
    else:
        return {"mode" : "no_research"}