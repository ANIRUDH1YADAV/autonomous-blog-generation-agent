import logging

logger = logging.getLogger(__name__)


def reducer_node(state: dict) -> dict:
    """
    Assembles all written sections and generated images
    into the final blog post. This is the last node before END,
    so it owns the shape of the final output.
    """
    title    = state["plan"]["title"]
    sections = state.get("written_sections", [])
    images   = state.get("images", [])

    logger.info(f"Reducing {len(sections)} sections into final blog: '{title}'")

    blog_parts = [f"# {title}\n"]

    for i, section in enumerate(sections):
        blog_parts.append(section)

        # Insert image after each section if one is available
        if i < len(images):
            img = images[i]
            alt  = img.get("alt", "Diagram")
            path = img.get("path", "")
            blog_parts.append(f"![{alt}]({path})\n")

    final_blog = "\n\n".join(blog_parts)

    logger.info(f"Final blog assembled — {len(final_blog)} characters")

    return {"final_blog": final_blog}