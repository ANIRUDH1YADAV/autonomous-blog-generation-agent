from app.agents.research import research_node


class _FakeSearch:
    def invoke(self, _topic: str):
        return {
            "results": [
                {
                    "title": "Doc 1",
                    "url": "https://example.com/1",
                    "content": "A" * 600,
                },
                {
                    "title": "Doc 2",
                    "url": "https://example.com/2",
                    "content": "Useful short summary",
                },
            ]
        }


class _FailingSearch:
    def invoke(self, _topic: str):
        raise RuntimeError("search failed")


def test_research_node_formats_evidence(monkeypatch):
    monkeypatch.setattr("app.agents.research.search_tool", _FakeSearch())

    result = research_node({"topic": "transformers"})
    evidence = result["evidence"]

    assert len(evidence) == 2
    assert evidence[0]["title"] == "Doc 1"
    assert evidence[0]["url"] == "https://example.com/1"
    assert len(evidence[0]["content"]) == 500


def test_research_node_handles_tool_errors(monkeypatch):
    monkeypatch.setattr("app.agents.research.search_tool", _FailingSearch())

    result = research_node({"topic": "transformers"})
    assert result == {"evidence": []}