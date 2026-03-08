from app.services.llm_service import get_llm
from app.schemas.blog_schema import BlogPlan
import json
import re

llm = get_llm()


def planner_node(state: dict):

    topic = state["topic"]

    prompt = f"""
You are a professional blog planner.

Create a structured outline for a technical blog.

Topic: {topic}

Return ONLY valid JSON in this format:

{{
"title": "Blog Title",
"sections": [
{{
"title": "Section Title",
"subsections": [
"Subtopic 1",
"Subtopic 2"
]
}}
]
}}

Rules:
- Create 5 sections
- Each section must contain 2 subsections
- Return ONLY JSON
"""

    response = llm.invoke(prompt).content

    json_match = re.search(r"\{[\s\S]*\}", response)

    if not json_match:
        raise ValueError("Planner did not return valid JSON")

    plan_dict = json.loads(json_match.group())

    # validate using Pydantic
    plan = BlogPlan(**plan_dict)

    return {"plan": plan.model_dump()}