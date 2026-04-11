from app.graph.workflow import builder


def test_final_dag_nodes_and_linear_edges():
    expected_nodes = {
        "router",
        "web_search",
        "llm_knowledge",
        "brainstorming",
        "content_generation",
        "image_generator",
        "translator",
        "seo_reducer",
        "save_memory",
    }

    assert set(builder.nodes.keys()) == expected_nodes

    expected_edges = {
        ("__start__", "router"),
        ("web_search", "brainstorming"),
        ("llm_knowledge", "brainstorming"),
        ("brainstorming", "content_generation"),
        ("content_generation", "image_generator"),
        ("translator", "seo_reducer"),
        ("seo_reducer", "save_memory"),
        ("save_memory", "__end__"),
    }

    assert builder.edges == expected_edges


def test_final_dag_conditional_routes():
    assert "router" in builder.branches
    assert "image_generator" in builder.branches

    router_routes = builder.branches["router"]["route_after_router"].ends
    image_routes = builder.branches["image_generator"]["route_after_image_generation"].ends

    assert router_routes == {
        "web_search": "web_search",
        "llm_knowledge": "llm_knowledge",
    }

    assert image_routes == {
        "translator": "translator",
        "seo_reducer": "seo_reducer",
    }