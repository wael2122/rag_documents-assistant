# Assistant documentaire multimodal — rapports annuels

Assistant qui répond en français à des questions sur des rapports annuels d'entreprises (texte, tableaux
et graphiques), cite ses sources page par page et tourne **entièrement en local** (Ollama + GPU).

> Statut : phase 1 — fondations. Les résultats chiffrés seront publiés dans
> [`docs/resultats.md`](docs/resultats.md) à chaque version.

## Démarrage rapide

Prérequis : Docker, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) et un GPU NVIDIA.

```bash
# 1. Dépendances Python
uv sync --extra dev

# 2. Configuration
cp .env.example .env

# 3. Base de données (PostgreSQL + pgvector, schéma créé automatiquement)
docker compose up -d db

# 4. Modèles locaux
ollama pull qwen3:8b
ollama pull qwen2.5vl:7b
ollama pull bge-m3

# 5. Vérification de l'environnement
uv run doc-assistant check
```

## Structure

```text
├── data/eval/          # jeu de test (golden set)
├── data/raw/           # rapports PDF (non versionnés)
├── docs/               # cadrage, corpus, ADR, résultats
├── sql/                # schéma de la base
├── src/doc_assistant/  # code applicatif
└── tests/
```

## Documentation

- [Cadrage du projet](docs/cadrage.md)
- [Corpus](docs/corpus.md)
- [Jeu de test](docs/jeu-de-test.md)
- Décisions d'architecture : [modèles locaux](docs/adr/0001-modeles-locaux.md),
  [base vectorielle](docs/adr/0002-base-vectorielle.md)

## Qualité

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src
uv run pytest
uv run pre-commit install   # vérifications automatiques avant chaque commit
```
