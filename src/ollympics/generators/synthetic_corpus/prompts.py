"""Default prompts for the synthetic corpus agent.

These are written to `tasks/rag/prompts/*.md` on first run if missing.
The agent always reads from disk so the user (and the frontend) can edit them.
The Python constants here are the fallback when disk files are absent.
"""

from __future__ import annotations

from pathlib import Path

PROMPT_FILES: dict[str, str] = {
    "canonical_facts.md": """\
# Hechos canónicos — Helion Robotics

Estos hechos deben aparecer **idénticos** en todos los documentos que los referencien. No los contradigas.

## Empresa
- Nombre: **Helion Robotics**
- Fundación: **2019**
- Sede: **Querétaro, México**
- CEO: **Adriana Castellanos**
- Directora de Operaciones: **Mariana Tello**

## Producto: Helion-X3
- Lanzamiento: **abril de 2024**, sucesor del Helion-X2
- Peso: **45 kg**
- Dimensiones: **1.20 m alto × 0.60 m ancho × 0.40 m fondo**
- Carga útil: **18 kg**
- Batería: **LiFePO₄ 1.5 kWh, autonomía 8 horas**
- Velocidad máxima: **2.1 m/s**
- Sensores: LiDAR Hesai XT16, IMU 9-DOF, cámara estéreo 4K, 2 sensores térmicos
- Modos de operación: **Standard**, **Eco**, **Precision**, **Emergency**
- Conectividad: Wi-Fi 6E, Ethernet Gigabit, opcional 5G mmWave
- Firmware actual: **v3.4.1** (mayo 2026)

## API pública
- Versión actual: **v3.0.0** (lanzada **15 abril 2026**)
- Endpoint base: `https://api.helionrobotics.com/v3`
- Cambio breaking v3.0.0: header `X-Helion-Auth` reemplaza a `Authorization`

## Protocolo de sobrecarga térmica
- Al detectar sobrecarga, el robot entra en **modo seguro**: reduce potencia al **20%**, notifica al operador vía webhook, registra incidente en `/var/helion/incidents/`.
- Si la temperatura sigue subiendo durante **30 segundos**: **shutdown total**.
- Umbrales: motor > 85°C o chassis > 70°C.

## RR.HH.
- Vacaciones: **21 días pagados/año**, hasta **5 días** acumulables al siguiente año.
- Licencia parental: **16 semanas pagadas** (madres y padres).
- Per diem internacional: **USD 85/día**; doméstico: **MXN 1200/día**.
- Vuelos: business class si > 8 horas; premium economy si > 4 horas.
- Días por enfermedad: **15 días/año**; justificante médico después del **3er día consecutivo**.

## Estilo
- Tono técnico, claro, sin marketing speech.
- Unidades del SI.
- Fechas: `DD mes AAAA` (ej. "15 abril 2026").
- Versiones: `vMAJOR.MINOR.PATCH`.
- Idioma: **español**.
""",
    "doc_manual_x3.md": """\
# Tarea: generar `helion_manual_x3.md`

Genera un manual técnico del Helion-X3 en markdown. **Longitud objetivo: ~1800 palabras**.

## Estructura obligatoria

Usa `#` para el título y `##` para secciones. Las secciones, en orden:

1. **# Helion-X3 — Manual técnico**
2. **## Resumen ejecutivo** — 1 párrafo.
3. **## Especificaciones físicas** — incluye tabla markdown con peso, dimensiones, carga útil, batería.
4. **## Sensores y percepción** — describe cada sensor (LiDAR Hesai XT16, IMU 9-DOF, cámara estéreo 4K, 2 sensores térmicos).
5. **## Modos de operación** — sub-sección por modo (Standard, Eco, Precision, Emergency). Para cada uno: cuándo usarlo, consumo energético relativo, latencia típica.
6. **## Conectividad** — Wi-Fi 6E, Ethernet, opcional 5G, requisitos de red.
7. **## Mantenimiento programado** — intervalos en horas de operación; inventa números coherentes (filtros LiDAR cada N horas, calibración IMU cada N, lubricación cada N).
8. **## Actualización de firmware** — pasos (CLI `helionctl upgrade`, checksum SHA256, rollback). Menciona que v3.4.1 fue el upgrade de mayo 2026.
9. **## Códigos de error comunes** — tabla con al menos 8 códigos (`ERR_001` a `ERR_008`) con descripción y acción correctiva.
10. **## Garantía** — duración, qué cubre, cómo escalar.

## Salida

Responde con SOLO el contenido del documento en markdown. Sin meta-comentarios, sin código fences alrededor del markdown.
""",
    "doc_hr_policy.md": """\
# Tarea: generar `helion_hr_policy.md`

Genera la política de RR.HH. en markdown. **Longitud objetivo: ~1400 palabras**.

## Estructura obligatoria

1. **# Helion Robotics — Política de RR.HH. (revisión enero 2026)**
2. **## Horario de trabajo** — flex schedule, core hours **10:00–15:00 CST**, 40h/semana.
3. **## Vacaciones y descanso** — usa los datos canónicos. Procedimiento de solicitud (Workday, mínimo 2 semanas de anticipación).
4. **## Licencia parental** — 16 semanas, opcional split entre padres.
5. **## Días por enfermedad** — usa datos canónicos.
6. **## Política de viajes** — per diem, clase de vuelo, hospedaje (máx USD 220/noche internacional). Viajes >7 días requieren aprobación de **Mariana Tello, Directora de Operaciones**.
7. **## Beneficios** — seguro de gastos médicos mayores (MetLife México, deducible MXN 5000), vales de despensa MXN 2500/mes, fondo de ahorro 5% match.
8. **## Trabajo remoto** — híbrida 3 días oficina / 2 días remoto.
9. **## Capacitación** — presupuesto USD 1500/año/empleado para cursos.
10. **## Código de conducta** — 1 párrafo.

## Salida

Responde SOLO con el contenido del documento en markdown.
""",
    "doc_api_changelog.md": """\
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
""",
    "doc_safety_protocols.md": """\
# Tarea: generar `helion_safety_protocols.md`

Protocolos de seguridad. **Longitud objetivo: ~1100 palabras**.

## Estructura

1. **# Protocolos de seguridad — Helion-X3**
2. **## Parada de emergencia** — botón físico rojo en cara trasera, botón virtual en la app, comando MQTT `helion/emergency/stop`. Motores se desenergizan en **<200 ms**.
3. **## Sobrecarga térmica** — usa el protocolo canónico (modo seguro al 20%, webhook, 30s para shutdown total). Umbrales: motor >85°C o chassis >70°C.
4. **## Detección de proximidad humana** — zona de exclusión de **1.5 m**. En Standard: velocidad cae a 0.3 m/s. En Precision: detención completa.
5. **## Prevención de colisiones** — algoritmo VFH+, distancia mínima 0.5 m, frenado de emergencia <0.2 m.
6. **## Lockout/Tagout** — procedimiento de 5 pasos. Firmware bloquea operación si detecta tag activo.
7. **## Reporte de incidentes** — cadena: operador → supervisor → director de planta → **Mariana Tello**. SLA: notificar a Mariana en **<2 horas** si hay heridos o daño >USD 5000.
8. **## Auditoría y cumplimiento** — referencias a ISO 10218-1 y ISO 13849-1.
9. **## Capacitación obligatoria** — curso "X3 Safety Fundamentals" (8 horas, recertificación anual).

## Salida

Responde SOLO con el contenido del documento en markdown.
""",
    "qa_generation.md": """\
# Tarea: generar `qa.yaml` con 50 preguntas estratificadas

A partir de los 4 documentos del corpus (que recibirás en el mensaje), genera **exactamente 50 preguntas-respuesta** en formato YAML.

## Distribución obligatoria

- **20** preguntas `factual_single_doc` — respuesta literal en una sola sección de un solo documento. Respuesta corta (1–10 palabras o número con unidad).
- **20** preguntas `multi_doc_synthesis` — requieren combinar info de al menos 2 secciones (mismo o distintos docs).
- **10** preguntas `out_of_corpus` — preguntas plausibles cuya respuesta NO está en el corpus.

## Formato

YAML lista de objetos. Cada objeto:

```yaml
- qa_id: rag.factual_001
  tier: factual_single_doc
  question: "¿Cuál es el peso del Helion-X3?"
  expected_answer: "45 kg"
  key_facts: ["45 kg"]
  source_chunks: []
  judge_rubric: null
```

## Reglas

- `qa_id`: `rag.factual_001..020`, `rag.multi_001..020`, `rag.oop_001..010`.
- `expected_answer`: string corta. Para `out_of_corpus`: usa `null`.
- `key_facts`: 1-5 elementos, datos que la respuesta debe contener.
- `source_chunks`: déjalo `[]`.
- `judge_rubric`:
  - `factual_single_doc` → `null`
  - `multi_doc_synthesis` → `"rag_open_synthesis_v1"`
  - `out_of_corpus` → `"rag_honest_refusal_v1"`
- Idioma: español.
- Cada documento debe ser fuente de al menos 3 `factual_single_doc`.
- Las `out_of_corpus` deben sonar verosímiles (no preguntas absurdas).

## Salida

Responde SOLO con el contenido YAML. Sin meta-comentarios, sin code fences. Empieza con `- qa_id: rag.factual_001`.
""",
}


def write_default_prompts(prompts_dir: Path) -> None:
    """Writes each default prompt to disk if missing. Idempotent."""
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for name, content in PROMPT_FILES.items():
        target = prompts_dir / name
        if not target.exists():
            target.write_text(content)


def read_prompt(prompts_dir: Path, name: str) -> str:
    """Reads a prompt from disk, falling back to default if missing."""
    target = prompts_dir / name
    if target.exists():
        return target.read_text()
    if name not in PROMPT_FILES:
        raise KeyError(f"prompt desconocido: {name}")
    return PROMPT_FILES[name]
