# OLLAMPICS Roadmap

Status of features and what's still on the table. Each item is sized
roughly (S = a few hours, M = a day, L = several days) and tagged with
the area it touches. When you pick one up, open an issue first so we
don't duplicate work.

> **For agents implementing items**: each section below is structured so it
> can be handed to an LLM coding agent verbatim. Pre-conditions, files
> to touch, schemas to extend, and acceptance criteria are spelled out.

---

## Done

Everything from the original blueprint (Phases 0–10) is implemented. See
[blueprint.html](blueprint.html) and the corresponding "Fase N" sections
in [../README.md](../README.md).

---

## Open items

### 1 · Delete runs from the UI · DONE (this turn)

Implemented in `DELETE /api/runs/{id}` (cascade deletes attempts +
judge_evaluations) plus a trash icon on the Dashboard runs row and
RunDetail page. See `src/ollympics/api/routes/runs.py` and
`frontend/src/components/Button/style.js` (the Danger variant).

### 2 · Add tasks to a suite via the UI · S–M

**Why**: today contributors must `vim tasks/<suite>/*.yaml` and restart.
That's the single biggest UX gap for non-Python contributors.

**Pre-conditions**: Suite must already exist on disk. We are NOT exposing
"create a new suite" via UI — that requires new Python (executor + schema)
which the UI can't write.

**Files to touch**:
- `src/ollympics/api/routes/tests.py` — add `POST /api/tests/{suite}/tasks`
- `src/ollympics/schemas/task_input.py` — new `TaskInputSpec` matching what
  the form sends (subset of TaskSpec for safety)
- `frontend/src/pages/TestDetail/AddTaskForm/` — new modular component
  - `index.tsx` with form state
  - `style.js` with form fields styling
- `frontend/src/i18n/locales/{en,es}.json` — strings under `tests.addTask.*`

**API contract**:
```
POST /api/tests/{suite}/tasks
Body (JSON):
{
  "task_id": "baseline.my_new_task",   // must not collide
  "version": 1,
  "description": "...",
  "max_tries": 2,
  "timeout_s": 60,
  "prompt": { "system": "...", "user": "..." },
  "verifier": { "type": "regex", "pattern": "...", "flags": "i" }
}
Response: 201 with the written file path, or 409 if task_id collides.
```

Server-side validation:
- task_id must start with `<suite>.`
- Coerce input through Pydantic before serializing to YAML
- Refuse if `tasks/<suite>/<task_id>.yaml` already exists
- Refuse for suites with custom loaders (`rag`, `planning`) since those
  expect different YAML shapes

**Frontend UX**:
- "+ Add task" button on TestDetail header (only for non-RAG, non-planning suites)
- Modal or inline form with: task_id, description, max_tries, timeout_s,
  system prompt, user prompt, and a verifier picker
- Verifier picker initially supports `regex`, `exact_match`, `json_schema`
  (start with regex; the other two as iterations)
- On submit: POST, refetch suite detail, show toast

**Acceptance**:
- A user with no terminal access can create and run a new baseline task
  end-to-end (add task in UI → see it in detail page → run from Launcher).
- File appears on disk at the expected path.
- Re-loading the page shows the task picked up automatically.

### 3 · Cancel a running run · M

**Why**: today there's no graceful stop. If you launched a 50-Q&A RAG
run by accident, you wait it out.

**Files**:
- `src/ollympics/core/runner.py` — `execute_run` already checks
  `run.cancel_requested` between tasks but the field isn't persisted.
  Add a `cancel_requested: bool` column to the `runs` table, plumb it
  through the loop checks.
- `src/ollympics/db/models.py` — add column (and migration).
- `src/ollympics/api/routes/runs.py` — `POST /api/runs/{id}/cancel` sets
  the flag. Returns 202 immediately.
- `frontend/src/pages/RunDetail/` — "Cancel" button when status==running.

**Acceptance**: cancelling stops at the next task boundary (NOT mid-task,
that's harder). Run status becomes "cancelled". Attempts already
completed are kept.

### 4 · Attempt detail page · S

**Why**: transcripts are gold for debugging (especially RAG and tool
calling), but currently you have to query `GET /api/attempts/:id` via
curl to see them.

**Files**:
- `frontend/src/pages/AttemptDetail/index.tsx` + subfolders
- `frontend/src/main.tsx` — register `/attempts/:id` route
- Make each row in `RunDetail/AttemptsTable` a Link to the new page

**Layout**:
- Header: model, task, status, key metrics
- Tabs: "Prompt", "Response", "Tool calls" (if any), "Retrieval" (RAG
  only), "Verdict"
- For tool_trace: render the sequence visually
- For RAG: render retrieved chunks with score badges

**Acceptance**: any attempt is one click away from full transcript;
no curl needed.

### 5 · Pull models from the UI · S

**Why**: `oly models pull X` works, but UI users don't know about it.

**Files**:
- `frontend/src/pages/Dashboard/ModelsSection/` — "+ Pull model" button next
  to "Models in Ollama" title
- Modal with model-name input, hits `POST /api/models/pull` (already exists)
- WebSocket or polling for pull progress (Ollama streams it)

**Acceptance**: zero-terminal new-user can pull `qwen3.6:27b-mlx` and see
it in the model list when done.

### 6 · Backend pytest coverage · M–L

**Why**: today there's effectively zero tests of the harness itself. A
regression in the verifier or runner is invisible until smoke-test time.

**Targets** (in priority order):
1. `core/judge.py` verifiers — table-driven tests for each verifier type
   with known inputs/outputs.
2. `core/runner.py` — mock the OllamaClient and verify dispatch,
   idempotency (`already_succeeded` skip), attempt persistence.
3. `suites/*/loader.py` — load every existing YAML and validate it parses.
4. `core/embedder.py` + `core/vector_store.py` — round-trip save/load,
   cosine search returns the right chunk.
5. `core/judge_llm.py` — with mocked DeepSeek responses.

**Files**: create `tests/` with subdirs mirroring `src/ollympics/`.
`uv add --dev pytest pytest-asyncio respx` for HTTP mocking.

**Acceptance**: `uv run pytest` runs in < 30s and covers ≥ 60% of
`src/ollympics/core/` and `suites/*/loader.py`. CI runs it on every PR.

### 7 · GitHub Actions CI · S

**Why**: catches lint + build regressions before merge.

**File**: `.github/workflows/ci.yml`

```yaml
name: ci
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check src/
      - run: uv run pytest    # once item #6 lands
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build
```

**Acceptance**: PRs get a green/red check before review.

### 8 · React error boundary · S

**Why**: if any page crashes, user sees a white screen with no recovery.

**Files**: `frontend/src/components/ErrorBoundary/`. Wrap `<Routes>` in
main.tsx.

**Acceptance**: a thrown error in any page shows a friendly card with
"Reload" and a copy-able error summary, not a blank page.

### 9 · Code-split the JS bundle · S

**Why**: bundle is 684KB / 210KB gzipped, mostly Recharts. First load
on slow connections is sluggish.

**Approach**: dynamic imports for Recharts in chart components.
`React.lazy(() => import("./LeaderboardChart"))` etc.

**Acceptance**: initial JS chunk < 250KB gzipped.

### 10 · Better mobile layout · M

Most pages assume >900px. Tables overflow on phones. Nav menu needs
hamburger.

### 11 · Export run as CSV/JSON · S

**Files**: `GET /api/runs/{id}/export?format=csv` and a "Download"
button on RunDetail.

### 12 · Run tagging / search · M

Free-text search box on Dashboard. Backend: filter `notes` LIKE.
Optional: tags field.

### 13 · Time-series / trend view · M–L

When you re-run the same combo (same model + runtime + suite) over
time, show a sparkline of success_rate / tps over runs. Requires a new
view query.

### 14 · OpenAPI docs from UI · trivial

Link from footer or Home: "API docs → /docs".

### 15 · Streaming run events log · M

Today live updates re-fetch the full run on each WebSocket event.
Show an inline event log ticker on RunDetail when `status==running`.

### 16 · Auth / multi-user · L

Today: zero auth. Fine for `localhost`. If anyone wants to host this
shared, add at minimum a single shared password and CSRF on POSTs.

### 17 · More suites · L

- Math (GSM8K-style reasoning)
- Code repair (given bug + tests, produce fix)
- Multilingual (same task in N languages, check coherence)
- Vision (when local VLMs become first-class in Ollama)

---

## Non-goals (for the foreseeable future)

- **Distributed runs**: OLLAMPICS is single-machine by design. Each
  bench captures a specific hardware/model combination.
- **Training / fine-tuning**: out of scope. We measure, we don't tune.
- **Cloud hosting**: stay local. Cloud models are second-class citizens
  (DeepSeek is allowed only as judge).
