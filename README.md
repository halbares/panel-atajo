# panel-atajo

Backend para el Botón de Acción del iPhone. Una GitHub Action genera cada 30 min `data.json`
(cripto, libros NYT, noticias de audición de hoy) y lo publica en GitHub Pages. Un Atajo lo lee.

- Local: `python build.py` (opcional `.env` con `NYT_API_KEY`, `GROQ_API_KEY`).
- Secrets: `NYT_API_KEY` y `GROQ_API_KEY` (Groq, cuota gratuita sin tarjeta, https://console.groq.com/keys). Sin clave, filtro por palabras clave.
- `PANEL_TODAY=YYYY-MM-DD` fuerza la fecha "hoy" para pruebas.
