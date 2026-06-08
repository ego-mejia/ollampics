# OLLAMPICS

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/) [![uv](https://img.shields.io/badge/uv-managed-purple)](https://docs.astral.sh/uv/) [![Ollama](https://img.shields.io/badge/runs%20on-Ollama-black)](https://ollama.com)

Benchmark harness para LLMs locales en tareas agénticas. Cada modelo compite individualmente en las mismas pruebas — Baseline, Tool Calling, RAG, Planning, Personal Agent y Multi-agent — registrando estadísticas detalladas en SQLite. Un dashboard React permite comparar modelos, cuantizaciones y configuraciones de runtime apples-to-apples.

> Nombre de marca: **OLLAMPICS**. El package Python y CLI siguen como `ollympics` y `oly` por compatibilidad interna.

## ¿Por qué existe?

Hay benchmarks académicos para modelos grandes y cerrados, pero pocos pensados para LLMs que corres localmente con Ollama. Si quieres saber qué cuantización del modelo X corre mejor en tu hardware, o si el modelo Y nuevo realmente es mejor que tu favorito actual para *tu* caso de uso, necesitas correrlos tú. OLLAMPICS automatiza eso: define tareas, dispara los runs, mide throughput / TTFT / VRAM / success-rate, y los resultados quedan a un click en el dashboard.

Single-machine, sin cloud (excepto DeepSeek como juez opcional), reproducible (temperature 0, seed fija), open source.

## Contribuir / hoja de ruta

- Quick start para contribuidores y convenciones de código: [CONTRIBUTING.md](CONTRIBUTING.md)
- Qué falta y cómo ayudar: [docs/ROADMAP.md](docs/ROADMAP.md)
- Diseño completo (la fuente de verdad): [docs/blueprint.html](docs/blueprint.html)
- Licencia: [MIT](LICENSE)

## Cómo correr la app

Necesitas **Ollama corriendo** (en `localhost:11434`) y al menos un modelo descargado (`ollama pull <name>`).

**Primera vez:**

```bash
# Backend (Python)
uv sync                       # crea .venv e instala deps
uv run oly db init            # crea data/ollympics.db

# Frontend (React)
cd frontend && npm install    # solo la primera vez
```

**Modo dev (dos terminales):**

```bash
# Terminal 1 — backend en http://localhost:8000
uv run oly serve --port 8000 --reload

# Terminal 2 — frontend en http://localhost:5173
cd frontend && npm run dev
```

Abre `http://localhost:5173` en el navegador. Vite proxea `/api/*` al backend automáticamente.

**Modo CLI (sin frontend):**

```bash
uv run oly models list                                           # lista modelos en Ollama
uv run oly suites                                                # lista suites
uv run oly run --models 'qwen3.6:27b-mlx' --suites tool_calling  # dispara bench
uv run oly results show                                          # último run
```

**Build de producción del frontend:**

```bash
cd frontend && npm run build  # outputs a frontend/dist/
```

## Estado por fases

| Fase | Entrega | Status |
|---|---|---|
| 0 | Skeleton (uv, FastAPI, React, schema SQLite, control Ollama, CLI base) | ✅ |
| 1 | Suite **Baseline** funcionando end-to-end con métricas básicas | ✅ |
| 2 | Métricas de hardware (peak VRAM via `ollama ps`, watts via `powermetrics`) | ✅ |
| 3 | Suite **Tool Calling** con verificador `tool_trace` | ✅ |
| 4 | Suite **RAG** (corpus Helion Robotics, vector store local, nomic-embed-text, juez DeepSeek) | ✅ |
| 5 | Frontend MVP: Launcher, Run detail, Leaderboard | ✅ |
| 6 | Live runs vía WebSocket + página Compare A/B | ✅ |
| 7 | Suite **Planning** 4a/4b con LangGraph | ✅ |
| 8 | Suite **Personal Agent** (20 turnos + tools + recall probes) | ✅ |
| 9 | Suite **Multi-agent** (research) con LangGraph (substitute por CrewAI) | ✅ |
| 10 | `oly sweep`: matriz automática de cuantizaciones y KV cache | ✅ |

## Quick start

```bash
# 1. Sync deps (crea .venv e instala todo desde el lockfile)
uv sync

# 2. Inicializa la DB
uv run oly db init

# 3. Verifica modelos descubiertos en Ollama
uv run oly models list

# 4. Corre la suite baseline contra un modelo
uv run oly run --models 'liquidai/lfm2.5-1.2b-instruct:q8_0' --suites baseline

# 5. Ve el resumen del último run
uv run oly results show

# 6. (Opcional) Arranca FastAPI + frontend
uv run oly serve --port 8000         # backend en :8000
cd frontend && npm install && npm run dev   # frontend en :5173
```

## Comandos CLI

```
oly models list                 Lista modelos instalados en Ollama
oly suites                      Lista suites disponibles en tasks/
oly db init                     Crea schema SQLite (idempotente)

oly run                         Dispara una corrida
  --models 'X,Y,Z'              Comma-separated. Requerido.
  --suites 'baseline,rag'       Default: baseline
  --num-ctx 8192                Tamaño de contexto
  --kv-cache f16                f16 | q8_0 | q4_0
  --notes "texto libre"         Para identificar la corrida en results

oly results list                Lista corridas recientes
oly results show [--run-id N]   Detalle de attempts (último por default)
oly serve --port 8000           Levanta FastAPI
```

## Estructura del proyecto

```
ollympics/
├── docs/blueprint.html       # diseño completo del sistema
├── pyproject.toml            # uv-managed
├── src/ollympics/
│   ├── cli.py                # Typer: `oly`
│   ├── core/
│   │   ├── config.py         # settings (pydantic-settings, lee .env)
│   │   ├── ollama.py         # cliente HTTP async para Ollama
│   │   ├── judge.py          # verificadores deterministas
│   │   └── runner.py         # orquestador principal
│   ├── schemas/              # Pydantic: task, verifier, runtime, run, result
│   ├── db/                   # SQLAlchemy ORM + sesión + repo
│   ├── suites/loader.py      # carga tasks/<suite>/*.yaml
│   └── api/                  # FastAPI app + routes
├── tasks/baseline/           # 5 tasks YAML versionadas
├── frontend/                 # React + Vite + TS + Tailwind
└── data/ollympics.db         # SQLite (ignorado por git)
```

## Cómo agregar una task

Crea un archivo YAML en `tasks/<suite>/<numero>_<nombre>.yaml`:

```yaml
task_id: baseline.mi_test
version: 1
suite: baseline
description: Una pregunta corta.
max_tries: 2
timeout_s: 60

prompt:
  system: "Sé conciso."
  user: "¿Cuánto es 2+2?"

verifier:
  type: regex
  pattern: "\\b4\\b"
```

Verificadores disponibles:

| Tipo | Campos | Uso |
|---|---|---|
| `regex` | `pattern`, `flags` | match con `re.search` |
| `exact_match` | `expected` (string o lista), `case_sensitive`, `fuzzy` | contains o fuzzy ratio ≥0.85 |
| `json_schema` | `schema` (subset: `type`, `required`, `properties`, `items`, `enum`, `pattern`) | parsea JSON y valida |
| `composite` | `all_of: [...]` o `any_of: [...]` | combinación recursiva |
| `tool_trace` | `expected_calls`, `final_message`, `allow_extra_calls`, `strict_order`, `max_format_errors` | valida secuencia de tool calls + mensaje final |
| `llm_judge` | `rubric`, `pass_threshold` | stub — pendiente Fase 4 |

La task se descubre automáticamente al siguiente `oly run`. Si modificas un verificador, **bump `version`** para que los attempts viejos no se reciclen.

## Idempotencia

Re-ejecutar el mismo bench salta tasks que ya tienen un attempt exitoso para esa combinación `(modelo, runtime, task)`. La clave única es:

```
(model.name, runtime_config.hash, task.task_id+version)
```

Cambiar cualquiera de los tres ejes genera attempts nuevos sin perder históricos.

## Métricas capturadas

Por cada attempt:

| Métrica | Captura |
|---|---|
| `ttft_ms` | Wall-clock al primer token del stream |
| `tps_decode` | `eval_count / (eval_duration / 1e9)` desde el response final de Ollama |
| `tokens_in`, `tokens_out` | `prompt_eval_count`, `eval_count` |
| `wall_time_s` | Tiempo total del attempt |
| `peak_vram_mb` | Polling de `ollama ps` cada 250ms durante el attempt *(Fase 2)* |
| `avg_watts` | Sampler de `powermetrics` opcional *(Fase 2 — requiere sudo)* |
| `success` | Booleano definido por el verificador |
| `n_tries_used` | Cuántos intentos hicieron falta |

## Fase 2: medición de hardware

Implementada en [`core/metrics.py`](src/ollympics/core/metrics.py) como async context manager:

```python
async with MetricsSampler(model_name) as sampler:
    await client.generate(...)
# sampler.peak_vram_mb, sampler.avg_watts
```

El sampler arranca dos loops paralelos al iniciar el attempt y se cierra al salir del context. La granularidad por default es 250ms (configurable vía `OLLYMPICS_SAMPLER_INTERVAL_MS`).

### VRAM peak

Sin configuración adicional. Sampler hace `GET /api/ps` cada 250ms y lee `size_vram` del modelo cargado. Resultado verificado en bench real:

```
attempt  peak_vram_mb  tps   status
14       1365          201.0 fail
15       1365          198.3 fail
16       1365          193.3 success    # liquidai/lfm2.5-1.2b-instruct:q8_0
17       1365          269.9 success    # consistencia: VRAM idéntica entre attempts
```

### Watts promedio (opcional)

Apple Silicon no expone potencia GPU sin privilegios. Para habilitar:

```bash
# Opción A: opt-in por corrida (Ollympics intenta `sudo -n powermetrics`)
OLLYMPICS_ENABLE_WATTS=1 uv run oly run --models ... --suites ...

# Opción B (recomendado): passwordless sudo SOLO para powermetrics
sudo visudo -f /etc/sudoers.d/powermetrics
# añadir:  egomejia ALL=(ALL) NOPASSWD: /usr/bin/powermetrics
```

Si `powermetrics` falla (sin sudo, comando ausente), el attempt se guarda con `avg_watts=NULL` y el resto de las métricas intactas. La captura de VRAM no se ve afectada.

### Implementación

- **Independiente del request**: el sampler vive en su propio task de asyncio, paralelo a `client.generate`. No agrega latencia al attempt medido.
- **Sin fugas de proceso**: al cerrar el context, `powermetrics` recibe `SIGTERM`, espera hasta 2s, y si no responde se `kill`-ea.
- **Tolerante a fallos**: cualquier excepción en el loop de muestreo se silencia. El attempt nunca falla por culpa del sampler.

## Fase 3: suite Tool Calling

Implementada en [`src/ollympics/suites/tool_calling/`](src/ollympics/suites/tool_calling/):

- [`catalog.py`](src/ollympics/suites/tool_calling/catalog.py): catálogo de **6 tools mockeadas** con respuestas deterministas (mismos args → mismo resultado), exportable a formato Ollama (`type: function`).
- [`executor.py`](src/ollympics/suites/tool_calling/executor.py): loop multi-turno con `OllamaClient.chat`. Itera hasta no haber tool_calls o alcanzar `max_turns`. Captura trace, `format_errors`, métricas agregadas.

### Tools disponibles

| Tool | Descripción | Mock |
|---|---|---|
| `get_weather` | Clima por ciudad | Hash determinista → temp_c, condición, humedad |
| `search_web` | Búsqueda web con `limit` opcional | 3 resultados ficticios coherentes con el query |
| `send_email` | Envía email | Confirmación + `message_id` derivado del payload |
| `calculator` | Aritmética básica (regex de seguridad) | Evalúa expresión, errores capturados |
| `read_file` | Lee de un sistema mockeado | 3 archivos disponibles: `/notes/groceries.txt`, `/notes/todo.md`, `/projects/readme.md` |
| `create_calendar_event` | Agenda evento | Devuelve `event_id` derivado del título+fecha |

### Verificador `tool_trace`

Compara la secuencia emitida contra `expected_calls`. Cada expected define `tool` (nombre) y opcionalmente `args_schema` (JSON Schema parcial con `enum`/`pattern`). Modos:

- **`strict_order: false`** (default): cada expected debe matchear *algún* actual call. Útil cuando el orden no importa.
- **`strict_order: true`**: posición exacta.
- **`allow_extra_calls`**: si `false`, calls de más → fail.
- **`final_message`**: sub-verifier (regex, exact, etc.) aplicado al mensaje final del asistente.
- **`max_format_errors`**: tolerancia a tool calls con JSON inválido o nombres desconocidos.

### Resultado del smoke test

Bench contra `qwen3.6:27b-mlx` sobre las 8 tasks de la suite:

| Task | Resultado | Insight |
|---|---|---|
| single_call_simple | ✅ | clima Tokio correcto al primer intento |
| single_call_arg_typing | ✅ | date ISO 8601 emitida correctamente |
| no_call_needed | ✅ | no llamó tools en saludo casual (no false-positive) |
| sequential_2 | ✅ | calculator → send_email encadenó bien el resultado |
| sequential_3 | ✅ | 3 tools en orden lógico |
| **error_recovery** | ❌ | reintentó 6 veces con nombres en español; nunca probó `/notes/groceries.txt`. **Limitación real capturada por el bench.** |
| parallel_independent | ✅ | llamó `get_weather` dos veces, una por ciudad |
| ambiguous_no_clarify | ✅ | pidió clarificación, no inventó destinatario |

**7/8 success**. El fallo de `error_recovery` es exactamente el tipo de señal que el bench debería producir: el modelo sí tiene capacidad de retry, pero no exploró fuera del idioma de la pregunta. Un humano probaría `ls /notes/` mentalmente; el modelo no.

## Frontend · arquitectura modular

Reescrito con **Tailwind + `tailwind-styled-components`**. Cada componente vive en su propia carpeta con dos archivos:

```
ComponentName/
  index.tsx     # lógica, props, JSX
  style.js      # styled components vía `tw\`...\``
```

Para extender un componente externo (ej. React Router `Link`) se usa `tw(Link)` directamente — la librería no soporta el prop `as` de styled-components clásico.

### Estructura

```
frontend/src/
├── components/          # primitives reutilizables
│   ├── Alert/
│   ├── Badge/           # variants: success, fail, warn, neutral, live
│   ├── Button/          # Primary, PrimaryRouterLink, IconBtn
│   ├── Card/            # Card + Stat
│   ├── LanguageToggle/  # EN ↔ ES
│   ├── Layout/          # nav bar + outlet
│   ├── Logo/            # CSS mask, hereda color del tema
│   ├── PageHeader/
│   ├── Table/           # Table, THead, TR, TH, TD primitivos
│   └── ThemeToggle/     # dark ↔ light
├── hooks/
│   └── useTheme.ts      # localStorage + prefers-color-scheme
├── i18n/
│   ├── index.ts         # react-i18next + LanguageDetector
│   └── locales/
│       ├── en.json      # default
│       └── es.json
└── pages/
    ├── Dashboard/
    │   ├── ModelsSection/
    │   └── RunsSection/
    ├── Launcher/
    │   ├── ModelsSelector/
    │   ├── SuitesSelector/
    │   └── RuntimeFields/
    ├── Leaderboard/
    │   ├── LeaderboardFilters/
    │   └── LeaderboardTable/
    └── RunDetail/
        ├── SummaryCards/
        └── AttemptsTable/
```

Cada subfolder tiene `index.tsx + style.js`. Ningún archivo supera 200 líneas.

### Temas y branding

- **Logo** en `frontend/public/logo.svg` con `fill="currentColor"`. Se renderiza vía CSS `mask` heredando el color del texto del contenedor → blanco en dark, negro en light.
- **Tokens semánticos** vía CSS variables en [`src/index.css`](frontend/src/index.css): `bg`, `card`, `elev`, `border`, `border-soft`, `fg`, `fg-muted`, `fg-dim`. Cambian con `.dark` en `<html>`.
- **Paleta de marca** (mismas en ambos temas) en [`tailwind.config.js`](frontend/tailwind.config.js): `brand.blue` (active/primary), `brand.green` (success), `brand.red` (errors), `brand.magenta` (live/pulse), `brand.yellow/sky/orange` (ranks #1/2/3 en leaderboard).
- **Estética**: editorial dark/light estilo Linear/Vercel/Stripe — surfaces continuas, hairline borders, jerarquía por peso y espacio.

### Internacionalización

- **English por default**, Spanish toggle. Idioma persiste en localStorage.
- Strings en JSON: ver `i18n/locales/{en,es}.json`.
- Para agregar idioma: añadir `locales/<lang>.json` + entrada en `LANGUAGES` array + opción en `LanguageToggle`.

### Gotchas conocidos

- **`tailwind.config.js` debe escanear `.js`**: incluir `js,jsx` en el `content` glob; si no, las clases en `style.js` no entran al bundle CSS.
- **Sin interpolación `${var}` dentro de `tw\`...\``**: rompe la generación de classNames en runtime. Si necesitas compartir clases, repítelas o extrae a un componente.

## Fase 4: Suite RAG

Pipeline completo de Retrieval-Augmented Generation con corpus ficticio,
indexado local y juez LLM. Tres componentes:

### Componentes nuevos

- [`core/embedder.py`](src/ollympics/core/embedder.py) — cliente HTTP para `nomic-embed-text` vía Ollama (768-dim).
- [`core/vector_store.py`](src/ollympics/core/vector_store.py) — store local con persistencia JSONL + cosine similarity numpy. **No usa ChromaDB**: para escala de ~50 chunks, numpy es más simple y rápido.
- [`core/judge_llm.py`](src/ollympics/core/judge_llm.py) — juez OpenAI-compatible (DeepSeek por default vía `LLM_API_KEY`). 3 rúbricas: `rag_factual_match_v1`, `rag_open_synthesis_v1`, `rag_honest_refusal_v1`. Cache en `judge_evaluations` para re-evaluaciones (no durante el run live).
- [`suites/rag/chunker.py`](src/ollympics/suites/rag/chunker.py) — splitter markdown por párrafos con overlap, tracking de sección.
- [`suites/rag/corpus.py`](src/ollympics/suites/rag/corpus.py) — `build_vector_store()` chunkea + embede + persiste.
- [`suites/rag/loader.py`](src/ollympics/suites/rag/loader.py) — convierte `qa.yaml` (50 Q&A) en 50 `TaskSpec` con verificador apropiado por tier.
- [`suites/rag/executor.py`](src/ollympics/suites/rag/executor.py) — pipeline: embed query → top-k retrieval → augment prompt → generate.

### Schemas extendidos

- [`schemas/rag.py`](src/ollympics/schemas/rag.py) — `RagContextSpec` (top_k, expected_chunks, out_of_corpus).
- [`schemas/qa.py`](src/ollympics/schemas/qa.py) — `QAEntry` (tier, question, expected_answer, key_facts, judge_rubric).
- `TaskSpec.rag: RagContextSpec | None` — runner dispatch via `if spec.rag is not None`.

### Runner extendido

- `find_llm_judges()` helper recorre el árbol del verifier.
- Verify síncrono acepta `llm_results: dict[id(verifier_node), Verdict]` para resolver nodos `llm_judge` post-evaluación async.
- `_execute_rag_task` corre el pipeline RAG, llama al juez async para tasks que requieren juicio abierto, mergea resultados.

### CLI nuevo

```
oly corpus generate [--overwrite]   Genera corpus + qa.yaml con LangGraph + LLM
oly corpus build [--force]          Chunkea, embede y persiste vectors.jsonl
oly corpus info                     Lista chunks indexados
oly corpus prompts                  Lista prompts editables
```

### Verificadores por tier

- `factual_single_doc` → `exact_match` (fuzzy) sobre `expected_answer + key_facts`
- `multi_doc_synthesis` → `llm_judge` con `rag_open_synthesis_v1`
- `out_of_corpus` → `composite` con `llm_judge` + `rag_honest_refusal_v1`

### Flujo end-to-end

```bash
# 1. Generar corpus + Q&A (una vez)
oly corpus generate

# 2. Embed + indexar (cuando cambies el corpus o por primera vez)
oly corpus build

# 3. Pull del embedder local
ollama pull nomic-embed-text

# 4. Correr el bench (50 Q&A; necesita LLM_API_KEY para tiers multi y oop)
oly run --models 'gemma4:e4b-mlx' --suites rag

# 5. Inspeccionar resultados
oly results show
```

### Métricas RAG nuevas en el transcript

Cada attempt RAG persiste en su `transcript_json`:
- `retrieved_chunks`: top-k con `id`, `doc`, `section`, `score`
- `context_used`: el contexto exacto que vio el modelo
- `retrieval_recall_at_k`: si el chunk esperado entró al contexto (solo si la Q&A declara `source_chunks`)
- `answer`: respuesta del modelo

### Resultados del smoke test

Bench real contra `gemma4:e4b-mlx` (~6B params, MLX) sobre las 50 Q&A:

| Tier | Success | Total | Tasa |
|---|---|---|---|
| `factual_single_doc` | 14 | 20 | 70% |
| `multi_doc_synthesis` | 18 | 20 | 90% (juez DeepSeek) |
| `out_of_corpus` | 10 | 10 | 100% (juez DeepSeek) |
| **Total** | **42** | **50** | **84%** |

Costo del juez DeepSeek: ~$0.02 USD por corrida completa (30 evaluaciones, modelo `deepseek-v4-flash`).

## Fase 7: Suite Planning (LangGraph)

Aísla la capacidad de **planear** de la capacidad de **ejecutar** corriendo cada
problema en dos modalidades:

- **4a (plan propio)**: el modelo recibe solo el problema, produce su propio plan paso a paso (JSON array), y luego ejecuta cada paso.
- **4b (plan dado)**: el modelo recibe el problema + un `canonical_plan` curado. Solo ejecuta. Aísla la calidad de ejecución.

Comparar 4a vs 4b sobre el mismo modelo y misma tarea revela en qué eje falla.

### Implementación

- [`schemas/planning.py`](src/ollympics/schemas/planning.py) — `PlanningSpec(mode, canonical_plan, max_steps)`.
- [`suites/planning/executor.py`](src/ollympics/suites/planning/executor.py) — **LangGraph state machine**:
  ```
  START → [plan_node si 4a] → step_node ──loop── → synthesize_node → END
  ```
  Cada nodo es un `generate` independiente; estado acumula `plan`, `step_results`, métricas (`tokens_in`, `tokens_out`, `eval_duration_ns`, `ttft_ms`).
- [`suites/planning/loader.py`](src/ollympics/suites/planning/loader.py) — cada YAML produce 2 TaskSpec (`.4a` y `.4b`) sin duplicar contenido.
- `_execute_planning_task` en `core/runner.py` reusa el patrón sync+async del RAG (verificador determinista + opcional `llm_judge`).

### Tasks definidas (6 base × 2 modos = 12 instancias)

| Task ID base | Dominio |
|---|---|
| `planning.refactor_function` | Refactor de Python con type hints y extracción de helpers |
| `planning.api_design` | Diseño de API REST con autenticación y errores |
| `planning.bug_localization` | Identificar línea con bug (precedence de operadores) |
| `planning.data_pipeline` | Agregar CSV de ventas y producir tabla markdown |
| `planning.essay_outline` | Outline jerárquico para ensayo técnico |
| `planning.research_workflow` | Sintetizar ejes de confiabilidad de un benchmark |

### Resultado del smoke test (Run #10 · gemma4:e4b-mlx)

| Mode | Success | Total |
|---|---|---|
| **4a** (plan propio) | 4 | 6 |
| **4b** (plan dado) | 6 | 6 |

Las dos tasks que fallaron en 4a (`data_pipeline`, `refactor_function`) pasaron en 4b. **Exactamente la señal que el bench debe capturar**: el modelo ejecuta bien dado un buen plan, pero su plan propio queda corto en tareas técnicas.

## Fase 8: Suite Personal Agent

Conversación scripted de 20 turnos con un modelo, midiendo:

- **recall_rate**: % de "recall probes" que el modelo contesta usando hechos plantados en turnos previos (ej. ciudad, café favorito, motivo del reminder).
- **tool_fidelity**: % de tool calls esperadas que el modelo ejecuta correctamente con args válidos.
- **ttft_drift / tps_drift**: diferencia de latencia y throughput entre los primeros y últimos turnos (mide degradación con contexto creciente).
- **closing_summary_ok**: si el resumen del turno final menciona los hitos clave.

### Setup

- **Asistente bajo prueba**: persona "Ada", maneja español, conciso (≤4 líneas), system prompt fijo.
- **Tools**: `get_weather`, `set_reminder`, `take_note`, `create_calendar_event`, `search_web`.
- **Script**: 20 turnos pre-redactados con 3 recall probes (turnos 10, 14, 19) y 5 tool turns (3, 6, 9, 13, 18) más un closing summary (turno 20).

### Implementación

- [`schemas/personal_agent.py`](src/ollympics/schemas/personal_agent.py) — `PersonalAgentSpec` con `script: list[TurnSpec]`.
- [`suites/personal_agent/executor.py`](src/ollympics/suites/personal_agent/executor.py) — loop multi-turno con tool execution + per-turn metrics + recall/fidelity tracking.
- `PersonalAgentVerifier` evalúa `min_recall_rate`, `min_tool_fidelity`, `require_closing_summary`.
- `_execute_personal_agent_task` en runner persiste todo el conversation transcript + per-turn metrics + drift en `transcript_json`.

### Tools nuevas en el catálogo

`set_reminder` y `take_note`, agregadas a [`suites/tool_calling/catalog.py`](src/ollympics/suites/tool_calling/catalog.py). Determinísticas, mismo patrón que las existentes.

### Resultado del smoke test (Run #13 · gemma4:e4b-mlx)

| Métrica | Valor |
|---|---|
| `recall_rate` | **100%** (3/3 recall probes) |
| `tool_fidelity` | **100%** (5/5 tool turns) |
| `closing_summary_ok` | **True** |
| `ttft_first → last` | 5866ms → 7949ms (drift +2.1s) |
| `tps_first → last` | 57.4 → 56.4 (estable) |
| `verdict` | PASS |

El modelo recordó perfectamente los 3 hechos plantados (ciudad Querétaro, café Coatepec, motivo del reminder) y llamó las 5 tools esperadas con args válidos. La drift de TTFT confirma el costo creciente del contexto.

## Fase 9: Suite Multi-agent (Researcher → Critic → Writer)

Workflow multi-rol implementado como **LangGraph** state machine en lugar de CrewAI.

### Decisión de stack

CrewAI 0.x pinea `rich<13.7.0` y `typer<0.9.0`, incompatibles con las versiones que usa OLLAMPICS (rich 15.x, typer 0.26.x — necesarias para `console.status`, mejoras de tablas, etc.). CrewAI 1.x está en prerelease. **Decisión: usar LangGraph custom** con el mismo patrón Researcher/Critic/Writer; capturamos el costo real del patrón multi-rol sin downgrades destructivos del stack.

Implementación:
- [`schemas/multi_agent.py`](src/ollympics/schemas/multi_agent.py) — `MultiAgentSpec(iterations, *_system overrides)`.
- [`suites/multi_agent/executor.py`](src/ollympics/suites/multi_agent/executor.py) — graph: `START → researcher → critic → writer → (loop o END)`. Si `iterations > 1`, vuelve a critic+writer para refinar.
- Estado acumula `research_notes`, `critique`, `final_report`, transcripts por rol.

### Tasks

| Task ID | Iteraciones | Dominio |
|---|---|---|
| `multi.research_short` | 1 | Benchmark reliability — Researcher hace hallazgos, Critic marca gaps, Writer integra. |
| `multi.research_deep` | 2 | Tradeoffs cuantización Q4 vs Q8 — requiere tabla comparativa y recomendaciones por uso. |
| `multi.research_contradiction` | 2 | Posturas divididas sobre benchmarks sintéticos — el crew debe reconciliar. |

## Fase 5: Frontend MVP

La app es navegable extremo a extremo en `http://localhost:5173`. Cuatro páginas conectadas vía React Router + un `Layout` con nav bar persistente:

| Ruta | Propósito |
|---|---|
| `/` (Dashboard) | Modelos descubiertos en Ollama + corridas recientes con status badges. Botón "Nueva corrida". |
| `/launcher` | Form para configurar y disparar una corrida: checkboxes de modelos y suites, `num_ctx`, KV cache, notas. Al lanzar redirige al detalle. |
| `/leaderboard` | Ranking de modelos agregado por `(model, runtime_hash, suite)`. Filtro por suite, orden por `success_rate` / `avg_tps` / `avg_ttft_ms`. Barras visuales de progreso. |
| `/runs/:id` | Detalle de un run con métricas agregadas + tabla de attempts. **Auto-poll cada 2s mientras `status==running`**, refetch ligero vía `/api/runs/{id}/status` y full refresh solo cuando algo cambia. |

### Backend nuevo en esta fase

- `GET /api/leaderboard?suite=X&metric=Y` — agregación por mejor attempt por `(model, runtime, task)`, devuelve `success_rate`, `avg_tps`, `avg_ttft_ms`, `avg_tries`, `peak_vram_mb`.
- `GET /api/runs/{id}/status` — endpoint ligero para polling (sin attempts, solo `status` + counters).

### Resultado del smoke test (UI real)

Corrida #5 disparada desde el Launcher con `lfm2.5-350m`, `num_ctx=4096`, notas "fase 5 smoke test desde UI":
- Form envió payload correctamente, run apareció en background.
- Detalle muestra 8 attempts (5 fails de las 2 tasks duras + 3 successes), VRAM=419MB, ~340 tps decode.
- Leaderboard ahora muestra el mismo modelo **dos veces** — uno por cada `runtime_hash` (`num_ctx=4096` vs `8192`) — validando que la separación por runtime funciona.

## Fase 10: `oly sweep`

CLI para barrer matrices de configuración. Cada combinación de
`(modelo, num_ctx, kv_cache)` se ejecuta como un Run independiente, lo que
permite compararlas directamente en el Leaderboard (cada combo tiene su
propio `runtime_hash`).

```bash
oly sweep \
  --models 'qwen3.6:27b-mlx,qwen3.6:35b-mlx' \
  --num-ctx '2048,4096,8192,16384' \
  --kv-cache 'f16,q8_0,q4_0' \
  --suites baseline,tool_calling \
  --notes "sweep qwen ctx vs kv"
```

Imprime el plan antes de ejecutar y un resumen al final con los IDs de
cada Run. Soporta `--dry-run` para inspeccionar la matriz sin lanzar.

**Idempotencia preserved**: tasks que ya tienen attempt exitoso con el mismo
`runtime_hash` se saltan automáticamente — el sweep solo genera trabajo
nuevo cuando se cambia alguno de los ejes.

### Resultado del smoke test (Run #15–17 · lfm2.5-1.2b · baseline)

| Run | num_ctx | Success | avg_tps | avg_ttft_ms |
|---|---|---|---|---|
| #15 | 2048 | 4/6 | 202.1 | 150 |
| #16 | 4096 | 4/6 | 201.8 | 150 |
| #17 | 8192 | 0/2 | 198.1 | 138 |

Run #17 solo muestra 2 attempts porque la idempotencia detectó que los otros tasks ya pasaron con ese `runtime_hash` en runs anteriores.

## Fase 6: Live runs (WebSocket) + Compare A/B

### WebSocket en RunDetail

El polling HTTP cada 2s se reemplazó por un **WebSocket persistente** en
`/api/runs/{id}/ws`. El runner emite eventos (`task.started`, `task.finished`,
`suite.finished`, `run.finished`, etc.) que el backend rebroadcastea a todos
los subscribers de ese run.

**Backend** ([`api/routes/ws.py`](src/ollympics/api/routes/ws.py)):
- Registry global `dict[run_id, set[WebSocket]]` con lock async.
- `make_broadcast_callback(run_id)` construye un `on_event` que enruta eventos al pub/sub.
- `POST /api/runs` crea la fila del run **sincrónicamente**, luego dispara `execute_run(..., run_id=N)` en background — así el frontend recibe el `id` antes de que arranquen los eventos.

**Frontend** ([`pages/RunDetail/index.tsx`](frontend/src/pages/RunDetail/index.tsx)):
- Abre WebSocket en el mount, debounce de 250ms para refetch full detail al recibir eventos.
- Indicador visual del estado WS (●/○/✕) cuando el run está `running`.
- Vite proxy actualizado con `ws: true` para forwardear el upgrade.

### Compare A/B

Página nueva `/compare?a=N&b=M` con summary stats + diff side-by-side.

**Backend** ([`api/routes/compare.py`](src/ollympics/api/routes/compare.py)):
- `GET /api/compare?a&b` — para cada task compartida, toma el mejor attempt de cada run y arma columnas paralelas.
- `GET /api/compare/options` — lista de runs candidatos para el picker.

**Frontend** ([`pages/Compare/`](frontend/src/pages/Compare/)):
- 4 sub-componentes modulares: `CompareSelector/`, `CompareTable/`.
- Summary cards: `both_success`, `a_only_success`, `b_only_success`, `n_shared_tasks`.
- Diff visual: porcentaje de cambio en `tps` y `ttft_ms` con verde/rojo.
- URL params `?a=&b=` permiten compartir comparaciones.

### Resultado del smoke test

`/compare?a=15&b=16` (mismo modelo `lfm2.5-1.2b`, num_ctx 2048 vs 4096):
- Ambas pasan: **4/5** tasks (factual_qa, instruction_following, json_simple, list_format)
- Solo A: 0 · Solo B: 0
- Ambas fallan: short_generation
- Deltas de tps mínimos (~1%) confirman que el num_ctx no afecta throughput a esta escala

## Stack

- **Python 3.12+** con `uv` (lockfile versionado, ver memoria del usuario)
- **FastAPI** + **SQLAlchemy 2** + **SQLite**
- **Pydantic v2** para todos los schemas que cruzan frontera LLM ↔ código
- **Typer** + **Rich** para CLI
- **React 18** + **Vite** + **TS** + **Tailwind** en frontend
- **httpx** async para Ollama
- ChromaDB / nomic-embed-text / LangGraph / CrewAI: pendientes según fase

## Próximos pasos

Avanzando por orden del blueprint. Cuando quieras saltar una fase o priorizar otra, ajustamos. Para detalles arquitectónicos de fases futuras, ver [docs/blueprint.html](docs/blueprint.html).
