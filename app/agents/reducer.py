def reducer_node(state: dict):

    title = state["plan"]["title"]

    blog = f"# {title}\n\n"

    sections = state["written_sections"]
    images = state.get("images", [])

    for i, section in enumerate(sections):

        blog += section + "\n\n"

        # insert image if available
        if i < len(images):
            blog += f"![Diagram]({images[i]['path']})\n\n"

    state["final_blog"] = blog

    return state