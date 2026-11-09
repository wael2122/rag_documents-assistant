# ADR 0002 — PostgreSQL + pgvector

- Statut : accepté
- Date : 2026-11-09

## Contexte

Il faut stocker des chunks, leurs métadonnées et leurs embeddings, et faire à la fois une recherche
vectorielle et une recherche plein texte (pour la recherche hybride de la phase 4).

## Options

| Option | Pour | Contre |
| --- | --- | --- |
| PostgreSQL + pgvector | Une seule base pour vecteurs, plein texte et métadonnées ; SQL déjà maîtrisé | Moins de fonctions natives de recherche hybride |
| Qdrant | Spécialisé, filtrage rapide | Un service de plus ; plein texte limité |
| Chroma | Très simple | Moins adapté à une démo « production » |

## Décision

PostgreSQL 17 avec pgvector (image `pgvector/pgvector:pg17`), index HNSW en distance cosinus et index GIN
sur un `tsvector` en configuration `french` pour la recherche lexicale.

## Conséquences

- La recherche hybride se fait en SQL : deux requêtes, puis fusion RRF en Python.
- La dimension des vecteurs (1024) est figée dans le schéma : changer de modèle d'embedding impose une
  migration et une ré-indexation.
