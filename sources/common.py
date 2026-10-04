"""Utilidades compartidas: zona horaria del usuario y fecha de 'hoy'."""
import calendar
import datetime as dt
import os
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Santiago")
EMPTY_TODAY = "Hoy no se produjeron noticias relevantes."


def today():
    forced = os.environ.get("PANEL_TODAY")  # solo para pruebas: YYYY-MM-DD
    return dt.date.fromisoformat(forced) if forced else dt.datetime.now(TZ).date()


def published(entry):
    """Fecha de publicación de una entrada RSS en la zona del usuario, o None."""
    p = entry.get("published_parsed") or entry.get("updated_parsed")
    if not p:
        return None
    return dt.datetime.fromtimestamp(calendar.timegm(p), dt.timezone.utc).astimezone(TZ)
