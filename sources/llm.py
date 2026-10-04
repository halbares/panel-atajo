"""Cliente mínimo de Groq (cuota gratuita, API tipo OpenAI) con respaldo entre modelos."""
import json
import os
import time

import requests

MODELS = os.environ.get("LLM_MODELS", "openai/gpt-oss-120b,qwen/qwen3.8-27b,openai/gpt-oss-20b").split(",")
URL = "https://api.groq.com/openai/v1/chat/completions"


def chat_json(prompt, token, tag="llm"):
    """Pide JSON al primer modelo que responda. Imprime el uso de tokens y el cupo restante."""
    last = None
    for model in MODELS:
        body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0,
                "response_format": {"type": "json_object"}}
        if model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = "low"  # sin esto gasta miles de tokens razonando y puede dejar la respuesta vacía
        try:
            for attempt in range(2):
                r = requests.post(URL, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                  json=body, timeout=120)
                if r.status_code == 429 and attempt == 0:  # tope por minuto: espera y reintenta una vez
                    time.sleep(min(float(r.headers.get("retry-after", 15)), 30))
                    continue
                break
            r.raise_for_status()
            u = r.json().get("usage", {})
            print(f"[{tag}] {model}: {u.get('prompt_tokens')}+{u.get('completion_tokens')} tokens, "
                  f"restan {r.headers.get('x-ratelimit-remaining-requests')} req/día, "
                  f"{r.headers.get('x-ratelimit-remaining-tokens')} tokens/min")
            text = r.json()["choices"][0]["message"]["content"]
            return json.loads(text[text.index("{"): text.rindex("}") + 1])
        except Exception as e:
            last = f"{model}: {e!r}"
            print(f"[{tag}] {last}")
    raise RuntimeError(last)
