# ADR 0003 — Analyse avec Docling et découpage par section

- Statut : accepté pour la baseline (à comparer en phase 4)
- Date : 2026-11-09

## Contexte

Les rapports annuels font plus de 600 pages, avec des titres numérotés, beaucoup de tableaux, des
infographies, et des en-têtes et pieds de page répétés sur chaque page. Une extraction de texte brute
(PyMuPDF) mélange les colonnes et casse les tableaux.

## Décision

1. **Analyse** avec Docling : détection de la mise en page, tableaux reconstruits (TableFormer, mode
   précis), en-têtes et pieds de page écartés, OCR désactivé (les PDF ont une couche texte). Le résultat
   est mis en cache en JSON (`data/processed/`) : on peut changer le découpage sans réanalyser.
2. **Découpage** :
   - un chunk ne traverse jamais un titre de section ;
   - texte regroupé jusqu'à 250 mots, avec 40 mots de chevauchement ;
   - chaque tableau est un chunk à part, converti en Markdown et précédé du titre de sa section ;
     au-delà de 500 mots, il est coupé par lignes en répétant l'en-tête ;
   - le sommaire est ignoré (il répète tous les titres et attirerait les recherches).
3. **Nettoyage** : normalisation Unicode (ligatures « ﬁ », espaces insécables), réparation de la
   ligature « fi » mal encodée par certaines polices (« VériŘcations » → « Vérifications »), et
   suppression de la colonne de libellés dupliquée que Docling produit sur les cellules fusionnées.
   Les intitulés de section gardent le dernier titre numéroté comme contexte
   (« 8.3 Résultat global consolidé > TotalEnergies »).
4. **Métadonnées** : document, entreprise, exercice, pages de début et de fin, section, type.

## Alternatives écartées pour l'instant

- `HybridChunker` de Docling : efficace, mais moins transparent ; à comparer en phase 4.
- Taille de chunk fixe sans tenir compte des sections : plus simple, mais mélange des sujets.

## Conséquences

- L'analyse Docling d'un rapport complet prend plusieurs minutes (bien plus sans GPU).
- La taille est mesurée en mots, pas en tokens : approximation suffisante, `bge-m3` accepte 8 192
  tokens, très au-delà de nos chunks.
- Les figures sont repérées mais pas encore indexées : elles le seront en phase 5 (modèle de vision).
