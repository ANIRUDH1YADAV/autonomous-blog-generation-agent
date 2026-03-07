def reducer_node(state: dict):

    title = state["plan"]["title"]
    sections = state["written_sections"]

    blog = f"# {title}\n\n"

    for section in sections:
        blog += section + "\n\n"

    return {
        "final_blog": blog
    }