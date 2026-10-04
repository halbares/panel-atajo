# panel-atajo

Backend para el Botón de Acción del iPhone. Una GitHub Action genera cada 30 min `data.json`
(cripto, libros NYT, noticias de audición de hoy) y lo publica en GitHub Pages. Un Atajo lo lee.

- Local: `python build.py` (opcional `.env` con `NYT_API_KEY`, `GITHUB_MODELS_TOKEN`).
- Secret necesario: `NYT_API_KEY`. El LLM (GitHub Models) usa el `GITHUB_TOKEN` del workflow.
- `PANEL_TODAY=YYYY-MM-DD` fuerza la fecha "hoy" para pruebas.
