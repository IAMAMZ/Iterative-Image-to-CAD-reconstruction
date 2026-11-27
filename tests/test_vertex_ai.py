"""Vertex AI backend, with the Gemini client stubbed out (no network, no GCP credentials)."""
from types import SimpleNamespace

import pytest

import vertex_ai
import vlm

ENV_KEYS = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "VERTEX_MODEL",
            "VERTEX_THINKING_LEVEL", "VERTEX_MAX_OUTPUT_TOKENS"]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated config: no real .env, no cached client; a fake project and model."""
    for k in ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(vertex_ai, "ENV_FILE", tmp_path / "missing.env")
    monkeypatch.setattr(vertex_ai, "_client", None)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("VERTEX_MODEL", "gemini-test-flash")
    return monkeypatch


class FakeModels:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def generate_content(self, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def fake_response(text="CHANGE: dimensional - x\n```python\nresult = 1\n```", finish="STOP",
                  prompt=120, out=30, thoughts=50):
    return SimpleNamespace(
        text=text, candidates=[SimpleNamespace(finish_reason=finish)],
        usage_metadata=SimpleNamespace(prompt_token_count=prompt, candidates_token_count=out,
                                       thoughts_token_count=thoughts))


def install(env, *replies):
    models = FakeModels(replies or [fake_response()])
    env.setattr(vertex_ai, "_client", SimpleNamespace(models=models))
    return models


MESSAGES = [{"role": "system", "content": "You are a CAD engineer."},
            {"role": "user", "content": "Fix it.", "images": [b"\x89PNG-a", b"\x89PNG-b"]},
            {"role": "assistant", "content": "CHANGE: ..."},
            {"role": "user", "content": "That program failed."}]


def test_load_env_parses_and_never_overrides(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("# comment\nA_X=1\nexport A_Y='two words'\nA_Z=3 # trailing\nA_W=keep\n\nbad\n")
    for k in ["A_X", "A_Y", "A_Z"]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("A_W", "shell")
    vertex_ai.load_env(f)
    import os
    assert (os.environ["A_X"], os.environ["A_Y"], os.environ["A_Z"]) == ("1", "two words", "3")
    assert os.environ["A_W"] == "shell"


def test_config_defaults_and_missing_project(env):
    cfg = vertex_ai.config()
    assert cfg["project"] == "test-project" and cfg["model"] == "gemini-test-flash"
    assert cfg["location"] == "global" and cfg["thinking_level"] is None
    assert cfg["max_output_tokens"] == vertex_ai.DEFAULT_MAX_OUTPUT_TOKENS
    env.delenv("GOOGLE_CLOUD_PROJECT")
    with pytest.raises(RuntimeError, match="GOOGLE_CLOUD_PROJECT"):
        vertex_ai.config()


def test_to_contents_maps_roles_and_images():
    system, contents = vertex_ai.to_contents(MESSAGES)
    assert system == "You are a CAD engineer."
    assert [c.role for c in contents] == ["user", "model", "user"]
    first = contents[0].parts
    assert [p.inline_data.data for p in first[:2]] == [b"\x89PNG-a", b"\x89PNG-b"]
    assert first[0].inline_data.mime_type == "image/png"
    assert first[2].text == "Fix it."


def test_chat_returns_text_and_stats(env):
    models = install(env)
    text, st = vertex_ai.chat(MESSAGES, "gemini-test-flash", False, 0.4, 16384, 2500, 60)
    assert text.startswith("CHANGE:")
    assert st["prompt_tokens"] == 120 and st["output_tokens"] == 80 and st["thoughts_tokens"] == 50
    assert st["cut_off"] is None
    call = models.calls[0]
    assert call["model"] == "gemini-test-flash"
    assert call["config"].temperature == 0.4
    assert call["config"].system_instruction == "You are a CAD engineer."
    assert call["config"].thinking_config is None


def test_chat_think_and_cut_off(env):
    env.setenv("VERTEX_THINKING_LEVEL", "low")
    models = install(env, fake_response(finish="FinishReason.MAX_TOKENS"), fake_response())
    _, st = vertex_ai.chat(MESSAGES, None, False, 0.4, 0, 0, 60)
    assert st["cut_off"] == "max_tokens"
    assert models.calls[0]["model"] == "gemini-test-flash"          # falls back to VERTEX_MODEL
    assert "LOW" in str(models.calls[0]["config"].thinking_config.thinking_level)
    vertex_ai.chat(MESSAGES, None, True, 0.4, 0, 0, 60)
    assert "HIGH" in str(models.calls[1]["config"].thinking_config.thinking_level)


def test_chat_retries_rate_limits_only(env):
    env.setattr(vertex_ai.time, "sleep", lambda s: None)
    busy = Exception("quota"); busy.code = 429
    models = install(env, busy, fake_response(text="ok"))
    assert vertex_ai.chat(MESSAGES, None, False, 0.4, 0, 0, 60)[0] == "ok"
    assert len(models.calls) == 2
    bad = Exception("bad request"); bad.code = 400
    install(env, bad)
    with pytest.raises(Exception, match="bad request"):
        vertex_ai.chat(MESSAGES, None, False, 0.4, 0, 0, 60)


def test_chat_retries_dropped_connections(env):
    env.setattr(vertex_ai.time, "sleep", lambda s: None)
    ReadTimeout = type("ReadTimeout", (Exception,), {})
    ConnectError = type("ConnectError", (Exception,), {})
    models = install(env, ReadTimeout("slow"), ConnectError("wifi"), fake_response(text="ok"))
    assert vertex_ai.chat(MESSAGES, None, False, 0.4, 0, 0, 60)[0] == "ok"
    assert len(models.calls) == 3
    install(env, ValueError("a bug, not the network"))
    with pytest.raises(ValueError):
        vertex_ai.chat(MESSAGES, None, False, 0.4, 0, 0, 60)


def test_vlm_dispatches_to_vertex_by_default(env):
    install(env, fake_response(text="NO_CHANGE"))
    assert vlm.DEFAULT_BACKEND == "vertex"
    assert vlm.default_model("vertex") == "gemini-test-flash"
    assert vlm.default_model("ollama") == vlm.OLLAMA_MODEL
    text, _ = vlm.chat([{"role": "user", "content": "hi"}])
    assert text == "NO_CHANGE"


def test_refine_cli_reports_missing_config(env, tmp_path):
    import refine
    env.delenv("VERTEX_MODEL")
    with pytest.raises(SystemExit):
        refine.main([str(tmp_path), "--backend", "vertex", "--out", str(tmp_path / "o")])


def test_empty_assistant_turn_still_has_a_part():
    """Pilot 5 crash: an empty model reply in the history -> 400 'at least one parts field'."""
    _, contents = vertex_ai.to_contents([{"role": "user", "content": "go"},
                                         {"role": "assistant", "content": ""},
                                         {"role": "user", "content": "That program failed."}])
    assert all(c.parts for c in contents)
    assert contents[1].parts[0].text == vertex_ai.EMPTY_PLACEHOLDER


def function_call_only(prompt=100, out=5):
    """A reply whose only part is a hallucinated function_call (no text)."""
    from google.genai import types
    content = types.Content(role="model", parts=[types.Part(
        function_call=types.FunctionCall(name="run_code", args={}))])
    return SimpleNamespace(
        text=None, candidates=[SimpleNamespace(content=content, finish_reason="STOP")],
        usage_metadata=SimpleNamespace(prompt_token_count=prompt, candidates_token_count=out,
                                       thoughts_token_count=0))


def test_reply_without_text_is_retried_and_billed(env):
    models = install(env, function_call_only(), fake_response(text="ok", prompt=100, out=7,
                                                              thoughts=3))
    text, st = vertex_ai.chat(MESSAGES, None, False, 0.4, 0, 0, 60)
    assert text == "ok" and len(models.calls) == 2 and st["empty_retries"] == 1
    assert st["prompt_tokens"] == 200 and st["output_tokens"] == 5 + 10


def test_reply_without_text_gives_up_with_empty_string(env):
    models = install(env, *[function_call_only() for _ in range(vertex_ai.EMPTY_RETRIES + 1)])
    text, st = vertex_ai.chat(MESSAGES, None, False, 0.4, 0, 0, 60)
    assert text == "" and len(models.calls) == vertex_ai.EMPTY_RETRIES + 1
