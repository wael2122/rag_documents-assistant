"""Orchestration de l'ingestion : PDF -> blocs -> chunks -> embeddings -> base."""

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

import psycopg

from doc_assistant import db
from doc_assistant.ingestion.chunker import ChunkingConfig, chunk_blocks
from doc_assistant.ingestion.embedder import Embedder
from doc_assistant.ingestion.models import Block, Chunk
from doc_assistant.ingestion.parser import load_or_convert, to_blocks

logger = logging.getLogger(__name__)

_FILENAME = re.compile(r"^(?P<company>[a-z0-9-]+)_(?P<year>\d{4})_urd$")


@dataclass(frozen=True)
class DocumentInfo:
    company: str | None
    fiscal_year: int | None


def parse_filename(path: Path) -> DocumentInfo:
    """Lit l'entreprise et l'exercice dans un nom du type `totalenergies_2025_urd.pdf`."""
    match = _FILENAME.match(path.stem.lower())
    if not match:
        return DocumentInfo(None, None)
    return DocumentInfo(match["company"], int(match["year"]))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build_chunks(blocks: list[Block], info: DocumentInfo, config: ChunkingConfig) -> list[Chunk]:
    chunks = chunk_blocks(blocks, config)
    for c in chunks:
        c.metadata.update({"company": info.company, "fiscal_year": info.fiscal_year})
    return chunks


@dataclass
class IngestReport:
    filename: str
    status: str  # "ingested" | "skipped"
    n_chunks: int = 0
    seconds: float = 0.0


def ingest_file(
    path: Path,
    conn: psycopg.Connection,
    embedder: Embedder,
    *,
    cache_dir: Path,
    config: ChunkingConfig,
    page_range: tuple[int, int] | None = None,
    force: bool = False,
) -> IngestReport:
    start = time.perf_counter()
    sha = file_sha256(path)
    existing = db.get_document(conn, path.name)
    # Ingestion incrémentale : un fichier inchangé n'est pas retraité.
    if existing and existing.sha256 == sha and not force and page_range is None:
        return IngestReport(path.name, "skipped")

    doc = load_or_convert(path, cache_dir, page_range, force=force)
    info = parse_filename(path)
    chunks = build_chunks(to_blocks(doc), info, config)
    logger.info("chunks créés", extra={"document": path.name, "n_chunks": len(chunks)})

    embeddings = embedder.embed([c.content for c in chunks])
    db.replace_document(
        conn,
        filename=path.name,
        sha256=sha,
        company=info.company,
        fiscal_year=info.fiscal_year,
        n_pages=doc.num_pages(),
        chunks=chunks,
        embeddings=embeddings,
    )
    return IngestReport(path.name, "ingested", len(chunks), time.perf_counter() - start)
