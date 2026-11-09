import json
from pathlib import Path

import pytest

from doc_assistant.eval.golden_set import (
    GoldenSetError,
    QuestionType,
    load_golden_set,
    type_distribution,
)

EXAMPLE = Path(__file__).parents[1] / "data" / "eval" / "golden_set.example.jsonl"


def _write(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    path = tmp_path / "golden.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return path


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": "q1",
        "question": "Quel est le chiffre d'affaires ?",
        "answer": "10 Md€",
        "type": "table",
        "sources": [{"document": "a.pdf", "pages": [3]}],
    }
    row.update(overrides)
    return row


def test_example_file_is_valid() -> None:
    items = load_golden_set(EXAMPLE)
    assert len(items) == 3
    assert type_distribution(items)[QuestionType.OUT_OF_CORPUS.value] == 1


def test_duplicate_id_rejected(tmp_path: Path) -> None:
    with pytest.raises(GoldenSetError, match="double"):
        load_golden_set(_write(tmp_path, [_row(), _row()]))


def test_missing_sources_rejected(tmp_path: Path) -> None:
    with pytest.raises(GoldenSetError, match=":1:"):
        load_golden_set(_write(tmp_path, [_row(sources=[])]))


def test_out_of_corpus_must_have_no_source(tmp_path: Path) -> None:
    with pytest.raises(GoldenSetError):
        load_golden_set(_write(tmp_path, [_row(type="out_of_corpus")]))


def test_multi_doc_needs_two_documents(tmp_path: Path) -> None:
    with pytest.raises(GoldenSetError):
        load_golden_set(_write(tmp_path, [_row(type="multi_doc")]))
    two_docs = [{"document": "a.pdf", "pages": [1]}, {"document": "b.pdf", "pages": [2]}]
    assert load_golden_set(_write(tmp_path, [_row(type="multi_doc", sources=two_docs)]))


def test_page_zero_rejected(tmp_path: Path) -> None:
    with pytest.raises(GoldenSetError):
        load_golden_set(_write(tmp_path, [_row(sources=[{"document": "a.pdf", "pages": [0]}])]))
