import re
import time
from collections import Counter

import requests

WANTED = {
    "combined-print-and-e-book-fiction": "Ficción",
    "combined-print-and-e-book-nonfiction": "No ficción",
}
TOP = 5
CACHE_SECONDS = 12 * 3600
VERSION = 2  # sube al cambiar el formato: fuerza refrescar aunque la caché sea reciente
OL = "https://openlibrary.org"


def spanish_title(title, author):
    """Título de la edición en español según Open Library, o None si no hay edición registrada."""
    docs = requests.get(f"{OL}/search.json", params={"title": title, "author": author, "language": "spa",
                                                     "fields": "key", "limit": 1}, timeout=30).json().get("docs", [])
    if not docs:
        return None
    eds = requests.get(f"{OL}{docs[0]['key']}/editions.json", params={"limit": 200}, timeout=30).json().get("entries", [])
    names = []
    for e in eds:
        if any(l["key"] == "/languages/spa" for l in e.get("languages", [])):
            name = re.split(r"\s*[/(:]", e["title"])[0].strip()  # quita "(Original)" y "/ Original"
            if name and name.lower() != title.lower():
                names.append(name)
    return Counter(names).most_common(1)[0][0] if names else None


def fetch(api_key, prev=None):
    # La lista cambia una vez por semana: reutiliza la sección previa si es reciente.
    if prev and prev.get("v") == VERSION and time.time() - prev.get("fetched", 0) < CACHE_SECONDS:
        return prev
    r = requests.get(
        "https://api.nytimes.com/svc/books/v3/lists/overview.json",
        params={"api-key": api_key},
        timeout=30,
    )
    r.raise_for_status()
    lists = r.json()["results"]["lists"]
    lines, items = [], []
    for lst in lists:
        label = WANTED.get(lst["list_name_encoded"])
        if not label:
            continue
        lines.append(f"— {label} —")
        for b in lst["books"][:TOP]:
            title = b["title"].title()
            try:
                es = spanish_title(title, b["author"])
                note = f"🇪🇸 {es}" if es else "🚫 Sin edición en español registrada"
            except Exception as e:
                print(f"[nyt] Open Library falló para {title!r}: {e!r}")
                note = "❔ Sin verificar en español"
            lines.append(f"{b['rank']}. {title} · {b['author']}\n     {note}")
            items.append({"title": f"{title} ({b['author']})", "url": b.get("amazon_product_url") or ""})
    return {
        "id": "nyt",
        "title": "📚 Libros NYT",
        "text": "\n".join(lines),
        "items": items,
        "fetched": int(time.time()),
        "v": VERSION,
    }
