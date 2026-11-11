"""Structures de données du pipeline d'ingestion."""

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class BlockKind(StrEnum):
    HEADING = "heading"
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"


@dataclass(frozen=True)
class Block:
    """Un élément du document, dans l'ordre de lecture, tel que le parser l'a extrait."""

    kind: BlockKind
    text: str
    page: int
    caption: str | None = None


class ChunkType(StrEnum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"


@dataclass
class Chunk:
    """Un morceau de document prêt à être indexé."""

    content: str
    content_type: ChunkType
    page_start: int
    page_end: int
    section: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    @property
    def n_words(self) -> int:
        return len(self.content.split())
