"""Teste la conversion d'un DoclingDocument en blocs, sans lancer les modèles d'analyse."""

from pathlib import Path

import pytest

doc_types = pytest.importorskip("docling_core.types.doc")

from doc_assistant.ingestion.models import BlockKind  # noqa: E402
from doc_assistant.ingestion.parser import load_or_convert, to_blocks  # noqa: E402


def _prov(page: int):  # type: ignore[no-untyped-def]
    return doc_types.ProvenanceItem(
        page_no=page, bbox=doc_types.BoundingBox(l=0, t=10, r=100, b=0), charspan=(0, 1)
    )


def _cell(text: str, row: int, col: int, header: bool = False):  # type: ignore[no-untyped-def]
    return doc_types.TableCell(
        text=text,
        start_row_offset_idx=row,
        end_row_offset_idx=row + 1,
        start_col_offset_idx=col,
        end_col_offset_idx=col + 1,
        column_header=header,
    )


def build_document():  # type: ignore[no-untyped-def]
    doc = doc_types.DoclingDocument(name="test")
    doc.add_page(page_no=453, size=doc_types.Size(width=600, height=800))
    doc.add_text(label=doc_types.DocItemLabel.PAGE_HEADER, text="En-tête répété", prov=_prov(453))
    doc.add_heading(text="8.2 Compte de résultat consolidé", prov=_prov(453))
    doc.add_text(
        label=doc_types.DocItemLabel.TEXT, text="Exercice en millions de dollars.", prov=_prov(453)
    )
    cells = [
        _cell("Poste", 0, 0, True),
        _cell("2025", 0, 1, True),
        _cell("Chiffre d'affaires", 1, 0),
        _cell("201 196", 1, 1),
    ]
    caption = doc.add_text(label=doc_types.DocItemLabel.CAPTION, text="Tableau 1", prov=_prov(453))
    table = doc.add_table(
        data=doc_types.TableData(num_rows=2, num_cols=2, table_cells=cells),
        caption=caption,
        prov=_prov(453),
    )
    assert table is not None
    doc.add_table(
        data=doc_types.TableData(num_rows=1, num_cols=1, table_cells=[_cell("Sommaire", 0, 0)]),
        label=doc_types.DocItemLabel.DOCUMENT_INDEX,
        prov=_prov(453),
    )
    return doc


def test_to_blocks_keeps_body_and_tables() -> None:
    blocks = to_blocks(build_document())
    kinds = [b.kind for b in blocks]
    assert kinds == [BlockKind.HEADING, BlockKind.TEXT, BlockKind.TABLE]
    assert all(b.page == 453 for b in blocks)
    table = blocks[-1]
    assert "201 196" in table.text and "| Poste" in table.text
    assert table.caption == "Tableau 1"
    assert all("En-tête" not in b.text for b in blocks)
    assert all("Sommaire" not in b.text for b in blocks)


def test_cache_round_trip(tmp_path: Path) -> None:
    doc = build_document()
    pdf = tmp_path / "x_2025_urd.pdf"
    pdf.write_bytes(b"%PDF")
    doc.save_as_json(tmp_path / "x_2025_urd.docling.json")
    loaded = load_or_convert(pdf, tmp_path)  # lit le cache, n'appelle pas les modèles
    assert [b.text for b in to_blocks(loaded)] == [b.text for b in to_blocks(doc)]
