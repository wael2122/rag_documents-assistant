import pytest

from doc_assistant.ingestion.chunker import ChunkingConfig, chunk_blocks
from doc_assistant.ingestion.models import Block, BlockKind, ChunkType


def words(n: int, prefix: str = "mot") -> str:
    return " ".join(f"{prefix}{i}." if i % 20 == 19 else f"{prefix}{i}" for i in range(n))


def text(t: str, page: int = 1) -> Block:
    return Block(BlockKind.TEXT, t, page)


def heading(t: str, page: int = 1) -> Block:
    return Block(BlockKind.HEADING, t, page)


CFG = ChunkingConfig(max_words=50, overlap_words=10, max_table_words=30)


def test_short_paragraphs_are_grouped() -> None:
    chunks = chunk_blocks([heading("1.1 Intro"), text("un deux"), text("trois quatre")], CFG)
    assert len(chunks) == 1
    assert chunks[0].content == "un deux trois quatre"
    assert chunks[0].section == "1.1 Intro"


def test_heading_closes_chunk_without_overlap() -> None:
    blocks = [heading("A"), text("alpha beta"), heading("B"), text("gamma")]
    chunks = chunk_blocks(blocks, CFG)
    assert [c.section for c in chunks] == ["A", "B"]
    assert chunks[1].content == "gamma"


def test_no_chunk_exceeds_max_words() -> None:
    blocks = [heading("S")] + [text(words(30, f"p{i}_"), page=i) for i in range(10)]
    chunks = chunk_blocks(blocks, CFG)
    assert len(chunks) > 1
    assert all(c.n_words <= CFG.max_words for c in chunks)


def test_overlap_is_carried_between_chunks() -> None:
    blocks = [heading("S"), text(words(45, "a")), text(words(30, "b"))]
    first, second = chunk_blocks(blocks, CFG)[:2]
    tail = first.content.split()[-CFG.overlap_words :]
    assert second.content.split()[: CFG.overlap_words] == tail


def test_overlap_alone_never_becomes_a_chunk() -> None:
    blocks = [heading("A"), text(words(45, "a")), text(words(30, "b")), heading("B")]
    chunks = chunk_blocks(blocks, CFG)
    assert all(c.content.split()[-1].startswith("b") for c in chunks[1:])


def test_very_long_paragraph_is_split() -> None:
    chunks = chunk_blocks([heading("S"), text(words(200))], CFG)
    assert len(chunks) >= 4
    assert all(c.n_words <= CFG.max_words for c in chunks)


def test_pages_are_tracked() -> None:
    chunks = chunk_blocks([heading("S", 3), text("a b", 3), text("c d", 4)], CFG)
    assert (chunks[0].page_start, chunks[0].page_end) == (3, 4)


def test_table_is_its_own_chunk_with_title() -> None:
    table = "| Année | CA |\n| --- | --- |\n| 2025 | 201 196 |"
    blocks = [heading("8.2 Compte de résultat"), text("intro"), Block(BlockKind.TABLE, table, 453)]
    chunks = chunk_blocks(blocks, CFG)
    assert [c.content_type for c in chunks] == [ChunkType.TEXT, ChunkType.TABLE]
    assert chunks[1].content.startswith("8.2 Compte de résultat")
    assert chunks[1].page_start == 453


def test_large_table_is_split_with_header_repeated() -> None:
    rows = "\n".join(f"| ligne {i} | {i} | {i * 2} |" for i in range(20))
    table = f"| Nom | A | B |\n| --- | --- | --- |\n{rows}"
    chunks = chunk_blocks([Block(BlockKind.TABLE, table, 10)], CFG)
    assert len(chunks) > 1
    assert all("| Nom | A | B |" in c.content for c in chunks)
    all_rows = "".join(c.content for c in chunks)
    assert all(f"| ligne {i} |" in all_rows for i in range(20))


def test_figures_are_skipped_for_now() -> None:
    assert chunk_blocks([Block(BlockKind.FIGURE, "image", 2)], CFG) == []


def test_invalid_overlap_rejected() -> None:
    with pytest.raises(ValueError):
        ChunkingConfig(max_words=10, overlap_words=10)
