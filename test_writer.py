from app.agents.writer import writer_node

state = {
    "topic": "Self Attention in Transformers",
    "section": "Introduction to Self Attention"
}

result = writer_node(state)

print(result)