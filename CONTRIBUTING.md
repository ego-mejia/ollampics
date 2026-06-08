# Contributing to OLLAMPICS

Thanks for considering a contribution. OLLAMPICS is a benchmark harness for
local LLMs — the kind of project that gets better the more eyes are on it.
Here's how to participate.

## Quick start for contributors

```bash
git clone https://github.com/<your-fork>/ollampics
cd ollampics
uv sync                       # Python deps + venv
cd frontend && npm install    # Frontend deps
cd ..
uv run oly db init            # Create the SQLite schema
```

Run both servers in dev mode:

```bash
# Terminal 1
uv run oly serve --port 8000 --reload

# Terminal 2
cd frontend && npm run dev
```

Then open `http://localhost:5173`.

## Where to find things

| Area | Path |
|---|---|
| Backend code (FastAPI, runner, suites) | `src/ollympics/` |
| Frontend (React + Tailwind) | `frontend/src/` |
| Suite task definitions (YAML) | `tasks/<suite>/` |
| Database schema (SQLAlchemy) | `src/ollympics/db/models.py` |
| Architecture doc | `docs/blueprint.html` |
| Roadmap | `docs/ROADMAP.md` |

## Coding conventions

### Python
- Python 3.12+. Type hints obligatorios. Docstrings estilo Google donde aporten.
- `uv` para todo: `uv add <pkg>`, `uv run <cmd>`, `uv sync`. **Nunca** `pip` ni
  `python -m venv`.
- Pydantic v2 para todo schema que cruza una frontera (LLM ↔ código, YAML
  ↔ código, API ↔ frontend).
- Sin imports relativos. Usa el path completo: `from ollympics.core.x import ...`.
- Logs via Rich, no `print`.

### Frontend
- Cada componente vive en su propio directorio con dos archivos:
  ```
  ComponentName/
    index.tsx     # logic + JSX
    style.js      # tailwind-styled-components
  ```
- Tailwind + `tailwind-styled-components`. **No interpolaciones `${var}`**
  dentro de templates `tw\`...\`` — rompe en runtime.
- Todos los strings visibles van por `t('key')` con entradas en
  `src/i18n/locales/{en,es}.json`.
- Colores: usa tokens semánticos del theme (`bg-card`, `text-fg-muted`,
  `border-border-soft`) y la paleta de marca (`brand-blue`, `brand-green`,
  `brand-red`, `brand-magenta`...). No metas hex hardcoded.

### Suites & tasks
- Cada task es un YAML en `tasks/<suite>/<NN_name>.yaml`.
- Versiona la task con `version: N`. Bump al cambiar semántica del verifier.
- Para reproducibilidad: `temperature: 0`, `seed: 42` (el default está bien).

## Adding a new task to an existing suite

1. Copia un YAML existente en `tasks/<suite>/`.
2. Cambia `task_id` (formato `<suite>.<short_name>`), `description`, y el
   contenido del `prompt`.
3. Define el `verifier` (regex, exact_match, json_schema, composite, llm_judge,
   tool_trace, personal_agent).
4. (Opcional) Bump `version` si modificas un verifier existente — los attempts
   viejos quedan asociados a la version vieja, las nuevas re-corren.
5. Re-corre la suite: `uv run oly run --models <X> --suites <suite>`.

## Adding a new suite

1. Crea `src/ollympics/suites/<your_suite>/`:
   - `__init__.py`
   - `executor.py` con una función `run_<your_suite>_task(client, model, runtime, spec) -> Result`
2. (Opcional) Si tu suite necesita un loader especial (no un YAML por task),
   agrega `loader.py` y registra el case en `suites/loader.py`.
3. Si necesita un schema extra (como `RagContextSpec`), créalo en
   `schemas/<your_suite>.py` y agrégalo como campo opcional a `TaskSpec`.
4. En `core/runner.py` agrega tu `_execute_<your_suite>_task` y el dispatch en
   `execute_task`.
5. Si necesita un verifier nuevo, agrégalo al discriminated union en
   `schemas/verifier.py` y a `core/judge.py`.
6. Agrega entrada en `SUITE_META` de `api/routes/tests.py` (icono + label).
7. Agrega icono en `frontend/public/icons/<suite>.svg` y mapéalo en
   `frontend/src/components/SuiteIcon/index.tsx`.
8. Agrega traducciones en `i18n/locales/{en,es}.json` bajo `tests.suites.<name>`.
9. Escribe al menos 3–4 tasks YAML en `tasks/<your_suite>/`.

## Adding a verifier type

1. Define la clase Pydantic en `schemas/verifier.py` con
   `type: Literal["your_kind"]` y agrégala al `Verifier` union.
2. En `core/judge.py`, agrega un case en `verify()` que llame a un
   `_verify_your_kind(...)` privado.
3. Si requiere contexto externo (transcript, trace, etc.), agrega un kwarg al
   `verify()` y propágalo a través de composite.

## Running things

```bash
uv run oly --help               # CLI help
uv run oly models list          # what's installed in Ollama
uv run oly suites               # discovered suites
uv run oly run --models X --suites Y
uv run oly results show
uv run oly sweep --models X --num-ctx 2048,4096 --kv-cache f16,q8_0 --suites Y
uv run oly corpus generate      # synthetic RAG corpus via LangGraph + DeepSeek
uv run oly corpus build         # chunk + embed + persist vector store
uv run oly serve --port 8000    # FastAPI + WebSocket
```

## Tests

Backend: `uv run pytest` (note: full coverage is still being added — see
[docs/ROADMAP.md](docs/ROADMAP.md)).

Frontend type-check + build: `cd frontend && npm run build`.

## Pull requests

1. Fork → branch → commits → PR against `main`.
2. Keep PRs focused. If you're adding a suite AND fixing a UI bug, that's two
   PRs.
3. Update the README/docs if you change user-visible behavior.
4. Include before/after screenshots for UI changes.

## What I'd love help with

See [docs/ROADMAP.md](docs/ROADMAP.md) for the prioritized list. Highlights:

- Task-creation form in the UI (right now you have to edit YAML on disk).
- Run cancellation (the endpoint exists but isn't fully wired).
- Attempt detail page (transcripts are stored, just no UI yet).
- Backend pytest coverage of the runner and verifiers.
- GitHub Actions CI for lint + frontend build.
- More suite varieties (math, code repair, multilingual...).

## Code of conduct

Be kind. Assume good intent. Critique the code, not the person. If something
in this repo or in someone's PR makes you uncomfortable, open an issue or
reach out.
