# OLLAMPICS

**[English](README.md)** · **Español**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/) [![uv](https://img.shields.io/badge/uv-managed-purple)](https://docs.astral.sh/uv/) [![Ollama](https://img.shields.io/badge/runs%20on-Ollama-black)](https://ollama.com)

> Benchmark your local AI models like an Olympic decathlon.

OLLAMPICS corre tus modelos de Ollama a través de pruebas agénticas — tool calling, RAG, conversación multi-turno, planning, multi-agent — y te da una comparación limpia y reproducible de cómo se comporta cada modelo en tu hardware.

![Home](docs/screenshots/home.png)

## ¿Por qué existe?

Hay benchmarks académicos para LLMs grandes y cerrados, pero pocos pensados para los modelos que corres **localmente** con Ollama. Si quieres saber qué cuantización del modelo X corre mejor en tu Mac, o si el modelo Y nuevo realmente supera a tu favorito actual para *tu* caso de uso, lo tienes que correr tú. OLLAMPICS automatiza eso:

- Define tareas en YAML (o las que ya vienen).
- Dispara runs desde una UI o la CLI.
- Captura métricas reales: throughput, TTFT, VRAM, watts, success-rate.
- Guarda todo en SQLite — reproducible, sin nube, sin cuentas.

Single-machine por diseño. DeepSeek se usa **sólo como juez opcional** en pruebas RAG / planning. El resto es 100% local.

---

## Instalación

Necesitas:

- [Ollama](https://ollama.com/download) corriendo en `localhost:11434`
- Al menos un modelo descargado: `ollama pull qwen3.6:27b-mlx`
- Python 3.12+ vía [`uv`](https://docs.astral.sh/uv/) (no `pip`)
- Node 20+ (sólo si vas a tocar el frontend en dev)

```bash
git clone https://github.com/<your-fork>/ollampics
cd ollampics

# Backend
uv sync                       # crea .venv e instala todo
uv run oly db init            # crea data/ollampics.db

# Frontend (sólo la primera vez)
cd frontend && npm install && cd ..
```

### Variables de entorno (opcionales)

Copia `.env.example` a `.env` y ajusta si necesitas:

- `LLM_API_KEY` — sólo si vas a correr suites RAG / planning (usan DeepSeek como juez).
- `OLLYMPICS_OLLAMA_HOST` — si Ollama no está en `http://localhost:11434`.
- `OLLYMPICS_ENABLE_WATTS=true` — captura potencia GPU vía `powermetrics` (macOS, requiere sudo).

---

## Cómo usar la app

Dos terminales, dos servidores:

```bash
# Terminal 1 — backend en http://localhost:8000
uv run oly serve --port 8000 --reload

# Terminal 2 — frontend en http://localhost:5173
cd frontend && npm run dev
```

Abre `http://localhost:5173`. El frontend de Vite proxea `/api/*` al backend automáticamente.

### 1 · Home — qué hace cada pieza

La página de inicio explica visualmente qué es OLLAMPICS, cómo usarlo en 3 pasos, qué suites están disponibles, y qué significa cada métrica (tps, ttft, vram, watts, success_rate).

### 2 · Lanzar una corrida

Ve a **Launcher**: marca los modelos descubiertos en Ollama, las suites que quieres correr, define `num_ctx` y `kv_cache`. Lanza.

![Launcher](docs/screenshots/launcher.png)

### 3 · Ver progreso en vivo

El **Dashboard** lista runs recientes con status badges. Cada run abre una página de detalle con WebSocket: ves cada attempt al momento, con TTFT, TPS y verdict. Desde aquí también puedes borrar corridas viejas.

![Dashboard](docs/screenshots/dashboard.png)

### 4 · Comparar modelos en el Leaderboard

El **Leaderboard** agrega los mejores attempts por `(modelo, runtime, suite)` y los rankea. Los 3 primeros lugares aparecen con medallas 🥇 🥈 🥉. Filtros por suite, modelo y cuantización.

![Leaderboard](docs/screenshots/leaderboard.png)

### 5 · Tests y corpus

La página **Tests** muestra las suites disponibles, con tasks individuales y (para RAG) el corpus + los prompts que generaron ese corpus.

![Tests](docs/screenshots/tests.png)

### Modo CLI (sin frontend)

```bash
uv run oly models list                                # lista modelos en Ollama
uv run oly suites                                     # lista suites disponibles
uv run oly run --models qwen3.6:27b-mlx --suites baseline
uv run oly results show                               # último run
uv run oly sweep --models X,Y --num-ctx 2048,4096 --kv-cache f16,q8_0 --suites baseline
```

---

## Suites incluidas

| Suite | Qué mide |
|---|---|
| **Baseline** | Sanity check: generación corta, JSON, factual recall, instruction following, formato de lista. |
| **Tool Calling** | 6 tools mockeadas, 8 tasks cubriendo single call, secuencias, recuperación de errores y ambigüedad. |
| **RAG** | 50 Q&A sobre un corpus ficticio (Helion Robotics) en 3 tiers: single-doc, multi-doc, out-of-corpus. |
| **Planning** | Cada tarea corre en modo 4a (plan propio) y 4b (plan dado) — aísla "planear" de "ejecutar". |
| **Personal Agent** | Conversación de 20 turnos con tool calls intermedias y recall probes. Mide memoria de contexto. |
| **Multi-agent** | Workflow Researcher → Critic → Writer vía LangGraph. Mide la calidad del reporte sintetizado. |

Detalles técnicos por suite en [docs/PHASES.md](docs/PHASES.md).

---

## Correr en Docker

> El container **no incluye Ollama**. Ollama debe correr en el host (especialmente en Mac, donde necesita acceso directo al GPU). El container apunta a `host.docker.internal:11434`.

```bash
docker compose up --build
# luego abre http://localhost:8000
```

En Linux, descomenta `extra_hosts` en `docker-compose.yml` para que `host.docker.internal` resuelva al host. La métrica de `watts` (powermetrics) no funciona dentro del container — se desactiva automáticamente; el resto de métricas queda intacto.

---

## Métricas capturadas

Por cada attempt:

| Métrica | Cómo se captura |
|---|---|
| `ttft_ms` | Wall-clock al primer token del stream |
| `tps_decode` | `eval_count / (eval_duration / 1e9)` del response de Ollama |
| `tokens_in`, `tokens_out` | `prompt_eval_count`, `eval_count` |
| `peak_vram_mb` | Polling de `ollama ps` cada 250ms |
| `avg_watts` | Sampler de `powermetrics` (opt-in, requiere sudo en macOS) |
| `success` | Booleano del verifier de la task |
| `n_tries_used` | Cuántos intentos hicieron falta |

---

## Contribuir

Si te interesa el proyecto, hay varias formas de ayudar:

- **Quick start de contribuidor**: [CONTRIBUTING.md](CONTRIBUTING.md) (convenciones, dónde están las cosas, cómo agregar tasks / suites / verifiers).
- **Roadmap detallado**: [docs/ROADMAP.md](docs/ROADMAP.md) — items dimensionados con pre-conditions, files a tocar y acceptance criteria. Listo para que un LLM agente tome cualquier item completo.
- **Help wanted (visión grande)**: [docs/HELP_WANTED.md](docs/HELP_WANTED.md) — las direcciones que más me importan: fingerprint de hardware, builder visual de agentes tipo N8N, mejores gráficas y observabilidad, subir tests desde la UI.
- **Diseño del sistema**: [docs/blueprint.html](docs/blueprint.html) — fuente de verdad del diseño original.
- **Historial técnico**: [docs/PHASES.md](docs/PHASES.md) — qué se construyó en cada fase, con resultados de smoke tests reales.

Abre un issue antes de empezar para no duplicar trabajo.

---

## Stack

- Python 3.12 + uv · FastAPI · SQLAlchemy 2 · SQLite · Pydantic v2 · Typer + Rich · httpx async · LangGraph · LangChain-OpenAI.
- React 18 + Vite + TypeScript · Tailwind + tailwind-styled-components · react-i18next · Recharts · React Router.

---

## Licencia

[MIT](LICENSE) © 2026 Fernando Mejía Laguna
