"""Noticias de hoy sobre audición: hardware (OTC, gafas, Auracast) y biotech/cura."""
import calendar
import datetime as dt
import json
import os
import re
import urllib.parse
from zoneinfo import ZoneInfo

import feedparser
import requests

TZ = ZoneInfo("Europe/Madrid")
GN = "https://news.google.com/rss/search?q={q}+when:1d&hl={hl}&gl={gl}&ceid={ceid}"
EN = ("en-US", "US", "US:en")
ES = ("es", "ES", "ES:es")

QUERIES = [
    # hardware
    ('"OTC hearing aid"', EN), ('"hearing aid" earbuds', EN), ('"smart glasses" hearing OR captions', EN),
    ("Auracast", EN), ('"LE Audio" hearing', EN), ('"hearing aid" new feature', EN),
    ("audífonos sin receta", ES), ("gafas inteligentes subtítulos sordera", ES),
    # biotech / cura
    ('"hearing loss" gene therapy', EN), ("hair cell regeneration", EN), ("OTOF hearing", EN),
    ('"hearing loss" cure', EN), ("site:hearingtracker.com", EN), ("hipoacusia terapia génica", ES),
]
FEEDS = [
    "https://www.hearingreview.com/feed",
    "https://www.sciencedaily.com/rss/mind_brain/hearing_loss.xml",
]

HW_KW = ["otc", "hearing aid", "audífono", "audifono", "earbud", "airpods", "auracast", "le audio",
         "hearing-aid"]
GLASSES_KW = ["smart glasses", "gafas inteligentes", "ar glasses"]
ACCESS_KW = ["hearing", "caption", "subtít", "subtit", "deaf", "sordera", "sordo", "audici"]
BIO_KW = ["gene therapy", "terapia génica", "terapia genica", "hair cell", "otof", "regenerat", "stem cell",
          "células madre", "celulas madre", "hearing loss cure", "cure for hearing", "cura de la sordera"]
EXCLUDE_KW = ["cochlear", "coclear"]
NOISE_KW = ["forum", "council", "ball ", "recording", "grabaciones"]

# Modelos gratuitos de OpenRouter, en orden de preferencia (los :free tienen cupos y caen a veces).
MODELS = os.environ.get("OPENROUTER_MODELS", "google/gemma-4-31b-it:free,nvidia/nemotron-3-super-120b-a12b:free,google/gemma-4-26b-a4b-it:free").split(",")
MODELS_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_PER_SECTION = 8


def _today():
    forced = os.environ.get("PANEL_TODAY")  # solo para pruebas: YYYY-MM-DD
    return dt.date.fromisoformat(forced) if forced else dt.datetime.now(TZ).date()


def _published(entry):
    p = entry.get("published_parsed") or entry.get("updated_parsed")
    if not p:
        return None
    return dt.datetime.fromtimestamp(calendar.timegm(p), dt.timezone.utc).astimezone(TZ)


def _norm(title):
    return re.sub(r"\W+", " ", re.sub(r"\s-\s[^-]+$", "", title).lower()).strip()


def _gather(today):
    urls = [GN.format(q=urllib.parse.quote(q), hl=hl, gl=gl, ceid=ceid) for q, (hl, gl, ceid) in QUERIES]
    urls += FEEDS
    found, seen_titles = {}, set()
    for u in urls:
        try:
            feed = feedparser.parse(u, request_headers={"User-Agent": "Mozilla/5.0 panel-atajo"})
        except Exception:
            continue
        for e in feed.entries:
            pub = _published(e)
            if not pub or pub.date() != today:  # frescura estricta: solo hoy
                continue
            link, title = e.get("link"), e.get("title", "").strip()
            key = _norm(title)
            if not link or not title or link in found or key in seen_titles:
                continue
            seen_titles.add(key)
            found[link] = {"title": title, "summary": re.sub(r"<[^>]+>", "", e.get("summary", ""))[:300]}
    return found


def _keyword_classify(item):
    """Respaldo sin LLM: solo mira el titular para evitar ruido de foros y resúmenes."""
    t = item["title"].lower()
    if any(k in t for k in EXCLUDE_KW + NOISE_KW):
        return "descartar"
    if any(k in t for k in BIO_KW):
        return "biotech"
    if any(k in t for k in GLASSES_KW) and any(k in t for k in ACCESS_KW):
        return "hardware"
    if any(k in t for k in HW_KW):
        return "hardware"
    return "descartar"


def _llm_classify(new, token):
    listing = [{"id": i, "title": it["title"], "summary": it["summary"]} for i, (_, it) in enumerate(new.items())]
    prompt = (
        "Clasifica noticias sobre audición. Para cada una devuelve category: "
        "'hardware' (audífonos OTC, auriculares/AirPods con función de audífono, gafas inteligentes con subtítulos o "
        "audición asistida, Auracast/LE Audio, gadgets de accesibilidad auditiva), "
        "'biotech' (terapia génica, regeneración de células ciliadas, avances hacia la cura de la hipoacusia) o "
        "'descartar'. Descarta SIEMPRE implantes cocleares, publicidad sin novedad, ofertas y noticias no relacionadas. "
        "Añade 'titulo' (titular en español, sin el nombre del medio) y 'resumen' (una línea en español, máx. 140 caracteres). "
        'Responde SOLO con JSON: {"items":[{"id":0,"category":"...","titulo":"...","resumen":"..."}]}\n\n'
        + json.dumps(listing, ensure_ascii=False)
    )
    last = None
    for model in MODELS:
        try:
            r = requests.post(
                MODELS_URL,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
                timeout=120,
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            out = json.loads(text[text.index("{"): text.rindex("}") + 1])["items"]
            return {x["id"]: x for x in out}
        except Exception as e:
            last = f"{model}: {e!r}"
            print(f"[hearing] {last}")
    raise RuntimeError(last)


def fetch(prev_state, token=None):
    """Devuelve (sección_hw, sección_bio, nuevo_estado)."""
    today = _today()
    state = prev_state if prev_state and prev_state.get("day") == str(today) else {"day": str(today), "classified": {}}
    classified = state["classified"]
    found = _gather(today)
    new = {u: it for u, it in found.items() if u not in classified}

    if new:
        llm = {}
        if token:
            try:
                llm = _llm_classify(new, token)
            except Exception as e:
                print(f"[hearing] LLM falló, uso palabras clave: {e}")
        for i, (u, it) in enumerate(new.items()):
            res = llm.get(i)
            if res and res.get("category") in ("hardware", "biotech", "descartar"):
                cat = res["category"]
                title, summary = res.get("titulo") or it["title"], res.get("resumen", "")
            else:
                cat = _keyword_classify(it)
                title, summary = re.sub(r"\s-\s[^-]+$", "", it["title"]), ""
            classified[u] = {"cat": cat, "title": title, "summary": summary}

    def section(cat, sid, title):
        rows = [(u, c) for u, c in classified.items() if c["cat"] == cat][:MAX_PER_SECTION]
        if not rows:
            text = "Sin novedades hoy."
        else:
            text = "\n\n".join(f"• {c['title']}" + (f"\n  {c['summary']}" if c["summary"] else "") for _, c in rows)
        return {"id": sid, "title": title, "text": text,
                "items": [{"title": c["title"], "url": u} for u, c in rows]}

    return (section("hardware", "audicion-hw", "🦻 Audición: hardware"),
            section("biotech", "audicion-bio", "🧬 Audición: biotech/cura"),
            state)
