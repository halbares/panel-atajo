# panel-atajo

Backend para el Botón de Acción del iPhone. Una GitHub Action genera cada 30 min `data.json`
(cripto, libros NYT, noticias de audición de hoy) y lo publica en GitHub Pages. Un Atajo lo lee.

- Local: `python build.py` (opcional `.env` con `NYT_API_KEY`, `GROQ_API_KEY`).
- Secrets: `NYT_API_KEY` y `GROQ_API_KEY` (Groq, cuota gratuita sin tarjeta, https://console.groq.com/keys). Sin clave, filtro por palabras clave.
- `PANEL_TODAY=YYYY-MM-DD` fuerza la fecha "hoy" para pruebas.

## Formato de `data.json`

URL: `https://halbares.github.io/panel-atajo/data.json`

```json
{"updated": "...", "sections": [{"id": "crypto", "title": "💰 Cripto", "text": "texto listo para mostrar", "items": []}]}
```

Secciones: `crypto`, `nyt`, `audicion-hw`, `audicion-bio`. Si una fuente falla, el texto lleva `⚠️ Sin actualizar`.

## Atajo de iPhone (Botón de Acción)

1. Atajos → nuevo atajo → **Obtener contenido de URL** con la URL de arriba.
2. **Obtener valor del diccionario** → clave `sections` (lista).
3. **Repetir con cada elemento** → dentro: **Obtener valor del diccionario** → `title`, y otro → `text`; únelos con **Texto** (`título` + salto + `texto`).
4. Fuera del bucle: **Combinar texto** (separador: dos saltos de línea) → **Mostrar resultado**.
5. Ajustes → Botón de Acción → **Atajo** → elige este atajo.

Para elegir sección al pulsar: reemplaza el bucle por **Elegir de la lista** sobre los `title` y filtra por el elegido.
