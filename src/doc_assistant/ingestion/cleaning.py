"""Nettoyage du texte extrait des PDF."""

import re
import unicodedata

# Certaines polices des rapports encodent la ligature « fi » avec un glyphe que l'extraction
# décode en « Ř » (ex. « VériŘcations »). Ce caractère n'existe pas en français : on le remplace
# seulement quand il est collé à une lettre, pour ne pas toucher un « Ř » isolé.
_BROKEN_FI = re.compile(r"(?<=\w)Ř|Ř(?=\w)")

# Caractères attendus dans un rapport en français ; les autres sont signalés par `inspect`.
_EXPECTED = set("àâäçéèêëîïôöùûüÿœæÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆ«»’‘“”–—…€£$%°•·×÷±≤≥µ²³½¼¾©®™§¶†‡→←↑↓")


def clean_text(text: str) -> str:
    # NFKC décompose les ligatures typographiques (ﬁ → fi, ﬂ → fl) et normalise les espaces.
    text = unicodedata.normalize("NFKC", text)
    text = _BROKEN_FI.sub("fi", text)
    return text


def suspicious_chars(text: str) -> set[str]:
    """Caractères inattendus : signe probable d'un problème d'encodage dans le PDF."""
    return {c for c in text if not c.isascii() and c not in _EXPECTED and not c.isspace()}


def dedupe_label_columns(markdown: str) -> str:
    """Vide la 2e colonne quand elle répète la 1re (cellules fusionnées dupliquées).

    Docling recopie parfois un libellé de ligne fusionné sur deux colonnes :
    « | Résultat net | Résultat net | 13 357 | ». Seules les cellules contenant des lettres sont
    concernées, pour ne jamais effacer un chiffre identique d'une colonne à l'autre.
    """
    out: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            out.append(line)
            continue
        cells = stripped[1:-1].split("|")
        if len(cells) >= 2:
            first, second = cells[0].strip(), cells[1].strip()
            if first and first == second and any(ch.isalpha() for ch in first):
                cells[1] = " " * len(cells[1])
        out.append("|" + "|".join(cells) + "|")
    return "\n".join(out)
