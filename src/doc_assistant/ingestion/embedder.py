"""Calcul des embeddings via l'API d'Ollama."""

from collections.abc import Sequence
from typing import Protocol

import httpx


class Embedder(Protocol):
    dim: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class EmbeddingError(RuntimeError):
    pass


class OllamaEmbedder:
    """Envoie les textes par lots à `POST /api/embed` (embeddings normalisés)."""

    def __init__(
        self,
        base_url: str,
        model: str,
        dim: int,
        batch_size: int = 32,
        timeout: float = 300.0,
    ) -> None:
        self.model = model
        self.dim = dim
        self.batch_size = batch_size
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = list(texts[start : start + self.batch_size])
            resp = self._client.post("/api/embed", json={"model": self.model, "input": batch})
            if resp.status_code != 200:
                raise EmbeddingError(f"Ollama a répondu {resp.status_code} : {resp.text[:200]}")
            batch_vectors: list[list[float]] = resp.json()["embeddings"]
            for v in batch_vectors:
                if len(v) != self.dim:
                    raise EmbeddingError(
                        f"dimension {len(v)} reçue, {self.dim} attendue : "
                        "vérifie EMBEDDING_DIM et le schéma SQL"
                    )
            vectors.extend(batch_vectors)
        return vectors
