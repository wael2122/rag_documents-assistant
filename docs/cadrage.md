# Cadrage du projet

## Problème

Un rapport annuel (document d'enregistrement universel) fait 300 à 500 pages. Les informations utiles
(chiffre d'affaires par segment, émissions de CO2, effectifs, facteurs de risque) sont dispersées dans le
texte, des tableaux et des graphiques. Les retrouver à la main prend du temps et les outils de recherche
classiques ne lisent ni les tableaux ni les graphiques.

## Utilisateurs cibles

- Analyste financier ou extra-financier (ESG) qui compare plusieurs entreprises.
- Étudiant ou journaliste qui cherche un chiffre précis et sa source.

## Ce que fait l'assistant

1. Répond en français à une question posée en langage naturel.
2. Cite systématiquement ses sources : document, page, extrait.
3. Lit le texte, les tableaux et les graphiques.
4. Répond « je ne sais pas » quand l'information n'est pas dans le corpus.
5. Tourne entièrement en local (aucune donnée envoyée à une API externe).

## Hors périmètre (pour l'instant)

- Calculs complexes ou projections financières.
- Documents scannés de mauvaise qualité.
- Langues autres que le français et l'anglais.

## Contraintes

| Contrainte | Valeur |
| --- | --- |
| Exécution | 100 % locale (Ollama + GPU NVIDIA) |
| Langue principale | Français |
| Latence cible | < 15 s par question (p95), à ajuster après la baseline |
| Données | Rapports publics, jamais versionnés dans git |

## Mesure du succès

Le projet est jugé sur le jeu de test `data/eval/golden_set.jsonl` (voir `docs/jeu-de-test.md`).
Chaque version est comparée à la baseline dans `docs/resultats.md`.
