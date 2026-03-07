from app.services.llm_service import get_llm

llm = get_llm()

def planner_node(state: dict):

    topic = state["topic"]
    evidence = state.get("evidence", [])

    evidence_text = ""

    for e in evidence:
        evidence_text += f"{e['title']}\n{e['content']}\n\n"

    prompt = f"""
You are a professional blog planner.

Create a structured blog outline.

Topic:
{topic}

Reference information:
{evidence_text}

Return:

Blog Title
Sections list (5-7 sections)
"""

    response = llm.invoke(prompt).content

    return {
        "plan": response
    }