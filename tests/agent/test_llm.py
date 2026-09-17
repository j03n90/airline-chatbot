from backend.agent.llm import chat_model, complete, openai_compatible_base_url


def test_openai_compatible_base_url_appends_v1():
    assert openai_compatible_base_url("https://api.deepseek.com") == "https://api.deepseek.com/v1"
    assert openai_compatible_base_url("https://api.deepseek.com/") == "https://api.deepseek.com/v1"


def test_openai_compatible_base_url_does_not_double_v1():
    assert openai_compatible_base_url("https://api.openai.com/v1") == "https://api.openai.com/v1"
    assert openai_compatible_base_url("https://api.openai.com/v1/") == "https://api.openai.com/v1"


def test_chat_model_none_without_key(monkeypatch):
    monkeypatch.setattr("backend.agent.llm.settings.api_key", "")
    assert chat_model() is None
    assert complete("system", "user") == ""


def test_chat_model_uses_settings(monkeypatch):
    captured: dict = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("backend.agent.llm.ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setattr("backend.agent.llm.settings.api_key", "sk-test")
    monkeypatch.setattr("backend.agent.llm.settings.base_url", "https://api.deepseek.com")
    monkeypatch.setattr("backend.agent.llm.settings.model", "deepseek-chat")
    model = chat_model()
    assert isinstance(model, FakeChatOpenAI)
    assert captured["model"] == "deepseek-chat"
    assert captured["api_key"] == "sk-test"
    assert captured["base_url"] == "https://api.deepseek.com/v1"
    assert captured["temperature"] == 0


def test_chat_model_keeps_existing_v1(monkeypatch):
    captured: dict = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("backend.agent.llm.ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setattr("backend.agent.llm.settings.api_key", "sk-test")
    monkeypatch.setattr("backend.agent.llm.settings.base_url", "https://api.openai.com/v1")
    monkeypatch.setattr("backend.agent.llm.settings.model", "gpt-4o-mini")
    chat_model()
    assert captured["base_url"] == "https://api.openai.com/v1"
    assert captured["model"] == "gpt-4o-mini"
