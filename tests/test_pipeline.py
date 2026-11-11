import os
from collections.abc import Iterator, Sequence
from pathlib import Path

import psycopg
import pytest

from doc_assistant.ingestion import pipeline
from doc_assistant.ingestion.chunker import ChunkingConfig
from doc_assistant.ingestion.models import Block, BlockKind
from doc_assistant.ingestion.pipeline import DocumentInfo, ingest_file, parse_filename

DIM = 1024


def test_parse_filename() -> None:
    assert parse_filename(Path("totalenergies_2025_urd.pdf")) == DocumentInfo("totalenergies", 2025)
    assert parse_filename(Path("Loreal_2024_URD.pdf")) == DocumentInfo("loreal", 2024)
    assert parse_filename(Path("rapport.pdf")) == DocumentInfo(None, None)


class FakeEmbedder:
    dim = DIM

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls += 1
        return [[(len(t) % 7 + 1) / 10] * DIM for t in texts]


class FakeDoc:
    def num_pages(self) -> int:
        return 3


BLOCKS = [
    Block(BlockKind.HEADING, "8.2 Compte de résultat consolidé", 1),
    Block(BlockKind.TEXT, "Le chiffre d'affaires du groupe a reculé en 2025.", 1),
    Block(
        BlockKind.TABLE,
        "| Exercice | 2025 |\n| --- | --- |\n| Chiffre d'affaires | 201 196 |",
        2,
    ),
]


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL non défini (base PostgreSQL de test requise)")
    with psycopg.connect(url) as c:
        c.execute("DELETE FROM documents WHERE filename LIKE 'test_%'")
        c.commit()
        yield c
        c.execute("DELETE FROM documents WHERE filename LIKE 'test_%'")
        c.commit()


@pytest.fixture
def fake_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "load_or_convert", lambda *a, **k: FakeDoc())
    monkeypatch.setattr(pipeline, "to_blocks", lambda doc: BLOCKS)


@pytest.mark.usefixtures("fake_parsing")
def test_ingest_stores_chunks_and_is_incremental(conn: psycopg.Connection, tmp_path: Path) -> None:
    pdf = tmp_path / "test_2025_urd.pdf"
    pdf.write_bytes(b"%PDF-1.4 contenu de test")
    embedder = FakeEmbedder()
    kwargs = {"cache_dir": tmp_path, "config": ChunkingConfig()}

    report = ingest_file(pdf, conn, embedder, **kwargs)  # type: ignore[arg-type]
    assert report.status == "ingested"
    assert report.n_chunks == 2

    rows = conn.execute(
        """SELECT c.content_type, c.page_start, c.section, c.metadata->>'fiscal_year',
                  d.company, d.fiscal_year, d.n_pages
           FROM chunks c JOIN documents d ON d.id = c.document_id
           WHERE d.filename = %s ORDER BY c.id""",
        (pdf.name,),
    ).fetchall()
    assert [r[0] for r in rows] == ["text", "table"]
    assert rows[1][1] == 2
    assert rows[0][2] == "8.2 Compte de résultat consolidé"
    assert rows[0][3] == "2025"
    assert rows[0][4:] == ("test", 2025, 3)

    # Même fichier : rien n'est recalculé.
    again = ingest_file(pdf, conn, embedder, **kwargs)  # type: ignore[arg-type]
    assert again.status == "skipped"
    assert embedder.calls == 1

    # Fichier modifié : le document est remplacé, sans doublon.
    pdf.write_bytes(b"%PDF-1.4 nouvelle version")
    assert ingest_file(pdf, conn, embedder, **kwargs).status == "ingested"  # type: ignore[arg-type]
    count = conn.execute(
        "SELECT count(*) FROM chunks c JOIN documents d ON d.id = c.document_id "
        "WHERE d.filename = %s",
        (pdf.name,),
    ).fetchone()
    assert count == (2,)


@pytest.mark.usefixtures("fake_parsing")
def test_vector_search_finds_stored_chunk(conn: psycopg.Connection, tmp_path: Path) -> None:
    pdf = tmp_path / "test_2024_urd.pdf"
    pdf.write_bytes(b"%PDF-1.4 x")
    ingest_file(pdf, conn, FakeEmbedder(), cache_dir=tmp_path, config=ChunkingConfig())
    query = "[" + ",".join(["0.1"] * DIM) + "]"
    row = conn.execute(
        "SELECT content_type FROM chunks ORDER BY embedding <=> %s::vector LIMIT 1", (query,)
    ).fetchone()
    assert row is not None
