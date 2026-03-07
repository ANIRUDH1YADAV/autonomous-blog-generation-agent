from app.agents.planner import planner_node

state = {
    "topic": "Self Attention in Transformers",
    "evidence": []
}

result = planner_node(state)

print(result)