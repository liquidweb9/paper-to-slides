#!/usr/bin/env python3
"""Export a slide PDF as vector or raster pictures with native PowerPoint speaker notes."""

import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from project_manager import MARKER, project_directory, project_lock, project_path
from build_pdf import require_current_build


SVG_NAMESPACE = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
SVG_EXTENSION = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
SVG_CONTENT_TYPE = "image/svg+xml"
RELATIONSHIP_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SVG_EMBED = f"{{{RELATIONSHIP_NAMESPACE}}}embed"
DEFAULT_PNG_LONG_EDGE = 3840


PAGE_HEADING = re.compile(r"## ([1-9][0-9]*)")
NUMBER = r"[0-9一二三四五六七八九十百〇零两]+"
SOURCE_LOCATOR = re.compile(
    rf"(?:见|参见|详见|请看|查阅|回到)\s*(?:原文|论文的?附录)"
    rf"|(?:原文|论文|文献|附录)(?:中|的|里|见|所列|所示|参见|详见|\s)*(?:第\s*)?"
    rf"(?:{NUMBER}\s*[页章节段行]|(?:图|表|式|公式|定理|附录|位置)\s*[（(]?\s*{NUMBER})"
    rf"|第\s*{NUMBER}\s*页|(?:图|表|公式|方程)\s*[（(]?\s*[0-9]+"
    r"|(?:原文|论文).{0,6}(?:位置|出处)"
    r"|\b(?i:pages?|pp?\.|fig(?:ure)?s?\.?|tables?|eq(?:uation)?s?\.?|sections?|sec\.|appendix)"
    r"\s*(?:\(\s*)?\d+|\b(?i:appendix)\s+[A-Z]\b"
    r"|§\s*\d|#page=\d|#L\d+\b|\bsources[/\\](?:manuscript|supplements)[/\\]"
    r"|https?://(?:www\.)?(?:arxiv\.org|doi\.org|openreview\.net)/"
    r"|(?:^|\n)\s*(?i:source|evidence|原文出处|证据定位|来源)\s*[:：]",
)


def read_notes(path, page_count):
    sections = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        heading = PAGE_HEADING.fullmatch(line.strip())
        if heading:
            expected = len(sections) + 1
            if int(heading[1]) != expected:
                raise ValueError(f"{path}:{line_number}: expected '## {expected}', got '{line.strip()}'.")
            sections.append([])
        elif line.lstrip().startswith("##") or (line.strip() and not sections):
            raise ValueError(f"{path}:{line_number}: use '## N' on its own line for each physical PDF page.")
        elif sections:
            sections[-1].append(line)
    notes = ["\n".join(lines).strip() for lines in sections]
    for number, note in enumerate(notes, 1):
        if not note:
            raise ValueError(f"{path}: missing speaker text for page {number}.")
        locator = SOURCE_LOCATOR.search(note)
        if locator:
            raise ValueError(f"{path}: page {number} contains a source locator ({locator[0]}). Rewrite it as spoken text.")
    if len(notes) != page_count:
        raise ValueError(f"{path}: found {len(notes)} notes for {page_count} PDF pages.")
    return notes


def attach_svg(picture, slide_part, svg, number):
    from lxml import etree
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from pptx.opc.package import Part
    from pptx.opc.packuri import PackURI
    from pptx.oxml.xmlchemy import OxmlElement

    svg_part = Part(PackURI(f"/ppt/media/page-vector-{number}.svg"),
                    SVG_CONTENT_TYPE, slide_part.package, svg)
    blip = picture._element.blipFill.blip
    extensions = OxmlElement("a:extLst")
    extension = OxmlElement("a:ext")
    extension.set("uri", SVG_EXTENSION)
    svg_blip = etree.SubElement(extension, f"{{{SVG_NAMESPACE}}}svgBlip", nsmap={"asvg": SVG_NAMESPACE})
    svg_blip.set(SVG_EMBED, slide_part.relate_to(svg_part, RT.IMAGE))
    extensions.append(extension)
    blip.append(extensions)


def render_svg(converter, pdf, number):
    result = subprocess.run(
        [converter, "-svg", "-origpagesizes", "-f", str(number), "-l", str(number),
         str(pdf.resolve()), "-"],
        capture_output=True,
    )
    if result.returncode or not result.stdout:
        diagnostic = result.stderr.decode(errors="replace").strip()
        raise ValueError(f"Page {number}: pdftocairo did not produce SVG. {diagnostic}")
    return result.stdout


def verify_package(path, notes, pictures, size):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    from pptx.oxml.ns import qn

    deck = Presentation(path)
    if len(deck.slides) != len(notes) or (deck.slide_width, deck.slide_height) != size:
        raise ValueError("Saved PowerPoint page count or slide size changed.")
    for number, (slide, note, (png_digest, svg_digest, bounds)) in enumerate(
        zip(deck.slides, notes, pictures, strict=True), 1
    ):
        if len(slide.shapes) != 1 or slide.shapes[0].shape_type != MSO_SHAPE_TYPE.PICTURE:
            raise ValueError(f"Slide {number}: expected one page image.")
        image = slide.shapes[0]
        if (image.left, image.top, image.width, image.height) != bounds or hashlib.sha256(image.image.blob).digest() != png_digest:
            raise ValueError(f"Slide {number}: page image or placement changed.")
        blip = image._element.blipFill.blip
        svg_blip = blip.find(
            f"{qn('a:extLst')}/{qn('a:ext')}[@uri='{SVG_EXTENSION}']/{{{SVG_NAMESPACE}}}svgBlip"
        )
        if svg_digest is not None:
            svg_id = svg_blip.get(SVG_EMBED) if svg_blip is not None else None
            svg_part = slide.part.related_part(svg_id) if svg_id in slide.part.rels else None
            if (svg_part is None or svg_part.content_type != SVG_CONTENT_TYPE
                    or hashlib.sha256(svg_part.blob).digest() != svg_digest):
                raise ValueError(f"Slide {number}: saved SVG relationship or image changed.")
        elif svg_blip is not None:
            raise ValueError(f"Slide {number}: unexpected SVG in PNG mode.")
        body = slide.notes_slide.notes_text_frame if slide.has_notes_slide else None
        if body is None or body.text != note:
            raise ValueError(f"Slide {number}: saved speaker notes do not match.")


def export(pdf, notes_path, output, image_format="svg", png_long_edge=DEFAULT_PNG_LONG_EDGE):
    try:
        import pymupdf
        from pptx import Presentation
        from pptx.util import Inches
    except ImportError as error:
        raise ValueError("Install the export dependencies: python -m pip install pymupdf python-pptx") from error

    if output.suffix.lower() != ".pptx" or output.resolve() in {pdf.resolve(), notes_path.resolve()}:
        raise ValueError("Choose a .pptx output path distinct from the inputs.")
    if any(parent.name.lower() == "sources" and (parent.parent / MARKER).is_file()
           for parent in output.resolve().parents):
        raise ValueError("Choose an output outside the project's read-only source archive.")
    if png_long_edge < 1:
        raise ValueError("PNG long edge must be a positive number of pixels.")
    converter = shutil.which("pdftocairo") if image_format == "svg" else None
    if image_format == "svg" and converter is None:
        raise ValueError("SVG export requires Poppler's pdftocairo on PATH. Use --format png for raster export.")
    deck = Presentation()
    deck._element.set("autoCompressPictures", "0")
    pictures = []
    with pymupdf.open(pdf) as document:
        if not document.is_pdf or document.needs_pass or not document.page_count:
            raise ValueError(f"Expected a readable slide PDF: {pdf}")
        notes = read_notes(notes_path, document.page_count)
        first = document[0].rect
        unit = Inches(13.333333) / max(first.width, first.height)
        deck.slide_width = round(first.width * unit)
        deck.slide_height = round(first.height * unit)
        for number, (page, note) in enumerate(zip(document, notes, strict=True), 1):
            rect = page.rect
            zoom = png_long_edge / max(rect.width, rect.height)
            png = page.get_pixmap(
                matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csRGB, alpha=False
            ).tobytes("png")
            scale = min(deck.slide_width / rect.width, deck.slide_height / rect.height)
            width, height = round(rect.width * scale), round(rect.height * scale)
            bounds = ((deck.slide_width - width) // 2, (deck.slide_height - height) // 2, width, height)
            slide = deck.slides.add_slide(deck.slide_layouts[6])  # Blank layout in python-pptx's default template.
            picture = slide.shapes.add_picture(io.BytesIO(png), *bounds)
            svg_digest = None
            if converter:
                svg = render_svg(converter, pdf, number)
                attach_svg(picture, slide.part, svg, number)
                svg_digest = hashlib.sha256(svg).digest()
            slide.notes_slide.notes_text_frame.text = note
            pictures.append((hashlib.sha256(png).digest(), svg_digest, bounds))
    with tempfile.TemporaryDirectory(prefix=".pptx-export-", dir=output.parent) as folder:
        candidate = Path(folder) / "candidate.pptx"
        deck.save(candidate)
        verify_package(candidate, notes, pictures, (deck.slide_width, deck.slide_height))
        candidate.replace(output)
    image_summary = f"{png_long_edge}px PNG"
    if image_format == "svg":
        image_summary = f"SVG with {image_summary} fallback"
    print(f"Exported {len(notes)} slides with native speaker notes ({image_summary}): {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Managed talk directory or a finished slide PDF")
    parser.add_argument("--notes", type=Path, help="UTF-8 speaker-notes.md (one '## N' section per PDF page)")
    parser.add_argument("--output", type=Path, help="Standalone PDF mode: destination .pptx (default: beside the PDF)")
    parser.add_argument("--format", choices=("svg", "png"), default="svg",
                        help="Page picture format (default: SVG with a PNG fallback)")
    parser.add_argument("--png-long-edge", type=int, default=DEFAULT_PNG_LONG_EDGE,
                        help=f"PNG long edge in pixels for either format (default: {DEFAULT_PNG_LONG_EDGE})")
    args = parser.parse_args()
    image_options = {"image_format": args.format, "png_long_edge": args.png_long_edge}
    try:
        if args.source.is_dir():
            if args.output:
                raise ValueError("Project mode writes build/main.pptx. Pass a PDF path to choose a different output.")
            root = project_directory(args.source)
            with project_lock(root):
                build = project_path(root, "build")
                require_current_build(build, project_path(root, "slides"))
                report = json.loads(project_path(build, "check.json").read_text(encoding="utf-8"))
                if not isinstance(report, dict) or report.get("automated_checks_passed") is not True:
                    raise ValueError("The current build has not passed PDF checks. Rebuild before exporting.")
                export(project_path(build, "main.pdf"), args.notes or root / "speaker-notes.md",
                       project_path(build, "main.pptx"), **image_options)
        else:
            pdf = args.source
            export(pdf, args.notes or pdf.with_name("speaker-notes.md"),
                   args.output or pdf.with_suffix(".pptx"), **image_options)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"PPTX export failed: {error}\n")


if __name__ == "__main__":
    main()
