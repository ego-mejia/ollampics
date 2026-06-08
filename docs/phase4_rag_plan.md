# Fase 4 — Suite RAG · Plan de implementación

> **Audiencia**: una IA agente que va a implementar esta fase sobre el repo
> OLLAMPICS (alias del package `ollympics`). El plan asume que las fases 0–3
> y 5 ya están implementadas y funcionando (ver `README.md` y
> `docs/blueprint.html`).
>
> **Misión**: agregar la suite **RAG** (Retrieval-Augmented Generation) al
> harness de benchmarking. Debe coexistir con las suites `baseline` y
> `tool_calling` sin romperlas.

---

## 1 · Contexto que necesitas conocer

### Lo que ya existe (no romper)

- **Backend Python** en `src/ollympics/`. Stack: FastAPI + Typer + SQLAlchemy 2 + Pydantic v2 + uv como package manager.
- **Tablas SQLite** ya creadas: `runs`, `models`, `runtime_configs`, `tasks_registry`, `attempts`, `judge_evaluations`. La tabla `judge_evaluations` está vacía pero su schema está listo.
- **Runner** en `src/ollympics/core/runner.py` con dispatch entre `_execute_generate_task` y `_execute_tool_calling_task` según si `spec.tools` está definido.
- **Sistema de verificadores** en `src/ollympics/core/judge.py` con tipos: `regex`, `exact_match`, `json_schema`, `composite`, `tool_trace`. El verificador `llm_judge` existe como schema pero está stubeado (devuelve fail con mensaje "no implementado").
- **Cliente Ollama** en `src/ollympics/core/ollama.py` con `generate`, `chat`, `warmup`, `list_models`, `ps`, `stop`. Hay que extenderlo con `embeddings`.
- **Suites** se descubren en `tasks/<suite>/*.yaml` por `src/ollympics/suites/loader.py`. Cada YAML define un `TaskSpec`. La suite RAG va a romper esta convención porque tiene 50 Q&A — usaremos un loader especial.
- **Frontend React** en `frontend/` con Tailwind + tailwind-styled-components, i18n EN/ES. La suite RAG no requiere cambios al frontend en esta fase; el frontend ya muestra runs/attempts agnóstico de suite.

### Reglas y convenciones del proyecto

- **uv siempre**: `uv add <pkg>`, `uv run <cmd>`, `uv sync`. Nunca `pip` ni `python -m venv`.
- **Pydantic v2 estricto** para schemas que cruzan frontera LLM↔código o YAML↔código.
- **Type hints obligatorios**, docstrings estilo Google donde tenga sentido.
- **Sin imports relativos**: `from ollympics.core import ...`, nunca `from ..core import ...`.
- **Versionado de tasks**: cada YAML tiene `task_id` + `version`. Subir `version` invalida resultados viejos.
- **Idempotencia del runner**: la clave única de attempt es `(model.id, runtime.hash, task.id, try_n)`. Re-correr el mismo bench salta tasks ya exitosas.
- **Determinismo**: `temperature=0, seed=42, top_p=1` por default.
- **Frontend (si necesitas tocar)**: cada componente en folder con `index.tsx` + `style.js`. Tailwind + `tailwind-styled-components`. Sin interpolación `${var}` dentro de templates `tw\`...\`` (rompe en runtime). `tailwind.config.js` ya escanea `.js`.

### Cómo verificar que algo funciona

```bash
uv sync                                         # instala deps
uv run oly db init                              # crea DB si falta
uv run oly suites                               # debería mostrar rag además de baseline, tool_calling
uv run oly run --models X --suites rag          # bench end-to-end
uv run oly results show                         # resumen del último run
uv run pytest                                   # tests (debes agregar para tu fase)
```

---

## 2 · Arquitectura de la suite RAG

### Flujo por task (Q&A)

```
                   ┌──────────────────────────────┐
                   │  qa.yaml (50 entradas)       │
                   └─────────────┬────────────────┘
                                 │  load_rag_tasks()
                                 ▼
                 ┌───────────────────────────────────┐
                 │ TaskSpec con context.rag enabled  │
                 └───────────────┬───────────────────┘
                                 │
              ┌──────────────────┼────────────────────┐
              ▼                  ▼                    ▼
        Embed query        Retrieve top-k       Build prompt:
        (nomic via         desde vector          system + context +
         Ollama embed)     store local           question
                                                       │
                                                       ▼
                                          ┌─────────────────────┐
                                          │ Modelo en evaluación │
                                          │ (vía OllamaClient)   │
                                          └──────────┬──────────┘
                                                     │
              ┌──────────────────────────────────────┴───────┐
              ▼                                              ▼
       Verificador determinista                         Juez LLM
       (regex, exact_match, json_schema)                (DeepSeek)
                                                        opt-in según task
              └──────────────────────┬───────────────────────┘
                                     ▼
                              Verdict + persist
```

### Componentes nuevos a crear

```
src/ollympics/
├── core/
│   ├── embedder.py              # Cliente nomic-embed-text via Ollama
│   ├── vector_store.py          # Vector store local (numpy + JSON persistido)
│   └── judge_llm.py             # DeepSeek async + cache en DB
└── suites/
    └── rag/
        ├── __init__.py
        ├── chunker.py           # Split markdown a chunks
        ├── loader.py            # Convierte qa.yaml a list[TaskSpec]
        ├── executor.py          # Pipeline retrieve→prompt→generate
        └── corpus.py            # Build/load del corpus + chunks

tasks/rag/
├── corpus/                      # 4 documentos markdown (los genera tu otra IA, ver phase4_corpus_prompt.md)
│   ├── helion_manual_x3.md
│   ├── helion_hr_policy.md
│   ├── helion_api_changelog.md
│   └── helion_safety_protocols.md
├── prompts/                     # Jinja2 templates (versionados)
│   ├── generate_corpus.j2
│   └── generate_qa.j2
└── qa.yaml                      # 50 Q&A estratificadas

data/
└── chroma/                      # NO usar chromadb. Usar custom vector store. (ver §5)
    └── vectors.jsonl            # Persistencia del vector store
```

### Decisión de stack para vectores

**No uses ChromaDB**. La escala es pequeña (~50 chunks por corpus), la dependencia es pesada (~200MB con onnxruntime, expat, tokenizers). Reemplaza con un store custom:

- Persistencia: archivo `data/vectors.jsonl` con un objeto por chunk
  ```json
  {"id": "helion_manual_x3:chunk_0", "doc": "helion_manual_x3", "section": "Overview", "text": "...", "embedding": [0.123, ...]}
  ```
- Búsqueda: cosine similarity con `numpy`. Para 50–200 chunks es instantáneo.
- Ventaja: cero deps nuevas (`numpy` ya está disponible vía pandas/pydantic? No — agregar `numpy` con `uv add numpy`).

### Decisión de embedder

**`nomic-embed-text` vía Ollama**. Razones: ya tenemos Ollama corriendo, modelo pequeño (~270MB), multilingüe (ES/EN), formato consistente con el resto del stack.

Endpoint: `POST http://localhost:11434/api/embeddings` con `{model: "nomic-embed-text", prompt: "..."}` → `{embedding: [...]}`.

Debes hacer `ollama pull nomic-embed-text` antes del primer run. Documéntalo en el README de la suite.

### Decisión de juez LLM

**DeepSeek API**, opt-in vía `OLLYMPICS_DEEPSEEK_API_KEY`. Cliente: `httpx` directo (no `litellm` que pesa). Endpoint: `https://api.deepseek.com/v1/chat/completions` (OpenAI-compatible). Modelo: `deepseek-chat`.

Sin API key: las tasks que requieren `llm_judge` se marcan como `fail` con `error_type="judge_unavailable"` y mensaje claro. El runner no debe colgar ni romper otras tasks por esto.

---

## 3 · Schemas nuevos (Pydantic v2)

Agregar a `src/ollympics/schemas/`:

### `schemas/rag.py` (nuevo)

```python
from __future__ import annotations
from pydantic import BaseModel, Field

class RagContextSpec(BaseModel):
    """Contexto de retrieval para una task de RAG."""
    enabled: bool = True
    top_k: int = 4
    chunk_size_tokens: int = 500       # aprox; usado solo al chunkear
    chunk_overlap_tokens: int = 50
    # IDs canónicos de chunks que la respuesta DEBERÍA usar.
    # Permite calcular retrieval_recall@k aparte del answer quality.
    expected_chunks: list[str] = Field(default_factory=list)
    # Si True, la pregunta NO tiene respuesta en el corpus (test de honestidad).
    out_of_corpus: bool = False
```

### `schemas/qa.py` (nuevo)

```python
class QAEntry(BaseModel):
    """Una entrada de qa.yaml."""
    qa_id: str                                  # ej. "rag.factual_001"
    tier: Literal[
        "factual_single_doc",
        "multi_doc_synthesis",
        "out_of_corpus",
    ]
    question: str
    expected_answer: str | None = None          # null si out_of_corpus
    key_facts: list[str] = Field(default_factory=list)
    source_chunks: list[str] = Field(default_factory=list)
    judge_rubric: str | None = None             # nombre de rúbrica para llm_judge
```

### Extender `schemas/task.py`

Agregar `rag: RagContextSpec | None = None` a `TaskSpec`:

```python
class TaskSpec(BaseModel):
    task_id: str
    version: int = 1
    suite: str
    description: str = ""
    max_tries: int = 1
    timeout_s: int = 60
    prompt: PromptSpec
    verifier: Verifier
    tools: ToolsSpec | None = None
    rag: RagContextSpec | None = None    # ← NUEVO
    metrics_focus: list[str] = Field(default_factory=list)
```

El runner dispatchará: `if spec.rag is not None: usa rag executor`.

### Extender `schemas/verifier.py`

El verificador `LLMJudgeVerifier` ya existe. Agregar campo `judge_model` opcional para override:

```python
class LLMJudgeVerifier(BaseModel):
    type: Literal["llm_judge"]
    rubric: str                         # nombre de rúbrica (ver §7)
    pass_threshold: float = 0.7
    judge_model: str = "deepseek-chat"
```

---

## 4 · Módulo `core/embedder.py`

```python
# src/ollympics/core/embedder.py
"""nomic-embed-text via Ollama. Provides embed(text) and embed_batch(texts)."""

from __future__ import annotations
import httpx
from ollympics.core.config import settings

EMBEDDER_MODEL = "nomic-embed-text"

class Embedder:
    def __init__(self, host: str | None = None, model: str = EMBEDDER_MODEL):
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.host}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            r.raise_for_status()
            return r.json()["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # Ollama no soporta batch nativamente; secuencial pero rápido
        return [await self.embed(t) for t in texts]
```

**Acceptance**: `await Embedder().embed("hello")` devuelve lista de floats de longitud 768 (dimensión de nomic-embed-text).

---

## 5 · Módulo `core/vector_store.py`

```python
# src/ollympics/core/vector_store.py
"""Local persistent vector store. JSONL on disk, numpy for similarity."""

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class Chunk:
    id: str
    doc: str
    section: str
    text: str
    embedding: list[float]

class VectorStore:
    def __init__(self, path: Path):
        self.path = path
        self._chunks: list[Chunk] = []
        self._matrix: np.ndarray | None = None
        if path.exists():
            self.load()

    def load(self) -> None:
        self._chunks = []
        with self.path.open() as f:
            for line in f:
                d = json.loads(line)
                self._chunks.append(Chunk(**d))
        self._rebuild_matrix()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as f:
            for c in self._chunks:
                f.write(json.dumps({
                    "id": c.id, "doc": c.doc, "section": c.section,
                    "text": c.text, "embedding": c.embedding,
                }) + "\n")

    def upsert(self, chunks: list[Chunk]) -> None:
        existing_ids = {c.id for c in self._chunks}
        new = [c for c in chunks if c.id not in existing_ids]
        self._chunks.extend(new)
        self._rebuild_matrix()

    def _rebuild_matrix(self) -> None:
        if not self._chunks:
            self._matrix = None
            return
        m = np.array([c.embedding for c in self._chunks], dtype=np.float32)
        # L2 normalize so cosine == dot product
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        self._matrix = m / np.maximum(norms, 1e-9)

    def search(self, query_embedding: list[float], k: int = 4) -> list[tuple[Chunk, float]]:
        if self._matrix is None or not self._chunks:
            return []
        q = np.array(query_embedding, dtype=np.float32)
        q = q / max(np.linalg.norm(q), 1e-9)
        scores = self._matrix @ q
        idx = np.argsort(-scores)[:k]
        return [(self._chunks[i], float(scores[i])) for i in idx]

    def __len__(self) -> int:
        return len(self._chunks)
```

**Acceptance**:
```python
store = VectorStore(Path("data/vectors.jsonl"))
store.upsert([Chunk("a:0", "doc_a", "intro", "hola", [0.1]*768)])
store.save()
results = store.search([0.1]*768, k=1)
assert results[0][0].id == "a:0"
```

---

## 6 · Módulo `suites/rag/chunker.py`

Chunker simple para markdown. Splittea por párrafos, agrupa hasta ~500 tokens (aprox 1 token ≈ 4 chars en español), con overlap de ~50 tokens.

```python
# src/ollympics/suites/rag/chunker.py
"""Markdown chunker: by-paragraph with size budget + overlap."""

from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

@dataclass
class RawChunk:
    doc: str           # nombre del archivo sin extensión
    section: str       # último heading H1/H2 visto
    chunk_index: int   # 0-based dentro del doc
    text: str          # contenido del chunk

    @property
    def id(self) -> str:
        return f"{self.doc}:chunk_{self.chunk_index:02d}"

def chunk_markdown(
    path: Path,
    target_chars: int = 2000,   # ~500 tokens
    overlap_chars: int = 200,   # ~50 tokens
) -> list[RawChunk]:
    text = path.read_text()
    doc_name = path.stem

    # Split en párrafos preservando headings como markers
    paragraphs: list[tuple[str, str]] = []  # (section, paragraph_text)
    current_section = "(root)"
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        h = re.match(r"^#{1,3}\s+(.+)$", block, re.MULTILINE)
        if h and block.startswith("#"):
            current_section = h.group(1).strip()
            continue
        paragraphs.append((current_section, block))

    chunks: list[RawChunk] = []
    buf: list[str] = []
    buf_section = current_section if not paragraphs else paragraphs[0][0]
    buf_len = 0

    def flush():
        if not buf:
            return
        chunks.append(RawChunk(
            doc=doc_name, section=buf_section,
            chunk_index=len(chunks),
            text="\n\n".join(buf),
        ))

    for section, para in paragraphs:
        if buf_len + len(para) > target_chars and buf:
            flush()
            # overlap: keep tail of previous chunk
            tail = "\n\n".join(buf)[-overlap_chars:]
            buf = [tail] if tail else []
            buf_len = len(tail)
            buf_section = section
        buf.append(para)
        buf_len += len(para)

    flush()
    return chunks
```

**Acceptance**: chunking de un doc de 1000 palabras produce 2–4 chunks, todos con IDs únicos del estilo `helion_manual_x3:chunk_00`.

---

## 7 · Módulo `core/judge_llm.py`

```python
# src/ollympics/core/judge_llm.py
"""DeepSeek-as-judge for open-ended RAG answers."""

from __future__ import annotations
import json
from dataclasses import dataclass
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import select
from ollympics.core.config import settings
from ollympics.db.models import JudgeEvaluation

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

@dataclass
class JudgeResult:
    score: float        # 0.0 – 1.0
    passed: bool
    rationale: str
    cost_usd: float | None
    judge_model: str

# Rúbricas como prompts. Cada rúbrica devuelve JSON {score, pass, rationale}.
RUBRICS: dict[str, str] = {
    "rag_factual_match_v1": (
        "Evalúa si la respuesta del modelo contiene los hechos clave "
        "esperados. Score=1.0 si menciona TODOS los hechos clave; "
        "0.5 si menciona al menos uno; 0.0 si ninguno."
    ),
    "rag_open_synthesis_v1": (
        "Evalúa si la respuesta combina coherentemente la información "
        "del contexto recuperado. Score alto si: (a) menciona los key_facts, "
        "(b) no contradice el contexto, (c) está bien estructurada."
    ),
    "rag_honest_refusal_v1": (
        "La pregunta NO tiene respuesta en el contexto. Score=1.0 si el "
        "modelo lo dice explícitamente ('no lo sé', 'no está en el "
        "contexto', etc.) sin inventar; 0.0 si fabricó una respuesta."
    ),
}

async def evaluate_with_judge(
    session: Session,
    attempt_id: int,
    rubric: str,
    threshold: float,
    response_text: str,
    question: str,
    key_facts: list[str],
    context_used: str,
    judge_model: str = "deepseek-chat",
) -> JudgeResult:
    """Cached: if (attempt_id, judge_model, rubric) already evaluated, return that."""
    existing = session.scalar(
        select(JudgeEvaluation).where(
            JudgeEvaluation.attempt_id == attempt_id,
            JudgeEvaluation.judge_model == judge_model,
            JudgeEvaluation.rubric_name == rubric,
        )
    )
    if existing:
        return JudgeResult(
            score=existing.score, passed=existing.pass_,
            rationale=existing.rationale or "", cost_usd=existing.cost_usd,
            judge_model=judge_model,
        )

    if not settings.deepseek_api_key:
        # Devolver fail explícito; runner mostrará error_type="judge_unavailable"
        return JudgeResult(
            score=0.0, passed=False,
            rationale="DEEPSEEK_API_KEY no configurada",
            cost_usd=0.0, judge_model=judge_model,
        )

    rubric_text = RUBRICS.get(rubric, "Evalúa la calidad de la respuesta.")
    system = (
        "Eres un juez evaluador estricto. Lees un transcript y aplicas una "
        "rúbrica. Responde SOLO con JSON: "
        '{"score": float entre 0 y 1, "pass": bool, "rationale": "string corto"}. '
        "Sin texto adicional."
    )
    user = (
        f"RUBRIC: {rubric_text}\n\n"
        f"QUESTION: {question}\n\n"
        f"KEY_FACTS_EXPECTED: {key_facts}\n\n"
        f"RETRIEVED_CONTEXT:\n{context_used[:4000]}\n\n"
        f"MODEL_ANSWER:\n{response_text}\n"
    )

    payload = {
        "model": judge_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(DEEPSEEK_URL, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    raw = data["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: extraer JSON con regex (algunos modelos meten markdown fences)
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        parsed = json.loads(m.group(0)) if m else {"score": 0.0, "pass": False, "rationale": raw[:200]}

    score = float(parsed.get("score", 0.0))
    passed = bool(parsed.get("pass", score >= threshold))
    rationale = str(parsed.get("rationale", ""))

    # Cost: DeepSeek-chat ≈ $0.27 input / $1.10 output per 1M tokens (junio 2026)
    usage = data.get("usage", {})
    cost = (
        usage.get("prompt_tokens", 0) * 0.00000027
        + usage.get("completion_tokens", 0) * 0.0000011
    )

    # Persist
    session.add(JudgeEvaluation(
        attempt_id=attempt_id,
        judge_model=judge_model,
        rubric_name=rubric,
        score=score,
        pass_=passed,
        rationale=rationale,
        cost_usd=cost,
    ))
    session.flush()

    return JudgeResult(
        score=score, passed=passed, rationale=rationale,
        cost_usd=cost, judge_model=judge_model,
    )
```

**Acceptance**:
- Sin API key, devuelve `passed=False` con razón clara, sin levantar excepción.
- Con API key, evalúa una respuesta sintética y guarda en `judge_evaluations`.
- Re-evaluar el mismo attempt+rubric usa el cache de DB (no vuelve a llamar API).

---

## 8 · Módulo `suites/rag/loader.py`

```python
# src/ollympics/suites/rag/loader.py
"""Loads tasks/rag/qa.yaml and produces a list of TaskSpec instances."""

from __future__ import annotations
from pathlib import Path
import yaml
from ollympics.core.config import settings
from ollympics.schemas.qa import QAEntry
from ollympics.schemas.rag import RagContextSpec
from ollympics.schemas.task import PromptSpec, TaskSpec
from ollympics.schemas.verifier import (
    CompositeVerifier, ExactMatchVerifier, LLMJudgeVerifier, Verifier,
)

RAG_SYSTEM_PROMPT = """\
Eres un asistente que responde usando SOLO el contexto recuperado.
Si la respuesta no está en el contexto, di explícitamente "No lo sé"
o "No está en el contexto". No inventes información.
"""

def load_rag_tasks(tasks_dir: Path | None = None) -> list[TaskSpec]:
    base = (tasks_dir or settings.tasks_dir) / "rag"
    qa_path = base / "qa.yaml"
    if not qa_path.exists():
        return []
    raw = yaml.safe_load(qa_path.read_text()) or []
    return [_qa_to_task(QAEntry(**e)) for e in raw]

def _qa_to_task(qa: QAEntry) -> TaskSpec:
    verifier = _verifier_for(qa)
    return TaskSpec(
        task_id=qa.qa_id,
        version=1,
        suite="rag",
        description=qa.question,
        max_tries=2,
        timeout_s=90,
        prompt=PromptSpec(
            system=RAG_SYSTEM_PROMPT,
            user=qa.question,    # se templatea en el executor con contexto
        ),
        verifier=verifier,
        rag=RagContextSpec(
            top_k=4,
            expected_chunks=qa.source_chunks,
            out_of_corpus=(qa.tier == "out_of_corpus"),
        ),
    )

def _verifier_for(qa: QAEntry) -> Verifier:
    if qa.tier == "factual_single_doc" and qa.expected_answer:
        return ExactMatchVerifier(
            type="exact_match",
            expected=[qa.expected_answer, *qa.key_facts[:3]],
            case_sensitive=False,
            fuzzy=True,
        )
    if qa.tier == "multi_doc_synthesis":
        return LLMJudgeVerifier(
            type="llm_judge",
            rubric=qa.judge_rubric or "rag_open_synthesis_v1",
            pass_threshold=0.7,
        )
    # out_of_corpus
    return CompositeVerifier(
        type="composite",
        all_of=[
            LLMJudgeVerifier(
                type="llm_judge",
                rubric=qa.judge_rubric or "rag_honest_refusal_v1",
                pass_threshold=0.8,
            ),
        ],
    )
```

### Modificar `suites/loader.py` para delegar

```python
# en src/ollympics/suites/loader.py, dentro de load_suite:
def load_suite(suite: str, tasks_dir: Path | None = None) -> list[TaskSpec]:
    if suite == "rag":
        from ollympics.suites.rag.loader import load_rag_tasks
        return load_rag_tasks(tasks_dir)
    # ... resto igual (glob *.yaml)
```

Y en `list_suites()`: si existe `tasks/rag/qa.yaml`, añadir "rag" al listado aunque no haya `.yaml` directos.

---

## 9 · Módulo `suites/rag/corpus.py`

```python
# src/ollympics/suites/rag/corpus.py
"""Builds the vector store from tasks/rag/corpus/*.md."""

from __future__ import annotations
from pathlib import Path
from ollympics.core.config import settings
from ollympics.core.embedder import Embedder
from ollympics.core.vector_store import Chunk, VectorStore
from ollympics.suites.rag.chunker import chunk_markdown

CORPUS_DIR_NAME = "corpus"
VECTOR_STORE_FILE = "vectors.jsonl"

def vector_store_path() -> Path:
    return Path("data") / VECTOR_STORE_FILE

def corpus_dir() -> Path:
    return settings.tasks_dir / "rag" / CORPUS_DIR_NAME

async def build_corpus(
    embedder: Embedder | None = None,
    force: bool = False,
) -> VectorStore:
    """Indexes all markdown docs in tasks/rag/corpus/. Idempotent.

    Args:
        force: re-embed everything even if vector store exists.
    """
    store = VectorStore(vector_store_path())
    if len(store) > 0 and not force:
        return store

    embedder = embedder or Embedder()
    cdir = corpus_dir()
    if not cdir.exists():
        raise FileNotFoundError(f"No existe {cdir}. Genera los 4 docs con el prompt de la otra IA.")

    new_chunks: list[Chunk] = []
    for md in sorted(cdir.glob("*.md")):
        raw_chunks = chunk_markdown(md)
        texts = [c.text for c in raw_chunks]
        embeddings = await embedder.embed_batch(texts)
        for rc, emb in zip(raw_chunks, embeddings, strict=True):
            new_chunks.append(Chunk(
                id=rc.id, doc=rc.doc, section=rc.section,
                text=rc.text, embedding=emb,
            ))

    if force:
        store = VectorStore(vector_store_path())  # empty
    store.upsert(new_chunks)
    store.save()
    return store
```

---

## 10 · Módulo `suites/rag/executor.py`

Pipeline: embed query → retrieve → build augmented prompt → call modelo → return result + metadata.

```python
# src/ollympics/suites/rag/executor.py
"""RAG pipeline executor. Used by core/runner.py for tasks with spec.rag."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any
from ollympics.core.embedder import Embedder
from ollympics.core.ollama import OllamaClient
from ollympics.core.vector_store import Chunk, VectorStore
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.schemas.task import TaskSpec
from ollympics.suites.rag.corpus import vector_store_path

RAG_USER_TEMPLATE = """\
Contexto recuperado:
---
{context}
---

Pregunta: {question}
"""

@dataclass
class RagResult:
    answer: str
    retrieved_chunks: list[dict]      # {id, doc, section, text, score}
    context_used: str
    retrieval_recall_at_k: float | None
    ttft_ms: int | None
    wall_time_s: float
    tokens_in: int | None
    tokens_out: int | None
    tps_decode: float | None
    error: str | None = None
    raw_ollama_final: dict[str, Any] = field(default_factory=dict)

async def run_rag_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> RagResult:
    assert spec.rag is not None
    start = time.monotonic()

    store = VectorStore(vector_store_path())
    if len(store) == 0:
        return RagResult(
            answer="", retrieved_chunks=[], context_used="",
            retrieval_recall_at_k=None, ttft_ms=None,
            wall_time_s=time.monotonic() - start,
            tokens_in=None, tokens_out=None, tps_decode=None,
            error="vector store vacío. Corre `oly corpus build`.",
        )

    embedder = Embedder()
    q_emb = await embedder.embed(spec.prompt.user)
    hits = store.search(q_emb, k=spec.rag.top_k)

    chunks_data = [
        {"id": c.id, "doc": c.doc, "section": c.section, "text": c.text, "score": score}
        for c, score in hits
    ]
    context = "\n\n---\n\n".join(f"[{c['id']}] {c['text']}" for c in chunks_data)
    user_prompt = RAG_USER_TEMPLATE.format(
        context=context, question=spec.prompt.user
    )

    gen = await client.generate(
        model=model_name,
        prompt=user_prompt,
        system=spec.prompt.system,
        options=runtime.ollama_options(),
        timeout_s=spec.timeout_s,
    )

    expected = set(spec.rag.expected_chunks)
    if expected:
        retrieved = {c["id"] for c in chunks_data}
        recall = len(expected & retrieved) / len(expected)
    else:
        recall = None

    return RagResult(
        answer=gen.text,
        retrieved_chunks=chunks_data,
        context_used=context,
        retrieval_recall_at_k=recall,
        ttft_ms=gen.ttft_ms,
        wall_time_s=gen.wall_time_s,
        tokens_in=gen.tokens_in,
        tokens_out=gen.tokens_out,
        tps_decode=gen.tps_decode,
        raw_ollama_final=gen.raw_final,
    )
```

---

## 11 · Modificar `core/runner.py`

Agregar dispatch y manejo de LLM judge **async** después del verify síncrono:

```python
# en _execute_rag_task (nuevo método análogo a _execute_tool_calling_task)
# y agregar al dispatch en execute_task:

async def execute_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> AttemptResult:
    if spec.tools is not None:
        return await _execute_tool_calling_task(client, model_name, runtime, spec)
    if spec.rag is not None:
        return await _execute_rag_task(client, model_name, runtime, spec)
    return await _execute_generate_task(client, model_name, runtime, spec)
```

El `_execute_rag_task` debe:
1. Llamar `run_rag_task(...)` con metric sampler activo (igual que en tool_calling).
2. Construir transcript con: prompt, retrieved_chunks, context_used, answer, retrieval_recall@k.
3. Ejecutar `verify(...)` síncrono primero (cubre regex/exact/json_schema/composite que no involucran llm_judge).
4. Detectar si el verifier tree contiene algún `LLMJudgeVerifier` (helper `find_llm_judges(verifier) -> list[LLMJudgeVerifier]`).
5. Si hay LLM judges Y la respuesta ya tiene contenido: llamar `evaluate_with_judge(...)` async, mergear resultados con AND.
6. Persistir attempt + judge_evaluations.

### Helper `find_llm_judges`

```python
# en core/judge.py
def find_llm_judges(verifier: Verifier) -> list[LLMJudgeVerifier]:
    from ollympics.schemas.verifier import CompositeVerifier, LLMJudgeVerifier
    if isinstance(verifier, LLMJudgeVerifier):
        return [verifier]
    if isinstance(verifier, CompositeVerifier):
        out = []
        for sub in (verifier.all_of or []) + (verifier.any_of or []):
            out.extend(find_llm_judges(sub))
        return out
    return []
```

### Cómo mergear sync + async verdicts

Estrategia: el sync verifier devuelve `pass=True` automáticamente para los `LLMJudgeVerifier` (los trata como placeholder); el async judge los evalúa después; merge final es AND. Para implementarlo, agrega un parámetro opcional `llm_results: dict[int, Verdict]` a `verify()` y, si `id(verifier) in llm_results`, devuelve ese veredicto en lugar del stub.

---

## 12 · CLI nuevos comandos

Agregar a `src/ollympics/cli.py`:

```python
corpus_app = typer.Typer(no_args_is_help=True, help="RAG corpus management")
app.add_typer(corpus_app, name="corpus")

@corpus_app.command("build")
def corpus_build(force: bool = typer.Option(False, "--force")):
    """Chunkea los 4 docs, embede con nomic-embed-text, persiste vectors.jsonl."""
    import asyncio
    from ollympics.suites.rag.corpus import build_corpus
    store = asyncio.run(build_corpus(force=force))
    console.print(f"[green]✓[/green] Vector store: [cyan]{len(store)}[/cyan] chunks")

@corpus_app.command("info")
def corpus_info():
    """Muestra qué docs/chunks hay indexados."""
    from ollympics.core.vector_store import VectorStore
    from ollympics.suites.rag.corpus import vector_store_path
    store = VectorStore(vector_store_path())
    table = Table(title="Vector store")
    table.add_column("Chunk ID"); table.add_column("Doc"); table.add_column("Sección")
    for c in store._chunks[:50]:
        table.add_row(c.id, c.doc, c.section)
    console.print(table)
```

---

## 13 · Plan de implementación por sub-fases

Implementa en este orden, marcando cada sub-fase como completa solo después de su acceptance test:

| Sub-fase | Entrega | Acceptance |
|---|---|---|
| **4.1** | `core/embedder.py` + `core/vector_store.py` + chunker | Test unitario: chunk un doc tipo, store + search devuelve el chunk correcto |
| **4.2** | Schemas `rag.py`, `qa.py`, extensión `task.py` | `uv run python -c "from ollympics.schemas.rag import RagContextSpec; ..."` ok |
| **4.3** | `suites/rag/loader.py` + extensión a `suites/loader.py` | `uv run oly suites` muestra "rag" cuando hay `tasks/rag/qa.yaml` |
| **4.4** | `suites/rag/corpus.py` + CLI `oly corpus build/info` | Después de generar los 4 docs (ver §15), `oly corpus build` produce `data/vectors.jsonl` con ~30-60 chunks. `oly corpus info` los lista. |
| **4.5** | `suites/rag/executor.py` + dispatch en runner | `uv run oly run --models <X> --suites rag` corre las 20 factual tasks y persiste attempts con `retrieval_recall_at_k` en transcript |
| **4.6** | `core/judge_llm.py` + integración async en runner | Sin API key: tasks de tier multi/oop fallan con error_type=`judge_unavailable`. Con API key: pasan a `judge_evaluations` y son success/fail real. |
| **4.7** | README update + smoke test final | Sección "Fase 4" en README con comando de pull del embedder, resultados de un run real |

---

## 14 · Acceptance criteria globales

Un PR de Fase 4 completo debe satisfacer:

- [ ] `uv sync` instala sin errores. Nuevas deps: `numpy`. Nada más.
- [ ] Las suites `baseline` y `tool_calling` siguen funcionando idénticas (no regresión).
- [ ] `uv run oly suites` muestra `rag` cuando existe `tasks/rag/qa.yaml`.
- [ ] `uv run oly corpus build` construye el vector store de los 4 docs sin error.
- [ ] `uv run oly run --models <fast> --suites rag` corre las 50 tasks. Las 20 factual no requieren API key. Las 30 abiertas se marcan como `judge_unavailable` sin API key o como `success/fail` reales con API key.
- [ ] El campo `retrieval_recall_at_k` aparece en el transcript JSON de los attempts donde había `expected_chunks`.
- [ ] La tabla `judge_evaluations` se popula correctamente con `score`, `pass`, `rationale`, `cost_usd`.
- [ ] Re-correr el mismo bench con `oly run` salta tasks ya exitosas (idempotencia).
- [ ] Re-evaluar el mismo attempt con el juez no llama DeepSeek dos veces (cache).
- [ ] El frontend muestra los runs RAG en la lista (no requiere cambios; ya es agnóstico).

---

## 15 · Dependencia externa: el corpus

Este plan **asume** que en `tasks/rag/corpus/` ya existen los 4 documentos:

- `helion_manual_x3.md`
- `helion_hr_policy.md`
- `helion_api_changelog.md`
- `helion_safety_protocols.md`

Y en `tasks/rag/qa.yaml` la lista de 50 Q&A.

Estos archivos los genera otra IA usando el prompt en `docs/phase4_corpus_prompt.md`. **No los inventes tú.** Si no existen, fallar con error claro y pedir al usuario que los genere antes.

---

## 16 · Gotchas y notas

- **nomic-embed-text** debe instalarse antes con `ollama pull nomic-embed-text`. Documéntalo en README + en el mensaje de error si la primera llamada a `/api/embeddings` falla con 404.
- **DeepSeek API** es OpenAI-compatible pero a veces ignora `response_format: json_object`. Por eso el fallback regex para extraer JSON del mensaje.
- **Cost guard**: el juez puede gastar dólares. Considera un cap de `OLLYMPICS_JUDGE_BUDGET_USD` (default $1.0) que detenga el uso del juez si se excede. No bloqueante para esta fase pero anota TODO.
- **Idempotencia**: el helper `already_succeeded(model_id, runtime_id, task_id)` ya existe en `db/repo.py`. Úsalo en el loop de la suite RAG igual que las otras suites.
- **Test data**: incluye un mini-fixture de 1 chunk + 1 query embedded para testing offline.

---

## 17 · Estado final esperado del repo

```
src/ollympics/
├── core/
│   ├── embedder.py            ← NUEVO
│   ├── judge_llm.py           ← NUEVO
│   ├── vector_store.py        ← NUEVO
│   └── judge.py               ← extendido con find_llm_judges + soporte llm_results
├── schemas/
│   ├── qa.py                  ← NUEVO
│   ├── rag.py                 ← NUEVO
│   └── task.py                ← extendido con .rag
└── suites/
    ├── loader.py              ← extendido para delegar 'rag'
    └── rag/                   ← NUEVO
        ├── __init__.py
        ├── chunker.py
        ├── corpus.py
        ├── executor.py
        └── loader.py

tasks/rag/
├── corpus/                    ← GENERADO POR OTRA IA
│   ├── helion_manual_x3.md
│   ├── helion_hr_policy.md
│   ├── helion_api_changelog.md
│   └── helion_safety_protocols.md
├── prompts/
│   ├── generate_corpus.j2     ← Jinja2 del prompt de corpus (referencia)
│   └── generate_qa.j2
└── qa.yaml                    ← GENERADO POR OTRA IA, 50 entradas

data/
└── vectors.jsonl              ← GENERADO POR `oly corpus build`

docs/
├── blueprint.html             ← (ya existe)
├── phase4_rag_plan.md         ← este archivo
└── phase4_corpus_prompt.md    ← prompt para la otra IA
```
