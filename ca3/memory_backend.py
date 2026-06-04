from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class MemoryRecord:
    id: int
    session_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


class InMemoryMemoryBackend:
    """Tiny deterministic lexical MemoryBackend for no-model smoke tests."""

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    def write(
        self,
        session_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            id=len(self._records),
            session_id=session_id,
            text=text,
            metadata=dict(metadata or {}),
        )
        self._records.append(record)
        return record

    def retrieve(self, query: str, top_k: int = 3) -> list[MemoryRecord]:
        query_tokens = tokenize(query)
        scored: list[tuple[int, int, MemoryRecord]] = []
        for record in self._records:
            overlap = len(query_tokens & tokenize(record.text))
            if overlap > 0:
                scored.append((-overlap, record.id, record))
        scored.sort(key=lambda item: (item[0], item[1]))
        return [record for _, _, record in scored[:top_k]]
