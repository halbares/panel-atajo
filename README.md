# panel-atajo

Backend para el Botón de Acción del iPhone. Una GitHub Action genera cada 30 min `data.json`
(libros NYT en español, artículos NYT de tecnología, salud y gadgets, noticias de audición de hoy) y lo publica en GitHub Pages. Un Atajo lo lee.

- Local: `python build.py` (opcional `.env` con `NYT_API_KEY`, `GROQ_API_KEY`).
- Secrets: `NYT_API_KEY` y `GROQ_API_KEY` (Groq, cuota gratuita sin tarjeta, https://console.groq.com/keys). Sin clave, filtro por palabras clave.
- `PANEL_TODAY=YYYY-MM-DD` fuerza la fecha "hoy" para pruebas.

## Formato de `data.json`

URL: `https://halbares.github.io/panel-atajo/data.json`

```json
{"updated": "...", "sections": [{"id": "crypto", "title": "💰 Cripto", "text": "texto listo para mostrar", "items": []}]}
```

Secciones: `crypto`, `nyt`, `audicion-hw`, `audicion-bio`. Si una fuente falla, el texto lleva `⚠️ Sin actualizar`.

## Dashboard y Atajo de iPhone

Dashboard (HTML estático, `index.html`, se publica junto a `data.json`): https://halbares.github.io/panel-atajo/

Atajo de 1 acción: **Abrir URL** con esa dirección. Luego Ajustes → Botón de Acción → Atajo → elegir el atajo.
