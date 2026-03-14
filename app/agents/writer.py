from app.services.llm_service import get_llm

llm = get_llm()


def writer_node(state: dict):

    topic = state["topic"]
    section = state["section"]

    title = section["title"]
    subsections = section.get("subsections", [])

    prompt = f"""
You are a technical blog writer.

Write the section of a blog.

Topic: {topic}

Section Title: {title}

Cover these subsections:
{subsections}

Rules:
- Do NOT repeat the blog title
- Do NOT introduce the entire article again
- Write only this section
"""

    response = ""

    # stream tokens from the LLM
    for chunk in llm.stream(prompt):

        token = chunk.content or ""

        response += token

    return {
        "written_sections": [f"## {title}\n{response}"]
    }