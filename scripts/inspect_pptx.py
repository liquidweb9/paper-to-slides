#!/usr/bin/env python3
"""Archive a reference PPTX, inventory its layouts, and extract selected embedded images."""

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from zipfile import BadZipFile

from prepare_sources import sha256
from project_manager import project_directory, project_lock, project_path


ARCHIVE = "template-source"
IMAGE_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg"}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def image_part(part, blips):
    if not blips:
        return None
    from pptx.oxml.ns import qn

    link = blips[0].get(qn("r:embed"))
    if not link or link not in part.rels or part.rels[link].is_external:
        return None
    return part.related_part(link)


def classify_image(entry, media, blips, images):
    if media is None:
        if blips:
            entry["image"] = {"extractable": False, "reason": "No embedded image; links are not fetched."}
        return
    entry["image"] = {"part": str(media.partname), "content_type": media.content_type,
                      "extractable": media.content_type in IMAGE_EXTENSIONS}
    if entry["image"]["extractable"]:
        images[entry["id"]] = media


def summary(text):
    return " ".join(text.split())[:160]


def shape_inventory(shapes, scope, part, images):
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    entries = []
    for shape in shapes:
        node = shape._element
        entry = {"id": f"{scope}:{shape.shape_id}", "name": shape.name, "type": shape.shape_type.name}
        if shape.is_placeholder:
            entry["placeholder"] = shape.placeholder_format.type.name
        # Group children have group-local coordinates, not slide coordinates.
        entry["box_bp"] = [round(value / 12700, 2) if value is not None else None
                           for value in (shape.left, shape.top, shape.width, shape.height)]
        if shape.has_text_frame and (text := summary(shape.text)):
            entry["text_preview"] = text
        if shape.has_text_frame:
            fonts = sorted(set(node.xpath("./p:txBody/a:p/*/a:rPr/*/@typeface")))
            sizes = sorted(set(node.xpath("./p:txBody/a:p/*/a:rPr/@sz")), key=int)
            if fonts or sizes:
                entry["direct_text_style"] = {"fonts": fonts, "sizes_pt": [int(s) / 100 for s in sizes]}
        for attr, path in (("direct_fill", "./p:spPr/a:solidFill/a:srgbClr/@val"),
                           ("scheme_fill", "./p:spPr/a:solidFill/a:schemeClr/@val")):
            values = node.xpath(path)
            if values:
                entry[attr] = values[0]
        blips = node.xpath("./p:blipFill/a:blip | ./p:spPr/a:blipFill/a:blip")
        classify_image(entry, image_part(part, blips), blips, images)
        if blips:
            crops = node.xpath("./p:blipFill/a:srcRect | ./p:spPr/a:blipFill/a:srcRect")
            if crops and crops[0].attrib:
                entry["image"]["source_rect"] = dict(crops[0].attrib)
            if shape.rotation:
                entry["image"]["rotation_degrees"] = shape.rotation
        # A modern Office picture can show an SVG while storing a PNG fallback.
        if blips and blips[0].xpath(".//*[local-name()='svgBlip']"):
            entry["image"]["visual_fallback"] = True
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            entry["children"] = shape_inventory(shape.shapes, scope, part, images)
        entries.append(entry)
    return entries


def slide_layer(layer, scope, images):
    entry = {"id": scope, "name": layer.name, "shapes": shape_inventory(layer.shapes, scope, layer.part, images)}
    root = layer._element
    entry["show_master_shapes"] = root.get("showMasterSp", "1") not in {"0", "false"}
    backgrounds = root.xpath("./p:cSld/p:bg")
    if backgrounds:
        background = {"id": f"{scope}:bg"}
        blips = backgrounds[0].xpath("./p:bgPr/a:blipFill/a:blip")
        classify_image(background, image_part(layer.part, blips), blips, images)
        for attr, path in (("direct_color", "./p:bgPr/a:solidFill/a:srgbClr/@val"),
                           ("scheme_color", "./p:bgPr/a:solidFill/a:schemeClr/@val"),
                           ("theme_ref", "./p:bgRef/@idx")):
            values = backgrounds[0].xpath(path)
            if values:
                background[attr] = values[0]
        entry["background"] = background
    return entry


def theme_inventory(master):
    from lxml import etree
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from pptx.oxml.ns import nsmap

    try:
        part = master.part.part_related_by(RT.THEME)
    except KeyError:
        return {}
    theme = etree.fromstring(part.blob, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    namespaces = nsmap("a")
    colors = {}
    for element in theme.xpath("./a:themeElements/a:clrScheme/*", namespaces=namespaces):
        values = element.xpath("./a:srgbClr/@val | ./a:sysClr/@lastClr", namespaces=namespaces)
        if values:
            colors[etree.QName(element).localname] = values[0]
    fonts = {}
    for role in ("majorFont", "minorFont"):
        entries = theme.xpath(f"./a:themeElements/a:fontScheme/a:{role}/*", namespaces=namespaces)
        fonts[role] = {element.get("script") or etree.QName(element).localname: element.get("typeface")
                       for element in entries if element.get("typeface")}
    return {"name": theme.get("name"), "colors": colors, "fonts": fonts}


def inventory(path):
    try:
        from pptx import Presentation
    except ImportError as error:
        raise ValueError("PPTX inspection requires python-pptx (python -m pip install python-pptx).") from error

    presentation = Presentation(path)
    if not presentation.slides or not presentation.slide_width or not presentation.slide_height:
        raise ValueError("Expected a PPTX with at least one slide and a valid canvas.")
    width, height = presentation.slide_width, presentation.slide_height
    images, slides, layouts, masters = {}, [], {}, {}
    for number, slide in enumerate(presentation.slides, start=1):
        layout = slide.slide_layout
        master = layout.slide_master
        if master.part.partname not in masters:
            layer = slide_layer(master, f"m{len(masters) + 1}", images)
            layer["theme_candidates"] = theme_inventory(master)
            masters[master.part.partname] = layer
        if layout.part.partname not in layouts:
            layer = slide_layer(layout, f"l{len(layouts) + 1}", images)
            layer["master"] = masters[master.part.partname]["id"]
            layouts[layout.part.partname] = layer
        entry = slide_layer(slide, f"p{number}", images)
        title = slide.shapes.title
        entry.update(page=number, layout=layouts[layout.part.partname]["id"],
                     title=summary(title.text) if title is not None else None,
                     hidden=slide._element.get("show", "1") in {"0", "false"})
        slides.append(entry)
    report = {"sha256": sha256(path), "canvas": {"width_emu": width, "height_emu": height,
              "width_bp": round(width / 12700, 2), "height_bp": round(height / 12700, 2)},
              "slides": slides, "layouts": list(layouts.values()), "masters": list(masters.values())}
    return report, images


def archive_reference(root, source):
    if source.suffix.lower() != ".pptx" or not source.is_file():
        raise ValueError(f"Expected a local .pptx file: {source}")
    destination = project_path(root, ARCHIVE)
    if destination.exists():
        raise ValueError(f"Reference already archived: {destination}. Use a new project for another deck.")
    with tempfile.TemporaryDirectory(prefix=".pptx-", dir=root) as temp:
        staged = Path(temp) / ARCHIVE
        staged.mkdir()
        original = staged / "original.pptx"
        shutil.copyfile(source, original)
        report, _ = inventory(original)
        report["original_name"] = source.name
        write_json(staged / "inventory.json", report)
        staged.rename(destination)
    return destination / "inventory.json"


def extract_images(root, selected):
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("Provide a nonempty list of distinct approved asset IDs.")
    archive = project_path(root, ARCHIVE)
    original = project_path(archive, "original.pptx")
    saved = json.loads(project_path(archive, "inventory.json").read_text(encoding="utf-8"))
    report, images = inventory(original)
    if report["sha256"] != saved["sha256"]:
        raise ValueError("Archived PPTX changed since inspection; inspect and approve the new file in a new project.")
    unavailable = [asset_id for asset_id in selected if asset_id not in images]
    if unavailable:
        raise ValueError("Not an extractable embedded PNG/JPEG object: " + ", ".join(unavailable))

    figures = project_path(project_path(root, "slides"), "figures")
    destination = project_path(figures, "pptx")
    if destination.exists():
        raise ValueError(f"Extraction folder already exists: {destination}. Review and move it before re-extracting.")
    figures.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pptx-", dir=figures) as temp:
        staged = Path(temp) / "pptx"
        staged.mkdir()
        assets = []
        for asset_id in selected:
            media = images[asset_id]
            filename = f"{asset_id.replace(':', '-')}.{IMAGE_EXTENSIONS[media.content_type]}"
            blob = media.blob
            (staged / filename).write_bytes(blob)
            assets.append({"id": asset_id, "path": filename, "part": str(media.partname),
                           "sha256": hashlib.sha256(blob).hexdigest()})
        write_json(staged / "manifest.json", {"source_sha256": report["sha256"], "assets": assets})
        staged.rename(destination)
    return destination / "manifest.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Archive the PPTX and inventory its visible layers; copy no assets")
    inspect.add_argument("project", type=Path)
    inspect.add_argument("pptx", type=Path)
    extract = commands.add_parser("extract", help="Copy only the user-approved embedded image IDs")
    extract.add_argument("project", type=Path)
    extract.add_argument("--asset", action="append", required=True, help="Approved inventory ID; repeat as needed")
    args = parser.parse_args()
    try:
        from lxml.etree import XMLSyntaxError
        from pptx.exc import PackageNotFoundError
    except ImportError:
        parser.exit(1, "PPTX inspection requires python-pptx (python -m pip install python-pptx).\n")
    try:
        root = project_directory(args.project)
        with project_lock(root):
            print(archive_reference(root, args.pptx) if args.command == "inspect" else extract_images(root, args.asset))
    except (OSError, ValueError, RuntimeError, BadZipFile, KeyError, XMLSyntaxError, PackageNotFoundError) as error:
        parser.exit(1, f"PPTX operation failed: {error}\n")


if __name__ == "__main__":
    main()
