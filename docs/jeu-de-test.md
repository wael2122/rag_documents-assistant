# Jeu de test (golden set)

Le jeu de test est la pièce la plus importante du projet : sans lui, aucune amélioration n'est prouvable.

## Fichier

`data/eval/golden_set.jsonl`, une question par ligne au format JSON. Le format est vérifié par
`doc_assistant.eval.golden_set` (commande `doc-assistant check-golden-set`).

| Champ | Type | Description |
| --- | --- | --- |
| `id` | texte | Identifiant unique, ex. `q001` |
| `question` | texte | La question, formulée comme un vrai utilisateur |
| `answer` | texte | La réponse attendue, courte et factuelle |
| `type` | `text`, `table`, `figure`, `multi_doc`, `out_of_corpus` | Où se trouve la réponse |
| `sources` | liste | Documents et pages contenant la réponse (vide pour `out_of_corpus`) |
| `difficulty` | `easy`, `medium`, `hard` | Facultatif |
| `notes` | texte | Facultatif : remarque, ambiguïté |

## Objectif : 60 à 80 questions

| Type | Part | Exemple de question |
| --- | --- | --- |
| `text` | ~40 % | Quels sont les principaux facteurs de risque cités ? |
| `table` | ~25 % | Quel est le chiffre d'affaires de la division X en 2025 ? |
| `figure` | ~15 % | Quelle zone géographique a le plus progressé selon le graphique ? |
| `multi_doc` | ~10 % | Laquelle des deux entreprises a le plus d'employés ? |
| `out_of_corpus` | ~10 % | Quel sera le dividende 2030 ? |

## Règles

1. **Écris les questions à la main**, en ouvrant le PDF. Une question générée par un LLM est souvent trop
   facile et rend les scores flatteurs.
2. **Note la page exacte** (numéro de page du PDF, pas celui imprimé en bas de page).
3. Une réponse = un fait vérifiable. Évite « Parle-moi de la stratégie ».
4. Varie les formulations : synonymes, questions vagues, fautes de frappe légères.
5. Commence par 20 questions sur 2 documents, puis complète.
