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
