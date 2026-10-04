"""Artículos destacados del NYT (tecnología, salud, gadgets) con titular y resumen en español."""
import json
import re

import feedparser

from . import llm

FEEDS = [
    ("nyt-tech", "💻 NYT: Tecnología", "Technology"),
    ("nyt-salud", "🩺 NYT: Salud", "Health"),
    ("nyt-gadgets", "🔌 NYT: Gadgets", "PersonalTech"),
]
TOP = 5
BATCH = 15


def _read(slug):
    f = feedparser.parse(f"https://rss.nytimes.com/services/xml/rss/nyt/{slug}.xml",
                         request_headers={"User-Agent": "Mozilla/5.0 panel-atajo"})
    if not f.entries:
        raise RuntimeError(f"feed {slug} vacío")
    return f.entries


def _translate(arts, token):
    """arts: {url: {"title","summary"}} -> {url: {"titulo","resumen"}} (en lotes, para cuidar los tokens)."""
    items, out = list(arts.items()), {}
    for i in range(0, len(items), BATCH):
        chunk = items[i:i + BATCH]
        listing = [{"id": k, "title": a["title"], "summary": a["summary"]} for k, (_, a) in enumerate(chunk)]
        prompt = (
            "Traduce al español (neutro) estos artículos de The New York Times. Para cada uno devuelve 'titulo' "
            "(titular fiel, natural) y 'resumen' (una línea, máx. 140 caracteres). "
            'Responde SOLO con JSON: {"items":[{"id":0,"titulo":"...","resumen":"..."}]}\n\n'
            + json.dumps(listing, ensure_ascii=False)
        )
        res = {x["id"]: x for x in llm.chat_json(prompt, token, "articles")["items"]}
        for k, (url, _) in enumerate(chunk):
            if k in res and res[k].get("titulo"):
                out[url] = {"titulo": res[k]["titulo"], "resumen": res[k].get("resumen", "")}
    return out


def fetch(cache, token=None):
    """Devuelve (lista_de_secciones, cache_nuevo). Cache: url -> {titulo, resumen}."""
    picked, seen = [], set()
    for sid, title, slug in FEEDS:
        rows = []
        for e in _read(slug):
            link = e.get("link")
            if not link or link in seen:
                continue
            seen.add(link)
            rows.append((link, {"title": e.get("title", "").strip(),
                                "summary": re.sub(r"<[^>]+>", "", e.get("summary", ""))[:300]}))
            if len(rows) == TOP:
                break
        picked.append((sid, title, rows))

    todo = {u: a for _, _, rows in picked for u, a in rows if u not in cache}
    if todo and token:
        try:
            cache = {**cache, **_translate(todo, token)}
        except Exception as e:
            print(f"[articles] traducción falló, se muestra en inglés: {e}")
    cache = {u: c for u, c in cache.items() if u in {u for _, _, rows in picked for u, _ in rows}}

    sections = []
    for sid, title, rows in picked:
        blocks, items = [], []
        for url, a in rows:
            c = cache.get(url, {})
            t = c.get("titulo") or a["title"]
            blocks.append(f"• {t}" + (f"\n  {c['resumen']}" if c.get("resumen") else ""))
            items.append({"title": t, "url": url})
        sections.append({"id": sid, "title": title, "text": "\n\n".join(blocks), "items": items})
    return sections, cache
