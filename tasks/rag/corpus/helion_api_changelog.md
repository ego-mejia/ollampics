# Helion API — Changelog

Todas las fechas en formato `DD mes AAAA`. Versiones semánticas (`vMAJOR.MINOR.PATCH`). Los cambios se listan por orden cronológico inverso.

---

## v3.0.0 — 15 abril 2026

### Breaking changes

- **Header de autenticación**  
  Se reemplaza el header `Authorization` (usado en versiones anteriores) por el header `X-Helion-Auth`. El formato del token permanece igual (Bearer token).  
  **Motivo**: estandarización con el ecosistema interno de microservicios de Helion.

- **Endpoint base**  
  La URL base de la API cambia de `https://api.helionrobotics.com/v2` a `https://api.helionrobotics.com/v3`.

### Añadido

- Nuevo endpoint `GET /health` que devuelve el estado del servicio y versión del API.
- Soporte para paginación en listados (`/robots`, `/fleet/list`): parámetros `page` y `per_page` (máximo 100).

### Cambiado

- Todos los endpoints existentes de `v2.x` se mantienen funcionalmente idénticos, pero requieren el nuevo header de autenticación.
- Se actualizan los códigos de error HTTP: `401 Unauthorized` ahora se usa exclusivamente para tokens faltantes o expirados; `403 Forbidden` para permisos insuficientes.

### Deprecado

- Endpoint `POST /auth/token` (migrar a `POST /v3/auth/token` con nuevo header).

### Migration

**Antes (v2.x):**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.helionrobotics.com/v2/robots
```

**Después (v3.0.0):**
```bash
curl -H "X-Helion-Auth: Bearer <token>" \
  https://api.helionrobotics.com/v3/robots
```

---

## v2.4.1 — 02 marzo 2026

### Fixed

- **Corrección en `/status`**: en modo *Eco*, el campo `last_seen` devolvía `null` cuando el robot llevaba más de 10 minutos sin comunicarse. Corregido para devolver la última marca de tiempo conocida (unix epoch en milisegundos).

---

## v2.4.0 — 10 febrero 2026

### Added

- **Nuevo endpoint `/telemetry/stream`**: flujo de datos en tiempo real mediante Server-Sent Events (SSE). Cada evento contiene un objeto JSON con los campos: `robot_id`, `timestamp`, `telemetry` (objeto con todos los sensores activos).  
  - Formato del evento:  
    ```
    event: telemetry
    data: {"robot_id":"X3-...","timestamp":...,"telemetry":{...}}
    ```
  - Recomendado para dashboards en vivo, no para almacenamiento histórico.

---

## v2.3.1 — 22 enero 2026

### Changed

- **Rate limit de `/fleet/list`**: incrementado de 60 a 240 peticiones por minuto por token. El límite anterior generaba errores `429` en flotas grandes (>50 robots). No afecta a otros endpoints.

---

## v2.3.0 — 08 enero 2026

### Deprecated

- **`/legacy/incidents`**: este endpoint deja de recibir actualizaciones. Fecha de desactivación (sunset): **01 julio 2026**.  
  - Alternativa: usar `/incidents` (disponible desde v2.0.0) con el filtro `?status=open`.  
  - Se enviará una cabecera `Deprecation: true` en todas las respuestas de `/legacy/incidents` a partir de esta versión.

---

## v2.2.0 — 14 noviembre 2025

### Added

- **Nuevo endpoint `POST /robots/{id}/firmware`**: permite iniciar una actualización de firmware de forma remota.  
  - Body requerido: `{"version": "v3.4.1"}` (debe coincidir con una versión firmada disponible en el repositorio de Helion).  
  - Respuesta inmediata con `202 Accepted` y un campo `upgrade_id`.  
  - El robot reporta progreso a través del campo `firmware` en `/status`.  

**Ejemplo:**
```bash
curl -X POST https://api.helionrobotics.com/v2/robots/X3-001/firmware \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"version": "v3.4.1"}'
```

---

## v2.1.0 — 30 septiembre 2025

### Added

- **Webhooks de incidentes**: se añade soporte para recibir notificaciones de incidentes (sobrecarga térmica, colisión, error crítico) mediante webhooks configurables.  
  - Firma HMAC-SHA256 en el header `X-Helion-Signature`.  
  - Secreto rotable cada 90 días (se recomienda rotación manual).  
  - Payload JSON con campos: `incident_type`, `robot_id`, `timestamp`, `details`.  

**Configuración vía API:**
```bash
curl -X POST https://api.helionrobotics.com/v2/webhooks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://ejemplo.com/hooks","secret":"mi-secreto","events":["thermal_overload","collision"]}'
```

---

## v2.0.0 — 01 junio 2025

### Breaking changes

- **Formato de respuesta**: todas las respuestas migraron de **XML** a **JSON**.  
  - El header `Content-Type` ahora devuelve `application/json` en lugar de `application/xml`.  
  - Los endpoints que antes devolvían XML ahora emiten JSON con la misma estructura anidada pero sin etiquetas XML.

### Añadido

- Nuevo endpoint `GET /incidents` (reemplaza a `/legacy/incidents`).
- Paginación básica (offset/limit) en `/robots` y `/fleet/list`.

### Eliminado

- Soporte para el parámetro `?format=xml` (ignorado; siempre se devuelve JSON).

### Migration

**Antes (v1.x / v2.0.0-beta):**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.helionrobotics.com/v2/robots
# Respuesta XML
```
**Después (v2.0.0):**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.helionrobotics.com/v2/robots
# Respuesta JSON
```

---

## Guía de migración v2 → v3

Si actualmente usas la API v2.x, sigue estos pasos para migrar a v3.0.0:

1. **Actualizar la URL base**  
   De `https://api.helionrobotics.com/v2/...` a `https://api.helionrobotics.com/v3/...`.

2. **Cambiar el header de autenticación**  
   Reemplazar `Authorization: Bearer <token>` por `X-Helion-Auth: Bearer <token>`.

3. **Verificar soporte de cliente**  
   Asegúrate de que tu cliente HTTP permite headers personalizados y maneja correctamente códigos `401`/`403` (ver cambios en v3.0.0).

4. **Actualizar código de ejemplo**  

   **Antes:**
   ```bash
   curl -H "Authorization: Bearer abc123" \
     https://api.helionrobotics.com/v2/robots/X3-001/status
   ```

   **Después:**
   ```bash
   curl -H "X-Helion-Auth: Bearer abc123" \
     https://api.helionrobotics.com/v3/robots/X3-001/status
   ```

5. **Validar respuesta**  
   Realiza una llamada de prueba a `GET /health` (nuevo en v3) para confirmar conectividad:

   ```bash
   curl -H "X-Helion-Auth: Bearer <token>" \
     https://api.helionrobotics.com/v3/health
   ```

6. **Rollback**  
   En caso de problemas, la versión v2.x seguirá disponible hasta **15 octubre 2026** (180 días desde el lanzamiento de v3.0.0). Se recomienda migrar antes de esa fecha.