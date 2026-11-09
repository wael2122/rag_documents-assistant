"""Vérifications de l'environnement : base de données, Ollama et modèles."""

from dataclasses import dataclass

import httpx
import psycopg

from doc_assistant.config import Settings


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def check_database(settings: Settings) -> CheckResult:
    try:
        with psycopg.connect(str(settings.database_url), connect_timeout=5) as conn:
            row = conn.execute(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()
    except psycopg.Error as exc:
        return CheckResult("PostgreSQL", False, f"connexion impossible : {exc}")
    if row is None:
        return CheckResult("PostgreSQL", False, "extension pgvector absente")
    return CheckResult("PostgreSQL", True, f"pgvector {row[0]}")


def check_ollama(settings: Settings) -> list[CheckResult]:
    try:
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        return [CheckResult("Ollama", False, f"injoignable : {exc}")]

    installed = {m["name"] for m in resp.json().get("models", [])}
    results = [CheckResult("Ollama", True, f"{len(installed)} modèle(s) installé(s)")]
    for model in (settings.generation_model, settings.vision_model, settings.embedding_model):
        # Ollama ajoute ":latest" quand aucun tag n'est précisé.
        present = model in installed or f"{model}:latest" in installed
        detail = "installé" if present else f"manquant : lance `ollama pull {model}`"
        results.append(CheckResult(f"Modèle {model}", present, detail))
    return results


def run_all(settings: Settings) -> list[CheckResult]:
    return [check_database(settings), *check_ollama(settings)]
