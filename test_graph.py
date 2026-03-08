from app.graph.workflow import graph

state = {
    "topic": "Self Attention in Transformers"
}

result = graph.invoke(state)

print(result["final_blog"])