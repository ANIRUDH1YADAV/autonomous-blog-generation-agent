def reducer_node(state: dict):

    title = state["plan"]["title"]

    sections = state.get("written_sections", [])

    blog = f"# {title}\n\n"

    for section in sections:
        blog += section + "\n\n"

    state["final_blog"] = blog

    return state