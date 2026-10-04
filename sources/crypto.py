import requests

COINS = [("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL"), ("the-open-network", "TON"), ("ripple", "XRP")]


def _fmt(n):
    if n >= 100:
        return f"{n:,.0f}".replace(",", ".")
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fetch(key=None):
    headers = {"x-cg-demo-api-key": key} if key else {}
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": ",".join(c for c, _ in COINS),
            "vs_currencies": "eur,usd",
            "include_24hr_change": "true",
        },
        headers=headers,
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    lines = []
    for cid, sym in COINS:
        d = data[cid]
        ch = d["eur_24h_change"]
        arrow = "▲" if ch >= 0 else "▼"
        lines.append(f"{sym}  {_fmt(d['eur'])} €  ·  {_fmt(d['usd'])} $  {arrow} {ch:+.1f}%")
    return {"id": "crypto", "title": "💰 Cripto", "text": "\n".join(lines), "items": []}
