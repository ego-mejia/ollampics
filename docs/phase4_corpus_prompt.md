# Prompt — Generación del corpus RAG y Q&A para OLLAMPICS

> **Cómo usar este documento**: copia y pega TODO el bloque `## INSTRUCCIONES PARA LA IA` al modelo que vayas a usar (DeepSeek, GPT-4, Claude, etc.).
> El resultado son **5 archivos** que debes guardar en `tasks/rag/`:
> - `corpus/helion_manual_x3.md`
> - `corpus/helion_hr_policy.md`
> - `corpus/helion_api_changelog.md`
> - `corpus/helion_safety_protocols.md`
> - `qa.yaml`
>
> Las longitudes objetivo están elegidas para producir 8–15 chunks por
> documento al chunkear con `target_chars=2000, overlap_chars=200`.

---

## INSTRUCCIONES PARA LA IA

Eres un **escritor técnico senior y diseñador de evaluaciones de RAG**. Vas a generar un corpus ficticio coherente sobre una empresa imaginaria llamada **Helion Robotics** y, después, **50 preguntas-respuesta** estratificadas para evaluar sistemas RAG sobre ese corpus.

### Reglas duras de coherencia (CRÍTICO)

Estos hechos canónicos deben aparecer **idénticos** en TODOS los documentos donde sean relevantes. Inventa lo que falte, pero a partir de aquí no contradigas nunca:

- **Empresa**: Helion Robotics, fundada en **2019**, sede en **Querétaro, México**, CEO **Adriana Castellanos**.
- **Producto estrella**: el robot industrial **Helion-X3**, lanzado en **abril de 2024**, sucesor del Helion-X2.
- **Specs del Helion-X3** (no contradigas):
  - Peso: **45 kg**
  - Dimensiones: **1.20 m alto × 0.60 m ancho × 0.40 m fondo**
  - Carga útil: **18 kg**
  - Batería: **LiFePO₄ de 1.5 kWh, autonomía 8 horas**
  - Velocidad máx: **2.1 m/s**
  - Sensores: LiDAR Hesai XT16, IMU 9-DOF, cámara estéreo 4K, 2 sensores térmicos
  - Modos de operación: **Standard**, **Eco**, **Precision**, **Emergency**
  - Conectividad: Wi-Fi 6E, Ethernet Gigabit, opcional 5G mmWave
  - Firmware actual: **v3.4.1** (mayo 2026)
- **API pública**:
  - Versión actual: **v3.0.0**, lanzada **15 abril 2026**
  - Cambio breaking en v3.0.0: header `X-Helion-Auth` reemplaza a `Authorization`
  - Endpoint base: `https://api.helionrobotics.com/v3`
- **Protocolo de emergencia térmica**: cuando se detecta sobrecarga, el Helion-X3 entra en **modo seguro**: reduce potencia al **20%**, notifica al operador via webhook, y registra el incidente en `/var/helion/incidents/`. Si la temperatura sigue subiendo durante **30 segundos**, hace **shutdown total**.
- **RR.HH.**:
  - Vacaciones: **21 días pagados/año**, hasta **5 días** se pueden acumular al siguiente año.
  - Licencia parental: **16 semanas pagadas** (madres y padres).
  - Per diem de viaje: **USD 85/día** internacional, **MXN 1200/día** doméstico.
  - Vuelos: business class si el vuelo es **>8 horas**, premium economy si es **>4 horas**.
  - Días por enfermedad: **15 días/año**, justificante médico requerido después del **3er día consecutivo**.
- **Tono**: técnico, claro, sin marketing speech. Usa unidades del SI. Fechas en formato `DD mes AAAA` (ej. "15 abril 2026"). Versiones en formato `vMAJOR.MINOR.PATCH`.

### Documento 1 · `helion_manual_x3.md` (longitud: ~1800 palabras)

Manual técnico del Helion-X3. Secciones obligatorias (usa `#` y `##` markdown):

1. **# Helion-X3 — Manual técnico**
2. **## Resumen ejecutivo** — 1 párrafo con resumen del modelo.
3. **## Especificaciones físicas** — tabla markdown con peso, dimensiones, carga útil, batería.
4. **## Sensores y percepción** — descripción de cada sensor del listado canónico.
5. **## Modos de operación** — sub-sección por modo (Standard, Eco, Precision, Emergency). Para cada uno: cuándo usarlo, consumo energético relativo, latencia típica.
6. **## Conectividad** — Wi-Fi 6E, Ethernet, opcional 5G, requisitos de red.
7. **## Mantenimiento programado** — intervalos en horas de operación. Inventa números coherentes: cambio de filtros LiDAR cada N horas, calibración IMU cada N, lubricación de actuadores cada N.
8. **## Actualización de firmware** — pasos para actualizar (CLI `helionctl upgrade`, verificación de checksum SHA256, rollback). Menciona que v3.4.1 fue el upgrade de mayo 2026 desde v3.3.x.
9. **## Códigos de error comunes** — tabla con al menos 8 códigos (`ERR_001` a `ERR_008`) con descripción y acción correctiva.
10. **## Garantía** — duración, qué cubre, cómo escalar (referenciar a RR.HH. policy para autorización de viaje del técnico).

### Documento 2 · `helion_hr_policy.md` (longitud: ~1400 palabras)

Política interna de RR.HH. Secciones:

1. **# Helion Robotics — Política de RR.HH. (revisión enero 2026)**
2. **## Horario de trabajo** — flex schedule, core hours **10:00–15:00 CST**, 40h/semana.
3. **## Vacaciones y descanso** — usa los datos canónicos. Procedimiento de solicitud (Workday, mínimo 2 semanas de anticipación).
4. **## Licencia parental** — 16 semanas, opcional split entre padres.
5. **## Días por enfermedad** — usa datos canónicos.
6. **## Política de viajes** — per diem, clase de vuelo, política de hospedaje (máx USD 220/noche internacional). Referencia: para viajes >7 días requiere aprobación de **Directora de Operaciones, Mariana Tello**.
7. **## Beneficios** — seguro de gastos médicos mayores (MetLife México, deducible MXN 5000), vales de despensa MXN 2500/mes, fondo de ahorro 5% match.
8. **## Trabajo remoto** — política híbrida 3 días oficina / 2 días remoto. Excepciones requieren VP aprobación.
9. **## Capacitación** — presupuesto USD 1500/año/empleado para cursos y certificaciones. Reembolso contra factura.
10. **## Código de conducta** — 1 párrafo + enlace a documento separado (puedes mencionar `docs/code_of_conduct.md` inexistente).

### Documento 3 · `helion_api_changelog.md` (longitud: ~1200 palabras)

Changelog de la API pública. Estructura: una sección H2 por versión, en **orden cronológico inverso** (más nueva arriba). Versiones a incluir (inventa fechas razonables, mantén v3.0.0 = 15 abril 2026):

- **v3.0.0 (2026-04-15)** — BREAKING: header `X-Helion-Auth` reemplaza `Authorization`. Migración: ver sección dedicada.
- **v2.4.1 (2026-03-02)** — Bug fix: `/status` devolvía `null` en `last_seen` cuando el robot estaba en modo Eco.
- **v2.4.0 (2026-02-10)** — Nuevo endpoint `/telemetry/stream` (SSE).
- **v2.3.1 (2026-01-22)** — Fix: rate limit de `/fleet/list` subió de 60/min a 240/min.
- **v2.3.0 (2026-01-08)** — Deprecación: `/legacy/incidents` (sunset 2026-07-01).
- **v2.2.0 (2025-11-14)** — Nuevo `/robots/{id}/firmware` con POST para upgrade.
- **v2.1.0 (2025-09-30)** — Webhooks de incidentes (HMAC-SHA256, secret rotation cada 90 días).
- **v2.0.0 (2025-06-01)** — BREAKING: respuestas pasaron de XML a JSON.

Para cada versión incluye: fecha, lista de cambios con verbos imperativos (Added, Changed, Deprecated, Fixed, Removed), y para BREAKING una **sub-sección "Migration"** con código de ejemplo.

Al final del documento, una sección **## Guía de migración v2 → v3** con un snippet curl antes/después y nota sobre que el token sigue siendo el mismo, solo cambia el header.

### Documento 4 · `helion_safety_protocols.md` (longitud: ~1100 palabras)

Protocolos de seguridad. Secciones:

1. **# Protocolos de seguridad — Helion-X3**
2. **## Parada de emergencia** — botón físico rojo en cara trasera, botón virtual en la app, comando MQTT `helion/emergency/stop`. Acción: motores se desenergizan en **<200 ms**.
3. **## Sobrecarga térmica** — usa el protocolo canónico (modo seguro al 20%, webhook, 30s para shutdown total). Incluye umbral: motor >85°C o sensor de chassis >70°C.
4. **## Detección de proximidad humana** — el LiDAR + cámara estéreo + IMU mantienen una zona de exclusión de **1.5 m** alrededor del robot. Si una persona la cruza durante operación en modo Standard, velocidad cae a 0.3 m/s. En modo Precision, el robot se detiene completamente.
5. **## Prevención de colisiones** — algoritmo basado en VFH+, distancia de seguridad mínima 0.5 m, frenado de emergencia a <0.2 m.
6. **## Lockout/Tagout para mantenimiento** — procedimiento de 5 pasos para des-energizar antes de reparar. Mencionar que el firmware bloquea operación si detecta tag de lockout activo.
7. **## Reporte de incidentes** — cadena de escalación: operador → supervisor → director de planta → directora de operaciones **Mariana Tello**. SLA: notificar a Mariana en **<2 horas** si el incidente involucra heridos o daño material >USD 5000.
8. **## Auditoría y cumplimiento** — referencias a ISO 10218-1 (seguridad de robots industriales) e ISO 13849-1 (sistemas de control relacionados con seguridad).
9. **## Capacitación obligatoria** — toda persona que opera un Helion-X3 debe completar el curso "X3 Safety Fundamentals" (8 horas, recertificación anual).

---

## SEGUNDA TAREA · Generación de Q&A

Después de generar los 4 documentos, produce **50 preguntas-respuesta** estratificadas en exactamente **3 tiers**:

### Tier 1 · `factual_single_doc` (20 preguntas)

Preguntas con respuesta literal en una sola sección de un solo documento. Respuesta corta y verificable (1–10 palabras o un número con unidad).

Ejemplos:
- "¿Cuál es el peso del Helion-X3?" → "45 kg"
- "¿Quién es la CEO de Helion Robotics?" → "Adriana Castellanos"
- "¿En qué versión se introdujo el header X-Helion-Auth?" → "v3.0.0"
- "¿Cuál es el per diem internacional?" → "USD 85" (o "85 USD")

Distribuye las 20 entre los 4 docs (5 por doc aprox).

### Tier 2 · `multi_doc_synthesis` (20 preguntas)

Preguntas que requieren combinar información de **al menos 2 secciones** (mismo o distintos documentos). Respuesta abierta (1–3 frases).

Ejemplos:
- "Si necesito viajar a Brasil para reparar un Helion-X3 en campo, ¿qué políticas de viaje aplican y a quién debo notificar el incidente que motiva el viaje?" → combina HR (per diem internacional, business class >8h, aprobación de Mariana Tello si >7 días) y safety (escalación de incidentes a Mariana Tello).
- "Cuando un Helion-X3 detecta sobrecarga térmica, ¿qué hace el robot y qué reportes se generan?" → combina manual (modo seguro al 20%, log en /var/helion/incidents/) y safety (umbrales 85°C/70°C, escalación).
- "Una empresa usa la API v2.3.0 y quiere los webhooks de incidentes; ¿qué cambios debe hacer y qué precauciones de seguridad implica?" → API changelog (webhooks introducidos en v2.1.0, HMAC-SHA256, rotación de secret) + manual (URL del webhook se configura en `helionctl webhook set`).

Asigna a cada Q&A una rúbrica del set:
- `rag_open_synthesis_v1` (default)
- `rag_factual_match_v1` (si los key_facts son discretos)

### Tier 3 · `out_of_corpus` (10 preguntas)

Preguntas plausibles cuya respuesta **NO está** en los documentos. El modelo correcto admite no saber. Ejemplos:

- "¿Cuántas unidades de Helion-X3 se vendieron en Q1 2026?" (no está)
- "¿Cuál es el precio de lista del Helion-X3?" (no está)
- "¿Qué laboratorios externos validan los firmwares?" (no está)
- "¿Cuántos empleados tiene Helion Robotics?" (no está)

NO incluyas preguntas obviamente fuera de tema. Que suenen verosímiles para la empresa.

### Formato de salida para `qa.yaml`

YAML con una lista de objetos. Cada objeto tiene los campos:

```yaml
- qa_id: rag.factual_001       # rag.{tier_short}_{NNN} con NNN 001-099
  tier: factual_single_doc     # exactamente uno de los 3 valores
  question: "¿Cuál es el peso del Helion-X3?"
  expected_answer: "45 kg"      # null si tier=out_of_corpus
  key_facts: ["45 kg"]           # 1-5 hechos clave que la respuesta debe contener
  source_chunks: []             # déjalo vacío [] — el harness lo llena solo
  judge_rubric: null            # null para factual_single_doc; rag_open_synthesis_v1 para multi; rag_honest_refusal_v1 para oop
```

**Convenciones de qa_id**:
- factual_single_doc: `rag.factual_001` a `rag.factual_020`
- multi_doc_synthesis: `rag.multi_001` a `rag.multi_020`
- out_of_corpus: `rag.oop_001` a `rag.oop_010`

### Reglas de calidad de las Q&A

- **Sin ambigüedad lingüística**: si preguntas "¿cuánto cuesta?", específica de qué.
- **Diversidad**: cubre los 4 documentos. Cada doc debe ser fuente de al menos 3 factual_single_doc.
- **Respuesta única**: para `factual_single_doc`, asegura que solo haya UNA respuesta correcta dentro del corpus.
- **No tramposas**: las `out_of_corpus` deben sonar verosímiles, no preguntas absurdas tipo "¿qué desayuna el CEO?".
- **Lengua**: todas en **español**. La aplicación es bilingüe pero por ahora el corpus es en ES.

---

## ENTREGABLES

Cuando termines, devuelve **exactamente 5 bloques de código** en este orden y con estos encabezados:

````markdown
# === FILE: tasks/rag/corpus/helion_manual_x3.md ===
<contenido del manual>

# === FILE: tasks/rag/corpus/helion_hr_policy.md ===
<contenido de RR.HH.>

# === FILE: tasks/rag/corpus/helion_api_changelog.md ===
<contenido del changelog>

# === FILE: tasks/rag/corpus/helion_safety_protocols.md ===
<contenido de protocolos>

# === FILE: tasks/rag/qa.yaml ===
<YAML con 50 entradas>
````

No agregues meta-comentarios, ni introducción, ni explicación de cómo lo generaste. Solo los 5 bloques.

### Auto-validación antes de entregar

Antes de devolver tu respuesta, verifica internamente:

1. ¿Aparece el peso del Helion-X3 (45 kg) en `helion_manual_x3.md`? ¿Es citado correctamente en alguna Q&A de tier `factual_single_doc`?
2. ¿La política de viaje internacional menciona "USD 85" exactamente como aparece en `helion_hr_policy.md`?
3. ¿La versión v3.0.0 está marcada como BREAKING y trae sección de migración?
4. ¿El protocolo de sobrecarga térmica (modo seguro 20%, 30s para shutdown total) está idéntico en `helion_manual_x3.md` y `helion_safety_protocols.md`?
5. ¿Hay exactamente **20 + 20 + 10 = 50** entradas en `qa.yaml`?
6. ¿Ninguna pregunta de `out_of_corpus` tiene su respuesta en el corpus que generaste?

Si alguna respuesta es "no", **corrige antes de entregar**.
