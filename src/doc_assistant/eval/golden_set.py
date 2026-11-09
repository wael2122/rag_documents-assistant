"""Format et validation du jeu de test (golden set)."""

import json
from collections import Counter
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator


class QuestionType(StrEnum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    MULTI_DOC = "multi_doc"
    OUT_OF_CORPUS = "out_of_corpus"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SourceRef(BaseModel):
    document: str = Field(min_length=1)
    pages: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def pages_positive(self) -> "SourceRef":
        if any(p < 1 for p in self.pages):
            raise ValueError("les numéros de page commencent à 1")
        return self


class GoldenItem(BaseModel):
    id: str = Field(min_length=1)
    question: str = Field(min_length=5)
    answer: str = Field(min_length=1)
    type: QuestionType
    sources: list[SourceRef] = Field(default_factory=list)
    difficulty: Difficulty | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def sources_match_type(self) -> "GoldenItem":
        if self.type is QuestionType.OUT_OF_CORPUS and self.sources:
            raise ValueError("une question hors corpus ne doit pas avoir de source")
        if self.type is not QuestionType.OUT_OF_CORPUS and not self.sources:
            raise ValueError("au moins une source est requise")
        if self.type is QuestionType.MULTI_DOC and len({s.document for s in self.sources}) < 2:
            raise ValueError("une question multi_doc doit citer au moins deux documents")
        return self


class GoldenSetError(Exception):
    """Erreur de format dans le jeu de test, avec le numéro de ligne."""


def load_golden_set(path: Path) -> list[GoldenItem]:
    items: list[GoldenItem] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                item = GoldenItem.model_validate(json.loads(line))
            except (json.JSONDecodeError, ValidationError) as exc:
                raise GoldenSetError(f"{path}:{lineno}: {exc}") from exc
            if item.id in seen:
                raise GoldenSetError(f"{path}:{lineno}: identifiant en double '{item.id}'")
            seen.add(item.id)
            items.append(item)
    return items


def type_distribution(items: list[GoldenItem]) -> dict[str, int]:
    counts = Counter(item.type.value for item in items)
    return {t.value: counts.get(t.value, 0) for t in QuestionType}
