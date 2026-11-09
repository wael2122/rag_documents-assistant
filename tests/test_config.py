import pytest
from pydantic import ValidationError

from doc_assistant.config import Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    s = Settings(_env_file=None)
    assert s.embedding_model == "bge-m3"
    assert s.embedding_dim == 1024


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENERATION_MODEL", "gemma3:12b")
    monkeypatch.setenv("EMBEDDING_DIM", "768")
    s = Settings(_env_file=None)
    assert s.generation_model == "gemma3:12b"
    assert s.embedding_dim == 768


def test_embedding_dim_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    # pgvector indexe au maximum 2000 dimensions avec le type vector.
    monkeypatch.setenv("EMBEDDING_DIM", "4096")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
