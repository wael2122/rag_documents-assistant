"""Point d'entrée en ligne de commande : `doc-assistant --help`."""

from pathlib import Path

import typer

from doc_assistant.config import get_settings
from doc_assistant.eval.golden_set import GoldenSetError, load_golden_set, type_distribution
from doc_assistant.health import run_all
from doc_assistant.logging_setup import setup_logging

app = typer.Typer(help="Assistant documentaire multimodal sur des rapports annuels.")


@app.callback()
def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_json)


@app.command()
def check() -> None:
    """Vérifie la base de données, Ollama et les modèles."""
    results = run_all(get_settings())
    for r in results:
        mark = "OK " if r.ok else "KO "
        typer.echo(f"[{mark}] {r.name} : {r.detail}")
    if not all(r.ok for r in results):
        raise typer.Exit(code=1)


@app.command("check-golden-set")
def check_golden_set(path: Path | None = None) -> None:
    """Valide le format du jeu de test et affiche la répartition par type."""
    target = path or get_settings().golden_set_path
    try:
        items = load_golden_set(target)
    except (GoldenSetError, FileNotFoundError) as exc:
        typer.echo(f"Erreur : {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"{len(items)} question(s) valides dans {target}")
    for qtype, count in type_distribution(items).items():
        share = 100 * count / len(items) if items else 0
        typer.echo(f"  {qtype:<14} {count:>3}  ({share:.0f} %)")
