"""Découpage des blocs en chunks.

Règles :
- un chunk ne mélange jamais deux sections : un nouveau titre ferme le chunk en cours ;
- le texte est regroupé jusqu'à `max_words` ; au-delà, on coupe en gardant `overlap_words`
  mots de chevauchement pour ne pas perdre le contexte à la frontière ;
- un paragraphe trop long est découpé par phrases ;
- un tableau forme son propre chunk ; s'il est trop grand, il est découpé par lignes en
  répétant l'en-tête, pour que chaque morceau reste lisible seul.

La taille est mesurée en mots : c'est une approximation des tokens (environ 1,3 à 1,6 token par
mot en français), suffisante pour décider des coupures.
"""

import re
from dataclasses import dataclass

from doc_assistant.ingestion.models import Block, BlockKind, Chunk, ChunkType

_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+")


@dataclass(frozen=True)
class ChunkingConfig:
    max_words: int = 250
    overlap_words: int = 40
    max_table_words: int = 500

    def __post_init__(self) -> None:
        if not 0 <= self.overlap_words < self.max_words:
            raise ValueError("overlap_words doit être compris entre 0 et max_words")


def _split_long_text(text: str, max_words: int) -> list[str]:
    """Découpe un paragraphe trop long en morceaux de phrases entières (si possible)."""
    pieces: list[str] = []
    current: list[str] = []
    for sentence in _SENTENCE_END.split(text):
        words = sentence.split()
        # Une « phrase » plus longue que la limite (liste, énumération) est coupée net.
        while len(words) > max_words:
            if current:
                pieces.append(" ".join(current))
                current = []
            pieces.append(" ".join(words[:max_words]))
            words = words[max_words:]
        if len(current) + len(words) > max_words and current:
            pieces.append(" ".join(current))
            current = []
        current.extend(words)
    if current:
        pieces.append(" ".join(current))
    return pieces


def _split_table(markdown: str, max_words: int) -> list[str]:
    """Découpe un tableau Markdown par lignes en répétant l'en-tête dans chaque morceau."""
    lines = [line for line in markdown.splitlines() if line.strip()]
    if len(markdown.split()) <= max_words or len(lines) <= 3:
        return [markdown]
    header, rows = lines[:2], lines[2:]
    header_words = len(" ".join(header).split())
    parts: list[str] = []
    current: list[str] = []
    size = header_words
    for row in rows:
        row_words = len(row.split())
        if current and size + row_words > max_words:
            parts.append("\n".join(header + current))
            current, size = [], header_words
        current.append(row)
        size += row_words
    if current:
        parts.append("\n".join(header + current))
    return parts


class _TextBuffer:
    def __init__(self) -> None:
        self.words: list[str] = []
        self.new_words = 0  # mots ajoutés hors chevauchement
        self.page_start: int | None = None
        self.page_end: int | None = None

    def add(self, text: str, page: int, *, overlap: bool = False) -> None:
        if self.page_start is None:
            self.page_start = page
        self.page_end = page
        words = text.split()
        self.words.extend(words)
        if not overlap:
            self.new_words += len(words)

    def is_empty(self) -> bool:
        # Un buffer qui ne contient que le chevauchement du chunk précédent ne produit rien.
        return self.new_words == 0


def chunk_blocks(blocks: list[Block], config: ChunkingConfig | None = None) -> list[Chunk]:
    cfg = config or ChunkingConfig()
    chunks: list[Chunk] = []
    section: str | None = None
    buf = _TextBuffer()

    def flush(keep_overlap: bool) -> None:
        nonlocal buf
        if buf.is_empty():
            return
        assert buf.page_start is not None and buf.page_end is not None
        chunks.append(
            Chunk(
                content=" ".join(buf.words),
                content_type=ChunkType.TEXT,
                page_start=buf.page_start,
                page_end=buf.page_end,
                section=section,
            )
        )
        tail = buf.words[-cfg.overlap_words :] if keep_overlap and cfg.overlap_words else []
        last_page = buf.page_end
        buf = _TextBuffer()
        if tail:
            buf.add(" ".join(tail), last_page, overlap=True)

    for block in blocks:
        text = block.text.strip()
        if not text:
            continue

        if block.kind is BlockKind.HEADING:
            flush(keep_overlap=False)
            section = text
            continue

        if block.kind is BlockKind.TABLE:
            flush(keep_overlap=False)
            for part in _split_table(text, cfg.max_table_words):
                title = block.caption or section
                content = f"{title}\n\n{part}" if title else part
                chunks.append(
                    Chunk(
                        content=content,
                        content_type=ChunkType.TABLE,
                        page_start=block.page,
                        page_end=block.page,
                        section=section,
                    )
                )
            continue

        if block.kind is BlockKind.FIGURE:
            # Les figures seront décrites par le modèle de vision en phase 5.
            continue

        # Morceaux limités à (max - chevauchement) pour qu'un chunk ne dépasse jamais max_words.
        for piece in _split_long_text(text, cfg.max_words - cfg.overlap_words):
            if len(buf.words) + len(piece.split()) > cfg.max_words:
                flush(keep_overlap=True)
            buf.add(piece, block.page)

    flush(keep_overlap=False)
    return chunks
