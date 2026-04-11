from app.agents.router import router_node


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, _prompt: str):
        return _FakeResponse(self._content)


def test_router_selects_web_search_and_translation(monkeypatch):
    monkeypatch.setattr(
        "app.agents.router.get_llm",
        lambda: _FakeLLM('{"decision":"search"}'),
    )

    result = router_node(
        {
            "topic": "latest ai regulation changes",
            "target_language": "hindi",
        }
    )

    assert result["needs_web_search"] is True
    assert result["needs_translation"] is True
    assert result["target_language"] == "hindi"


def test_router_selects_direct_for_english(monkeypatch):
    monkeypatch.setattr(
        "app.agents.router.get_llm",
        lambda: _FakeLLM('{"decision":"direct"}'),
    )

    result = router_node(
        {
            "topic": "how transformers work",
            "target_language": "english",
        }
    )

    assert result["needs_web_search"] is False
    assert result["needs_translation"] is False
    assert result["target_language"] == "english"