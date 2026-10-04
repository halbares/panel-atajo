import time

import requests

WANTED = {
    "combined-print-and-e-book-fiction": "Ficción",
    "combined-print-and-e-book-nonfiction": "No ficción",
}
TOP = 5
CACHE_SECONDS = 12 * 3600


def fetch(api_key, prev=None):
    # La lista cambia una vez por semana: reutiliza la sección previa si es reciente.
    if prev and time.time() - prev.get("fetched", 0) < CACHE_SECONDS:
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
            lines.append(f"{b['rank']}. {title} · {b['author']}")
            items.append({"title": f"{title} ({b['author']})", "url": b.get("amazon_product_url") or ""})
    return {
        "id": "nyt",
        "title": "📚 Libros NYT",
        "text": "\n".join(lines),
        "items": items,
        "fetched": int(time.time()),
    }
