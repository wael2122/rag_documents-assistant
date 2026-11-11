"""Conversion PDF -> blocs, avec Docling.

Docling analyse la mise en page (titres, paragraphes, tableaux, images, en-têtes et pieds de
page). L'analyse est lente (plusieurs minutes pour un rapport de 600 pages) : le résultat est
donc mis en cache en JSON dans `data/processed/`, pour pouvoir modifier le découpage sans
tout réanalyser.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from doc_assistant.ingestion.models import Block, BlockKind

if TYPE_CHECKING:
    from docling_core.types.doc import DoclingDocument

logger = logging.getLogger(__name__)

# Les en-têtes et pieds de page sont classés à part par Docling et ne sont pas parcourus.
_HEADING_LABELS = {"title", "section_header"}
_TEXT_LABELS = {"text", "paragraph", "list_item", "footnote", "formula", "code"}
_SKIPPED_LABELS = {"caption", "page_header", "page_footer"}  # légendes rattachées aux tableaux


def convert_pdf(path: Path, page_range: tuple[int, int] | None = None) -> "DoclingDocument":
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions()
    options.do_ocr = False  # les rapports ont une couche texte : l'OCR serait lent et inutile
    options.do_table_structure = True
    options.table_structure_options.mode = TableFormerMode.ACCURATE
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )
    kwargs = {"page_range": page_range} if page_range else {}
    return converter.convert(path, **kwargs).document


def load_or_convert(
    path: Path, cache_dir: Path, page_range: tuple[int, int] | None = None, force: bool = False
) -> "DoclingDocument":
    from docling_core.types.doc import DoclingDocument

    suffix = f".p{page_range[0]}-{page_range[1]}" if page_range else ""
    cache = cache_dir / f"{path.stem}{suffix}.docling.json"
    if cache.exists() and not force:
        logger.info("analyse lue depuis le cache", extra={"cache": str(cache)})
        return DoclingDocument.load_from_json(cache)
    logger.info("analyse Docling en cours", extra={"document": path.name})
    doc = convert_pdf(path, page_range)
    cache_dir.mkdir(parents=True, exist_ok=True)
    doc.save_as_json(cache)
    return doc


def to_blocks(doc: "DoclingDocument") -> list[Block]:
    """Parcourt le document dans l'ordre de lecture et produit des blocs typés."""
    from docling_core.types.doc import PictureItem, TableItem, TextItem

    blocks: list[Block] = []
    for item, _level in doc.iterate_items():
        if not getattr(item, "prov", None):
            continue
        page = item.prov[0].page_no
        label = str(item.label.value if hasattr(item.label, "value") else item.label)

        if isinstance(item, TableItem):
            if label == "document_index":
                # Le sommaire répète les titres de tout le document : du bruit pour la recherche.
                continue
            markdown = item.export_to_markdown(doc=doc).strip()
            caption = item.caption_text(doc).strip() or None
            if markdown:
                blocks.append(Block(BlockKind.TABLE, markdown, page, caption))
        elif isinstance(item, PictureItem):
            caption = item.caption_text(doc).strip() or None
            blocks.append(Block(BlockKind.FIGURE, caption or "", page, caption))
        elif isinstance(item, TextItem):
            if label in _SKIPPED_LABELS:
                continue
            kind = BlockKind.HEADING if label in _HEADING_LABELS else BlockKind.TEXT
            if label not in _HEADING_LABELS | _TEXT_LABELS:
                logger.debug("étiquette inconnue traitée comme texte", extra={"label": label})
            blocks.append(Block(kind, item.text, page))
    return blocks
