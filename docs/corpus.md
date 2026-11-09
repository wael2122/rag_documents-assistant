# Corpus

## Choix

Six documents d'enregistrement universel (exercice 2025, publiés au printemps 2026) d'entreprises du
CAC 40, choisis pour couvrir des secteurs variés et donc des tableaux et graphiques différents.

| Entreprise | Secteur | Intérêt pour le projet |
| --- | --- | --- |
| TotalEnergies | Énergie | Nombreux tableaux d'émissions et de production |
| L'Oréal | Cosmétique | Ventes par division et par zone, graphiques |
| Airbus | Aéronautique | Carnet de commandes, livraisons, risques industriels |
| Schneider Electric | Équipements électriques | Indicateurs ESG détaillés |
| Danone | Agroalimentaire | Données par catégorie et par région |
| Orange | Télécoms | Indicateurs clients, segments, effectifs |

Tu peux remplacer une entreprise par une autre : l'important est la variété des contenus.

## Téléchargement

1. Va sur la page « Investisseurs » du site de chaque entreprise, rubrique « Document d'enregistrement
   universel » ou « Rapport annuel ».
2. Télécharge la version PDF de l'exercice 2025.
3. Renomme le fichier ainsi : `<entreprise>_2025_urd.pdf` en minuscules, sans accents
   (ex. `loreal_2025_urd.pdf`).
4. Place-le dans `data/raw/`.

`data/raw/` est exclu de git : ces documents ne nous appartiennent pas, on ne les republie pas.

## Pour démarrer plus vite

Les phases 2 et 3 peuvent commencer avec **deux documents seulement**. On ajoutera les autres quand le
pipeline d'ingestion sera stable.
