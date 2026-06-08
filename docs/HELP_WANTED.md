# Help wanted — the open-source wishlist

Estas son las direcciones que me importan más y para las que pido ayuda de la
comunidad. Si te interesa una de estas, abre un issue antes de empezar para
que no dupliquemos esfuerzo. El [ROADMAP](ROADMAP.md) tiene tasks más
granulares y ya dimensionadas — esto es la lista de "norte estratégico".

---

## 1 · Hardware fingerprint en cada corrida

**Por qué**: hoy las métricas (tps, ttft, vram) sólo tienen sentido en mi
máquina. La idea grande es que en el futuro haya un sitio público donde la
gente suba sus benchmarks y se pueda filtrar por hardware — "muéstrame el
mejor modelo de 7B en M2 Max 32GB".

**Qué hace falta**:
- Detectar y persistir en la DB: chip / GPU, RAM total, VRAM total, OS,
  versión de Ollama, número de cores.
- Nueva tabla `hardware_profiles` con FK desde `runs`.
- Captura automática al lanzar un run (sin requerir input del usuario).
- En el Leaderboard, un filtro por hardware fingerprint.
- Un endpoint `GET /api/runs/{id}/export` que incluya este metadata —
  esto desbloquea un futuro "upload your bench" public site.

**Stretch**: estandarizar el schema para que un sitio público de "shared
benchmarks" pueda agregar datos de muchos contribuyentes.

---

## 2 · Crear / subir tests desde la UI

**Por qué**: hoy hay que `vim tasks/<suite>/*.yaml`. Es el gap más grande
para contribuyentes no-Python.

**Qué hace falta**:
- Formulario en TestDetail con campos: task_id, descripción, prompt,
  verifier (regex / exact_match / json_schema), max_tries.
- Endpoint `POST /api/tests/{suite}/tasks` que valide con Pydantic y
  escriba el YAML en disco.
- Botón "subir YAML" como alternativa para usuarios avanzados.
- Validación: rechazar collision de `task_id`, validar suites con loaders
  custom (rag, planning) — esas tienen shape distinto.

Detalles técnicos completos en [ROADMAP item #2](ROADMAP.md).

---

## 3 · Builder visual de agentes (N8N-style)

**Por qué**: las suites más interesantes (planning, multi-agent, personal
agent) son grafos de LangGraph. Si la gente pudiera diseñar agentes
conectando cajas, OLLAMPICS deja de ser "harness de benchmarks" y empieza
a ser "playground para diseñar y comparar topologías de agentes".

**Qué hace falta** (ambicioso, varias fases):
- UI tipo flow editor (React Flow es la opción obvia) — nodos =
  Researcher / Critic / Writer / ToolCall / Branch / Merge; aristas =
  flujo de datos.
- Serializar el grafo a un YAML que un loader pueda convertir a un
  `StateGraph` de LangGraph.
- Soportar "ejecutar este grafo como un task" → mismo pipeline de
  verifiers que las suites estáticas.
- Library / templates de grafos comunes (research, debate, planning).

Este item es el más grande. Puede partirse en (3a) ejecutor de grafos
desde YAML, (3b) editor visual, (3c) marketplace de grafos.

---

## 4 · Mejores gráficas, observabilidad y análisis profundo

**Por qué**: las gráficas actuales son útiles pero superficiales. Hay
mucha más información oculta en los attempts (tool traces, retrieved
chunks, reasoning steps) que no estamos mostrando.

**Qué hace falta**:
- **Trazas de attempts**: para tool_calling y multi-agent, render
  cronológico de cada step (qué se llamó, qué retornó, cuánto tardó).
- **Análisis cruzado**: cuando re-corres la misma combinación
  (modelo + runtime + suite), mostrar trend lines de success_rate
  y latencia a través del tiempo.
- **Distribuciones**: hoy mostramos promedios. Agregar percentiles
  (p50, p95, p99) para tps y ttft — los promedios mienten cuando hay
  cola larga.
- **Heatmaps**: matriz tarea × modelo coloreada por éxito; expone
  rápidamente qué tareas son universalmente difíciles vs específicas
  de un modelo.
- **OpenTelemetry hooks**: emitir spans desde el runner para que la
  gente pueda enchufar Tempo / Jaeger / Honeycomb si quiere.
- **Bundle de export**: descargar un run completo (attempts +
  transcripts + hardware) en un único `.tar.gz` reproducible.

---

## 5 · Ideas que rondan (no priorizadas)

- **Vision suite** cuando los VLMs locales sean first-class en Ollama.
- **Suite de código** (dado bug + tests, producir fix).
- **Multilingual coherence** (mismo task en N idiomas, verificar
  consistencia).
- **Streaming chunks UI** — ver el modelo "pensando" en RunDetail en vez
  de sólo el resultado final.
- **Cancel + pause** parciales de runs largos (sólo cancel está en
  roadmap; pause es harder).

---

Si quieres tomar uno: abre un issue describiendo tu approach antes de
codear. Soy más útil revisando un PR pequeño y bien delimitado que uno
gigante que toca media app.
