"""Gemini on Vertex AI as the agent's VLM backend (vlm.chat(..., backend="vertex")).

Configuration comes from the environment, filled from a `.env` file at the repo root
(see .env.example; variables already set in the shell win):
  GOOGLE_CLOUD_PROJECT      GCP project id (required)
  GOOGLE_CLOUD_LOCATION     Vertex region, default "global"
  VERTEX_MODEL              model id, e.g. gemini-3.8-flash
  VERTEX_THINKING_LEVEL     optional: minimal | low | medium | high (unset = model default;
                            --think forces high)
  VERTEX_MAX_OUTPUT_TOKENS  optional cap on reply + thinking tokens (default 32768)

Authentication is Application Default Credentials; run once in a terminal:
    gcloud auth application-default login
"""
import os
import time
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"
DEFAULT_LOCATION = "global"
DEFAULT_MAX_OUTPUT_TOKENS = 32768
RETRIES = 4          # on 429 / 5xx, with exponential backoff
RETRY_STATUS = {429, 500, 502, 503, 504}
EMPTY_RETRIES = 2    # re-ask when the reply has no text (e.g. a hallucinated function_call)
EMPTY_PLACEHOLDER = "(empty reply)"


def load_env(path: Path | None = None) -> None:
    """Minimal .env reader: KEY=VALUE lines, # comments, optional quotes. Never overrides
    variables already in the environment."""
    path = ENV_FILE if path is None else path
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        else:
            val = val.split(" #", 1)[0].strip()
        os.environ.setdefault(key, val)


def config() -> dict:
    load_env()
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is not set; copy .env.example to .env and fill it in")
    model = os.environ.get("VERTEX_MODEL", "").strip()
    if not model:
        raise RuntimeError("VERTEX_MODEL is not set; copy .env.example to .env and fill it in")
    return {"project": project,
            "location": os.environ.get("GOOGLE_CLOUD_LOCATION", "").strip() or DEFAULT_LOCATION,
            "model": model,
            "thinking_level": os.environ.get("VERTEX_THINKING_LEVEL", "").strip().lower() or None,
            "max_output_tokens": int(os.environ.get("VERTEX_MAX_OUTPUT_TOKENS")
                                     or DEFAULT_MAX_OUTPUT_TOKENS)}


def default_model() -> str:
    return config()["model"]


_client = None


def get_client():
    """One genai.Client per process (the SDK is imported lazily so other backends and the
    tests do not need it)."""
    global _client
    if _client is None:
        from google import genai
        cfg = config()
        _client = genai.Client(vertexai=True, project=cfg["project"], location=cfg["location"])
    return _client


def to_contents(messages):
    """vlm-style messages -> (system_instruction, contents) for google-genai.
    Roles: system -> system_instruction, assistant -> model; images are PNG bytes."""
    from google.genai import types
    system, contents = [], []
    for m in messages:
        if m["role"] == "system":
            system.append(m["content"])
            continue
        parts = [types.Part.from_bytes(data=b, mime_type="image/png") for b in m.get("images") or []]
        if m.get("content"):
            parts.append(types.Part.from_text(text=m["content"]))
        if not parts:               # Vertex rejects a turn with no parts (400 INVALID_ARGUMENT)
            parts.append(types.Part.from_text(text=EMPTY_PLACEHOLDER))
        role = "model" if m["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=parts))
    return ("\n\n".join(system) or None), contents


def _status(exc):
    return getattr(exc, "code", None) or getattr(exc, "status_code", None)


def _text(resp) -> str:
    """Text parts only; non-text parts (function_call, ...) are dropped without the SDK warning."""
    try:
        parts = resp.candidates[0].content.parts or []
    except (AttributeError, IndexError, TypeError):
        return getattr(resp, "text", None) or ""
    return "".join(p.text for p in parts if getattr(p, "text", None) and not getattr(p, "thought", False))


def _generate(client, model, contents, gen_cfg):
    for attempt in range(RETRIES + 1):
        try:
            return client.models.generate_content(model=model, contents=contents, config=gen_cfg)
        except Exception as e:  # noqa: BLE001 - SDK raises several error types
            if _status(e) not in RETRY_STATUS or attempt == RETRIES:
                raise
            time.sleep(min(60, 2 ** attempt * 5))


def chat(messages, model, think, temperature, num_ctx, max_tokens, deadline):
    """vlm backend signature. `num_ctx` is ignored (Gemini's context is fixed) and
    `max_tokens` is replaced by VERTEX_MAX_OUTPUT_TOKENS, because Gemini counts thinking
    tokens against the output cap. -> (reply text, stats)."""
    from google.genai import types
    cfg = config()
    system, contents = to_contents(messages)
    level = "high" if think else cfg["thinking_level"]
    gen_cfg = types.GenerateContentConfig(
        system_instruction=system, temperature=temperature,
        max_output_tokens=cfg["max_output_tokens"],
        thinking_config=types.ThinkingConfig(thinking_level=level.upper()) if level else None,
        http_options=types.HttpOptions(timeout=int(deadline * 1000)))
    client = get_client()
    t0 = time.time()
    empty, tok = 0, {"prompt": 0, "out": 0, "thoughts": 0}
    while True:
        resp = _generate(client, model or cfg["model"], contents, gen_cfg)
        usage = getattr(resp, "usage_metadata", None)      # every attempt is billed
        tok["prompt"] += getattr(usage, "prompt_token_count", None) or 0
        tok["thoughts"] += getattr(usage, "thoughts_token_count", None) or 0
        tok["out"] += (getattr(usage, "candidates_token_count", None) or 0) + \
                      (getattr(usage, "thoughts_token_count", None) or 0)
        text = _text(resp)
        if text.strip() or empty == EMPTY_RETRIES:
            break
        empty += 1
    finish = None
    if getattr(resp, "candidates", None):
        finish = str(getattr(resp.candidates[0], "finish_reason", "") or "")
    stats = {"seconds": round(time.time() - t0, 1),
             "prompt_tokens": tok["prompt"], "output_tokens": tok["out"],
             "thoughts_tokens": tok["thoughts"],
             "cut_off": "max_tokens" if finish and "MAX_TOKENS" in finish else None,
             "finish_reason": finish, "empty_retries": empty}
    return text, stats
