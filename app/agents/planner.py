from app.services.llm_service import get_llm
import json
import re

llm = get_llm()

def planner_node(state: dict):

    topic = state["topic"]
    evidence = state.get("evidence", [])

    evidence_text = ""

    for e in evidence:
        evidence_text += f"{e['title']}\n{e['content']}\n\n"

    prompt = f"""
You are a professional blog planner.

Create a blog outline in JSON format.

Topic:
{topic}

Return ONLY JSON like this:

{{
"title": "Blog Title",
"sections": [
"Section 1",
"Section 2",
"Section 3",
"Section 4",
"Section 5"
]
}}
"""

    response = llm.invoke(prompt).content

    # extract JSON safely
    json_match = re.search(r"\{.*\}", response, re.DOTALL)

    if json_match:
        plan = json.loads(json_match.group())
    else:
        raise ValueError("Planner did not return valid JSON")

    return {"plan": plan}