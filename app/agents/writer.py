from app.services.llm_service import get_llm

llm = get_llm()

def writer_node(state: dict):

    topic = state["topic"]
    section = state["section"]

    prompt = f"""
You are a professional technical blog writer.

Write a detailed blog section.

Topic:
{topic}

Section:
{section}

Write clear explanations and examples if needed.
"""

    response = llm.invoke(prompt).content

    return {
        "section_content": response
    }