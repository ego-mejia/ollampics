"""Markdown chunker: paragraph-aware with size budget + overlap.

Splits docs at blank lines, tracks the latest H1/H2 as section context, and
packs paragraphs into chunks bounded by target_chars (approx. 500 tokens).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawChunk:
    doc: str
    section: str
    chunk_index: int
    text: str

    @property
    def id(self) -> str:
        return f"{self.doc}:chunk_{self.chunk_index:02d}"


def chunk_markdown(
    path: Path,
    target_chars: int = 2000,
    overlap_chars: int = 200,
) -> list[RawChunk]:
    text = path.read_text()
    doc_name = path.stem

    # Split paragraphs preserving headings as section markers
    paragraphs: list[tuple[str, str]] = []
    current_section = "(root)"
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", block)
        if heading:
            current_section = heading.group(2).strip()
            continue
        paragraphs.append((current_section, block))

    if not paragraphs:
        return []

    chunks: list[RawChunk] = []
    buf: list[str] = []
    buf_section = paragraphs[0][0]
    buf_len = 0

    def flush() -> None:
        if not buf:
            return
        chunks.append(
            RawChunk(
                doc=doc_name,
                section=buf_section,
                chunk_index=len(chunks),
                text="\n\n".join(buf),
            )
        )

    for section, para in paragraphs:
        if buf_len + len(para) > target_chars and buf:
            flush()
            tail = "\n\n".join(buf)[-overlap_chars:] if overlap_chars > 0 else ""
            buf = [tail] if tail else []
            buf_len = len(tail)
            buf_section = section
        buf.append(para)
        buf_len += len(para)

    flush()
    return chunks
