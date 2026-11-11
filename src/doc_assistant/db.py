"""Accès à la base : documents et chunks."""

import json
from collections.abc import Sequence
from dataclasses import dataclass

import psycopg

from doc_assistant.ingestion.models import Chunk


def to_pgvector(values: Sequence[float]) -> str:
    """Format texte accepté par pgvector : '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{v:.7g}" for v in values) + "]"


@dataclass
class StoredDocument:
    id: int
    filename: str
    sha256: str


def connect(database_url: str) -> psycopg.Connection:
    return psycopg.connect(database_url)


def get_document(conn: psycopg.Connection, filename: str) -> StoredDocument | None:
    row = conn.execute(
        "SELECT id, filename, sha256 FROM documents WHERE filename = %s", (filename,)
    ).fetchone()
    return StoredDocument(*row) if row else None


def replace_document(
    conn: psycopg.Connection,
    *,
    filename: str,
    sha256: str,
    company: str | None,
    fiscal_year: int | None,
    n_pages: int | None,
    chunks: Sequence[Chunk],
    embeddings: Sequence[Sequence[float]],
) -> int:
    """Remplace un document et tous ses chunks, dans une seule transaction."""
    if len(chunks) != len(embeddings):
        raise ValueError("autant d'embeddings que de chunks sont requis")
    with conn.transaction():
        conn.execute("DELETE FROM documents WHERE filename = %s", (filename,))
        row = conn.execute(
            """INSERT INTO documents (filename, company, fiscal_year, sha256, n_pages)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (filename, company, fiscal_year, sha256, n_pages),
        ).fetchone()
        assert row is not None
        doc_id: int = row[0]
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO chunks (document_id, page_start, page_end, section, content_type,
                                       content, content_hash, metadata, embedding)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)""",
                [
                    (
                        doc_id,
                        c.page_start,
                        c.page_end,
                        c.section,
                        c.content_type.value,
                        c.content,
                        c.content_hash,
                        json.dumps(c.metadata, ensure_ascii=False),
                        to_pgvector(e),
                    )
                    for c, e in zip(chunks, embeddings, strict=True)
                ],
            )
    return doc_id
