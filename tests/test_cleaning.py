from doc_assistant.ingestion.cleaning import clean_text, dedupe_label_columns, suspicious_chars


def test_broken_fi_ligature_is_repaired() -> None:
    assert clean_text("VériŘcations spéciŘques") == "Vérifications spécifiques"
    assert clean_text("Informations ﬁnancières") == "Informations financières"


def test_isolated_letter_is_kept() -> None:
    assert clean_text("Ř") == "Ř"


def test_normalizes_spaces_and_subscripts() -> None:
    assert clean_text("12 500 M$ de CO₂") == "12 500 M$ de CO2"


def test_suspicious_chars_ignores_french() -> None:
    assert suspicious_chars("Élève à l'œuvre « déjà » – 3,4 € (Ř)") == {"Ř"}


def test_duplicated_label_column_is_emptied() -> None:
    table = (
        "| Exercice | Exercice | 2025 |\n"
        "|---|---|---|\n"
        "| Résultat net | Résultat net | 13 357 |\n"
        "| Pertes | (note 10) | 42 |"
    )
    lines = dedupe_label_columns(table).splitlines()
    assert lines[0].split("|")[2].strip() == ""
    assert lines[2].split("|")[2].strip() == ""
    assert "(note 10)" in lines[3]


def test_identical_numbers_are_never_removed() -> None:
    row = "| 1 550 000 € | 1 550 000 € |"
    assert dedupe_label_columns(row) == row


def test_broken_fl_ligature_is_repaired() -> None:
    assert clean_text("Tableau des řux de trésorerie") == "Tableau des flux de trésorerie"
    assert clean_text("Řxe et řottant") == "fixe et flottant"
