# Tarea: generar `helion_api_changelog.md`

Changelog de la API pública. **Longitud objetivo: ~1200 palabras**.

## Estructura

Una sección H2 por versión, en **orden cronológico inverso**.

## Versiones a incluir

- **v3.0.0 (2026-04-15)** — BREAKING: header `X-Helion-Auth` reemplaza `Authorization`.
- **v2.4.1 (2026-03-02)** — Bug fix: `/status` devolvía `null` en `last_seen` en modo Eco.
- **v2.4.0 (2026-02-10)** — Nuevo endpoint `/telemetry/stream` (SSE).
- **v2.3.1 (2026-01-22)** — Rate limit de `/fleet/list` subió de 60/min a 240/min.
- **v2.3.0 (2026-01-08)** — Deprecación: `/legacy/incidents` (sunset 2026-07-01).
- **v2.2.0 (2025-11-14)** — Nuevo `/robots/{id}/firmware` para upgrade.
- **v2.1.0 (2025-09-30)** — Webhooks de incidentes (HMAC-SHA256, rotación cada 90 días).
- **v2.0.0 (2025-06-01)** — BREAKING: respuestas pasaron de XML a JSON.

Por versión: fecha, lista de cambios con verbos imperativos (Added, Changed, Deprecated, Fixed, Removed). Para BREAKING incluye sub-sección **"Migration"** con código curl antes/después.

Al final, sección **## Guía de migración v2 → v3** con snippet curl.

## Salida

Responde SOLO con el contenido del documento en markdown.
