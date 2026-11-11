"""Point d'entrée en ligne de commande : `doc-assistant --help`."""

import random
from pathlib import Path
from typing import Annotated

import typer

from doc_assistant.config import Settings, get_settings
from doc_assistant.eval.golden_set import GoldenSetError, load_golden_set, type_distribution
from doc_assistant.health import run_all
from doc_assistant.ingestion.chunker import ChunkingConfig
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


def _parse_pages(pages: str | None) -> tuple[int, int] | None:
    if not pages:
        return None
    try:
        start, end = (int(p) for p in pages.split("-"))
    except ValueError as exc:
        raise typer.BadParameter("format attendu : 1-20") from exc
    if not 1 <= start <= end:
        raise typer.BadParameter("plage de pages invalide")
    return start, end


def _chunking_config(settings: Settings) -> ChunkingConfig:
    return ChunkingConfig(
        max_words=settings.chunk_max_words,
        overlap_words=settings.chunk_overlap_words,
        max_table_words=settings.chunk_max_table_words,
    )


@app.command()
def ingest(
    path: Annotated[
        Path | None, typer.Argument(help="Un PDF ou un dossier (défaut : data/raw)")
    ] = None,
    pages: Annotated[str | None, typer.Option(help="Plage de pages pour tester, ex. 1-20")] = None,
    force: Annotated[bool, typer.Option(help="Réanalyse même si rien n'a changé")] = False,
) -> None:
    """Analyse les PDF, les découpe, calcule les embeddings et les stocke en base."""
    from doc_assistant import db
    from doc_assistant.ingestion.embedder import OllamaEmbedder
    from doc_assistant.ingestion.pipeline import ingest_file

    settings = get_settings()
    target = path or settings.raw_data_dir
    pdfs = sorted(target.glob("*.pdf")) if target.is_dir() else [target]
    if not pdfs:
        typer.echo(f"Aucun PDF trouvé dans {target}", err=True)
        raise typer.Exit(code=1)

    embedder = OllamaEmbedder(
        settings.ollama_base_url,
        settings.embedding_model,
        settings.embedding_dim,
        batch_size=settings.embedding_batch_size,
    )
    with db.connect(str(settings.database_url)) as conn:
        for pdf in pdfs:
            typer.echo(f"→ {pdf.name} …")
            report = ingest_file(
                pdf,
                conn,
                embedder,
                cache_dir=settings.processed_dir,
                config=_chunking_config(settings),
                page_range=_parse_pages(pages),
                force=force,
            )
            if report.status == "skipped":
                typer.echo("  inchangé, ignoré (utilise --force pour réanalyser)")
            else:
                typer.echo(f"  {report.n_chunks} chunks indexés en {report.seconds:.0f} s")


@app.command()
def inspect(
    n: Annotated[int, typer.Option(help="Nombre de chunks à afficher")] = 5,
    document: Annotated[str | None, typer.Option(help="Filtrer sur un fichier")] = None,
    seed: Annotated[int | None, typer.Option(help="Graine pour un tirage reproductible")] = None,
) -> None:
    """Affiche des chunks tirés au hasard, pour vérifier la qualité du découpage à l'œil."""
    from doc_assistant import db

    settings = get_settings()
    with db.connect(str(settings.database_url)) as conn:
        stats = conn.execute(
            """SELECT d.filename, c.content_type, count(*),
                      round(avg(array_length(regexp_split_to_array(c.content, '\\s+'), 1)))
               FROM chunks c JOIN documents d ON d.id = c.document_id
               GROUP BY 1, 2 ORDER BY 1, 2"""
        ).fetchall()
        typer.echo("Document / type / nombre de chunks / mots en moyenne")
        for filename, ctype, count, avg_words in stats:
            typer.echo(f"  {filename:<32} {ctype:<6} {count:>5}  {avg_words}")

        rows = conn.execute(
            """SELECT c.id, d.filename, c.page_start, c.page_end, c.section, c.content_type,
                      c.content
               FROM chunks c JOIN documents d ON d.id = c.document_id
               WHERE %(doc)s::text IS NULL OR d.filename = %(doc)s
               ORDER BY c.id""",
            {"doc": document},
        ).fetchall()
    if not rows:
        typer.echo("Aucun chunk en base : lance d'abord `doc-assistant ingest`.")
        raise typer.Exit(code=1)
    for row in random.Random(seed).sample(rows, min(n, len(rows))):
        cid, filename, p1, p2, section, ctype, content = row
        pages_txt = f"p. {p1}" if p1 == p2 else f"p. {p1}-{p2}"
        typer.echo(f"\n─── chunk {cid} · {filename} · {pages_txt} · {ctype} · {section}")
        typer.echo(content[:1200] + (" […]" if len(content) > 1200 else ""))
