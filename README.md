# panel-atajo

Backend para el Botón de Acción del iPhone. Una GitHub Action genera cada 30 min `data.json`
(cripto, libros NYT, noticias de audición de hoy) y lo publica en GitHub Pages. Un Atajo lo lee.

- Local: `python build.py` (opcional `.env` con `NYT_API_KEY`, `OPENROUTER_API_KEY`).
- Secrets: `NYT_API_KEY` y `OPENROUTER_API_KEY` (modelos `:free`; GitHub Models se retiró en julio de 2026). Sin clave, filtro por palabras clave.
- `PANEL_TODAY=YYYY-MM-DD` fuerza la fecha "hoy" para pruebas.
