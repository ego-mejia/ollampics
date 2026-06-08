"""Mock tool catalog for the tool_calling suite.

Each tool has:
  - name (used by the LLM)
  - description (shown to the LLM)
  - parameters: JSON Schema describing args
  - execute(args) -> dict: deterministic mock implementation

Determinism matters: the same args must always return the same result so that
verifier outcomes are reproducible.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    execute: Callable[[dict[str, Any]], dict[str, Any]]

    def ollama_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# ---- mock implementations ----

def _stable_int(seed: str, modulo: int, offset: int = 0) -> int:
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return (h % modulo) + offset


def _get_weather(args: dict[str, Any]) -> dict[str, Any]:
    city = str(args.get("city", "")).strip()
    if not city:
        return {"error": "missing city"}
    conditions = ["soleado", "nublado", "lluvioso", "despejado", "ventoso"]
    return {
        "city": city,
        "temp_c": _stable_int(city.lower(), 30, 5),
        "condition": conditions[_stable_int(city.lower(), len(conditions))],
        "humidity_pct": _stable_int(city.lower() + "h", 70, 20),
    }


def _search_web(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query", "")).strip()
    limit = int(args.get("limit", 3))
    if not query:
        return {"error": "missing query"}
    results = [
        {
            "title": f"Resultado {i + 1} sobre {query}",
            "url": f"https://example.com/{re.sub(r'[^a-z0-9]+', '-', query.lower())}/{i + 1}",
            "snippet": f"Breve descripción {i + 1} relacionada con {query}.",
        }
        for i in range(min(limit, 5))
    ]
    return {"query": query, "results": results}


def _send_email(args: dict[str, Any]) -> dict[str, Any]:
    to = args.get("to")
    subject = args.get("subject")
    body = args.get("body")
    if not all([to, subject, body]):
        return {"error": "missing required fields"}
    return {
        "sent": True,
        "message_id": hashlib.sha256(
            f"{to}|{subject}|{body}".encode()
        ).hexdigest()[:12],
        "to": to,
    }


_SAFE_EXPR = re.compile(r"^[\d\s+\-*/().%]+$")


def _calculator(args: dict[str, Any]) -> dict[str, Any]:
    expr = str(args.get("expression", "")).strip()
    if not expr:
        return {"error": "missing expression"}
    if not _SAFE_EXPR.match(expr):
        return {"error": "expression contiene caracteres no permitidos"}
    try:
        value = eval(expr, {"__builtins__": {}}, {})  # safe: regex-restricted input
    except Exception as e:
        return {"error": f"eval falló: {e}"}
    return {"expression": expr, "result": value}


_MOCK_FILES = {
    "/notes/groceries.txt": "1. tomate\n2. pan integral\n3. café\n4. lentejas",
    "/notes/todo.md": "- terminar reporte trimestral\n- llamar al banco\n- comprar regalo",
    "/projects/readme.md": "# Helion Robotics\nProyecto principal de la empresa.",
}


def _read_file(args: dict[str, Any]) -> dict[str, Any]:
    path = str(args.get("path", "")).strip()
    if not path:
        return {"error": "missing path"}
    if path not in _MOCK_FILES:
        return {"error": f"file not found: {path}"}
    return {"path": path, "content": _MOCK_FILES[path]}


def _create_calendar_event(args: dict[str, Any]) -> dict[str, Any]:
    title = args.get("title")
    date = args.get("date")
    if not title or not date:
        return {"error": "missing title or date"}
    event_id = hashlib.sha256(f"{title}|{date}".encode()).hexdigest()[:10]
    return {
        "event_id": event_id,
        "title": title,
        "date": date,
        "participants": args.get("participants", []),
    }


def _set_reminder(args: dict[str, Any]) -> dict[str, Any]:
    title = args.get("title") or args.get("text")
    when = args.get("when") or args.get("date") or args.get("datetime")
    if not title or not when:
        return {"error": "missing title or when"}
    rid = hashlib.sha256(f"{title}|{when}".encode()).hexdigest()[:10]
    return {"reminder_id": rid, "title": title, "when": when, "stored": True}


def _take_note(args: dict[str, Any]) -> dict[str, Any]:
    content = args.get("content") or args.get("text") or args.get("note")
    if not content:
        return {"error": "missing content"}
    note_id = hashlib.sha256(str(content).encode()).hexdigest()[:10]
    tags = args.get("tags", [])
    return {"note_id": note_id, "content": content, "tags": tags, "stored": True}


# ---- registry ----

CATALOG: dict[str, Tool] = {
    "get_weather": Tool(
        name="get_weather",
        description="Obtén el clima actual para una ciudad.",
        parameters={
            "type": "object",
            "required": ["city"],
            "properties": {
                "city": {"type": "string", "description": "Nombre de la ciudad."},
            },
        },
        execute=_get_weather,
    ),
    "search_web": Tool(
        name="search_web",
        description="Busca información en la web.",
        parameters={
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string", "description": "Consulta de búsqueda."},
                "limit": {"type": "integer", "description": "Máximo de resultados.", "default": 3},
            },
        },
        execute=_search_web,
    ),
    "send_email": Tool(
        name="send_email",
        description="Envía un email.",
        parameters={
            "type": "object",
            "required": ["to", "subject", "body"],
            "properties": {
                "to": {"type": "string", "description": "Email del destinatario."},
                "subject": {"type": "string", "description": "Asunto."},
                "body": {"type": "string", "description": "Cuerpo del mensaje."},
            },
        },
        execute=_send_email,
    ),
    "calculator": Tool(
        name="calculator",
        description="Evalúa una expresión aritmética. Solo +, -, *, /, %, paréntesis y números.",
        parameters={
            "type": "object",
            "required": ["expression"],
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Expresión aritmética, ej. '(2+3)*4'.",
                },
            },
        },
        execute=_calculator,
    ),
    "read_file": Tool(
        name="read_file",
        description="Lee el contenido de un archivo del sistema de notas del usuario.",
        parameters={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string", "description": "Ruta absoluta del archivo."},
            },
        },
        execute=_read_file,
    ),
    "create_calendar_event": Tool(
        name="create_calendar_event",
        description="Crea un evento en el calendario.",
        parameters={
            "type": "object",
            "required": ["title", "date"],
            "properties": {
                "title": {"type": "string", "description": "Título del evento."},
                "date": {
                    "type": "string",
                    "description": "Fecha y hora ISO 8601, ej. '2026-06-10T15:00:00'.",
                },
                "participants": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista opcional de emails.",
                },
            },
        },
        execute=_create_calendar_event,
    ),
    "set_reminder": Tool(
        name="set_reminder",
        description="Configura un recordatorio puntual para el usuario.",
        parameters={
            "type": "object",
            "required": ["title", "when"],
            "properties": {
                "title": {"type": "string", "description": "Sobre qué es el recordatorio."},
                "when": {
                    "type": "string",
                    "description": "Cuándo recordarlo. Texto natural o ISO.",
                },
            },
        },
        execute=_set_reminder,
    ),
    "take_note": Tool(
        name="take_note",
        description="Guarda una nota en el bloc del usuario, opcionalmente con tags.",
        parameters={
            "type": "object",
            "required": ["content"],
            "properties": {
                "content": {"type": "string", "description": "Contenido de la nota."},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista opcional de etiquetas.",
                },
            },
        },
        execute=_take_note,
    ),
}


def get_tools(names: list[str]) -> list[Tool]:
    out: list[Tool] = []
    for n in names:
        if n not in CATALOG:
            raise KeyError(f"tool desconocida: {n}")
        out.append(CATALOG[n])
    return out
