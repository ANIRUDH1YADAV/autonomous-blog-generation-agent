from app.agents.reducer import reducer_node

state = {
    "plan": {
        "title": "Test Blog"
    },
    "written_sections": [
        "## Intro\nThis is intro",
        "## Section\nThis is section"
    ]
}

result = reducer_node(state)

print(result["final_blog"])