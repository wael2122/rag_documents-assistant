# ADR 0001 — Modèles 100 % locaux

- Statut : accepté (à réévaluer après la baseline)
- Date : 2026-11-09

## Contexte

Le projet doit tourner sur un PC personnel équipé d'un GPU NVIDIA, sans API payante. Le corpus est en
français et contient des tableaux et graphiques.

## Décision

| Rôle | Modèle par défaut | Servi par | Pourquoi |
| --- | --- | --- | --- |
| Génération des réponses | `qwen3:8b` | Ollama | Bon en français, tient en ~6 Go de VRAM en Q4 |
| Description d'images et de pages | `qwen2.5vl:7b` | Ollama | Solide en OCR et lecture de documents ; `qwen3-vl` à tester si la VRAM le permet |
| Embeddings | `bge-m3` (1024 dimensions) | Ollama | Multilingue, robuste en français, 8 192 tokens de contexte |
| Reranking | `BAAI/bge-reranker-v2-m3` | sentence-transformers | Cross-encoder multilingue, non disponible dans Ollama |

Tous les noms sont configurables dans `.env` : l'architecture ne dépend d'aucun modèle précis.

## Conséquences

- Coût nul par requête, données privées.
- Qualité inférieure aux grands modèles API : à compenser par un meilleur retrieval (hybride, reranking).
- La VRAM limite la taille des modèles chargés en même temps ; génération et vision sont appelées à des
  étapes différentes, Ollama les charge à la demande.
- À comparer en phase 4 : au moins un second modèle d'embedding (ex. `multilingual-e5-large`).
