"""Genera public/data.json con las secciones del panel. Cada fuente falla de forma aislada."""
import datetime as dt
import json
import os
import pathlib
import shutil
from zoneinfo import ZoneInfo

import requests

from sources import crypto, hearing, nyt

OUT = pathlib.Path("public/data.json")
ORDER = ["crypto", "nyt", "audicion-hw", "audicion-bio"]


def load_env():
    env = pathlib.Path(".env")
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def load_prev():
    """Datos previos: de Pages en CI (PREV_URL) o del fichero local."""
    url = os.environ.get("PREV_URL")
    try:
        if url:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"[prev] no se pudo leer {url}: {e}")
    if OUT.exists():
        return json.loads(OUT.read_text())
    return {}


def stale(prev_section, sid, title):
    if prev_section:
        return {**prev_section, "text": "⚠️ Sin actualizar\n" + prev_section["text"].removeprefix("⚠️ Sin actualizar\n")}
    return {"id": sid, "title": title, "text": "⚠️ Sin datos todavía.", "items": []}


def main():
    load_env()
    prev = load_prev()
    prev_secs = {s["id"]: s for s in prev.get("sections", [])}
    now = dt.datetime.now(ZoneInfo("Europe/Madrid"))
    secs, state = {}, prev.get("state")

    def run(sid, title, fn):
        try:
            return fn()
        except Exception as e:
            print(f"[{sid}] ERROR: {e!r}")
            return stale(prev_secs.get(sid), sid, title)

    secs["crypto"] = run("crypto", "💰 Cripto", lambda: crypto.fetch(os.environ.get("COINGECKO_KEY")))

    nyt_key = os.environ.get("NYT_API_KEY")
    if nyt_key:
        secs["nyt"] = run("nyt", "📚 Libros NYT", lambda: nyt.fetch(nyt_key, prev_secs.get("nyt")))
    else:
        print("[nyt] sin NYT_API_KEY")
        secs["nyt"] = stale(prev_secs.get("nyt"), "nyt", "📚 Libros NYT")

    token = os.environ.get("GROQ_API_KEY")
    try:
        hw, bio, state = hearing.fetch(state, token)
        secs["audicion-hw"], secs["audicion-bio"] = hw, bio
    except Exception as e:
        print(f"[hearing] ERROR: {e!r}")
        secs["audicion-hw"] = stale(prev_secs.get("audicion-hw"), "audicion-hw", "🦻 Audición: hardware")
        secs["audicion-bio"] = stale(prev_secs.get("audicion-bio"), "audicion-bio", "🧬 Audición: biotech/cura")

    stamp = now.strftime("%H:%M")
    sections = []
    for sid in ORDER:
        s = secs[sid]
        if "⚠️" not in s["text"]:
            s["updated"] = now.isoformat(timespec="minutes")
        s["text"] += f"\n\n🕐 {stamp}" if "updated" in s and sid != "nyt" else ""
        sections.append(s)

    full = "\n\n———\n\n".join(f"{s['title']}\n{s['text']}" for s in sections)  # para el Atajo: un solo campo
    OUT.parent.mkdir(exist_ok=True)
    shutil.copy("index.html", OUT.parent / "index.html")  # dashboard estático
    OUT.write_text(json.dumps({"updated": now.isoformat(timespec="minutes"), "text": full, "sections": sections, "state": state},
                              ensure_ascii=False, indent=1))
    print(f"OK {len(sections)} secciones -> {OUT}")


if __name__ == "__main__":
    main()
