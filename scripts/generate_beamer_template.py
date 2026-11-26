#!/usr/bin/env python3
"""Generate editable Beamer example frames from a confirmed PPTX template specification."""

import argparse
import json
import re
from pathlib import Path

from inspect_pptx import ARCHIVE
from prepare_sources import sha256
from project_manager import project_directory, project_lock, project_path


LAYOUTS = {"cover", "divider", "bullets", "two-column", "figure", "formula", "summary"}
TEX_ESCAPE = dict(zip(r"\{}$&#%_^~", (r"\textbackslash{}", r"\{", r"\}", r"\$", r"\&", r"\#", r"\%",
                                      r"\_", r"\textasciicircum{}", r"\textasciitilde{}")))


def tex(text):
    if not isinstance(text, str) or not text.strip() or any(ord(char) < 32 for char in text):
        raise ValueError("Expected nonempty, single-line template labels.")
    return "".join(TEX_ESCAPE.get(char, char) for char in text)


def choice(data, key, allowed):
    value = data.get(key)
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{key} must be one of: {', '.join(sorted(allowed))}.")
    return value


def placeholder(label, width, height):
    return rf"\fbox{{\parbox[c][{height}\paperheight][c]{{{width}}}{{\centering {label}}}}}"


def theme(spec, canvas, logo):
    aspect = choice(spec, "canvas", {"source", "16:9", "4:3"})
    ratio = canvas["width_emu"] / canvas["height_emu"] if aspect == "source" else {"16:9": 16/9, "4:3": 4/3}[aspect]
    width, height = 160 * min(1, ratio / (16/9)), 160 * min(1 / ratio, 9/16)
    density = choice(spec, "density", {"roomy", "standard", "compact"})
    margin, font_size = {"roomy": (0.075, "12pt"), "standard": (0.06, "11pt"), "compact": (0.045, "10pt")}[density]
    header = choice(spec, "header", {"plain", "band"})
    footer = choice(spec, "footer", {"none", "number"})
    colors = spec["colors"]
    for name in ("accent", "text", "background", "on_accent"):
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", colors.get(name, "")):
            raise ValueError(f"colors.{name} must be a six-digit hex color without #.")

    sty = [r"\NeedsTeXFormat{LaTeX2e}", r"\ProvidesPackage{pptx-theme}",
           r"\RequirePackage{iftex}", r"\RequireXeTeX", r"\RequirePackage{xeCJK}",
           r"\RequirePackage{tikz}",
           rf"\geometry{{papersize={{{width:.3f}mm,{height:.3f}mm}}}}",
           rf"\setbeamersize{{text margin left={width * margin:.3f}mm,text margin right={width * margin:.3f}mm}}"]
    for field, set_font, fallback, options in (
        ("latin_font", "setsansfont", "TeX Gyre Heros", ""),
        ("cjk_font", "setCJKsansfont", "FandolHei", "[BoldFont=FandolHei-Bold.otf]"),
    ):
        name = spec.get(field)
        fallback_name = "FandolHei-Regular.otf" if options else fallback
        command = rf"\{set_font}{options}{{{fallback_name}}}"
        if name:
            if not isinstance(name, str) or not all(c.isalnum() or c in " .-_()" for c in name):
                raise ValueError(f"Unsupported characters in {field}.")
            setting = "[AutoFakeBold]" if options else ""
            command = (rf"\IfFontExistsTF{{{name}}}{{\{set_font}{setting}{{{name}}}}}{{%" + "\n"
                       rf"  \PackageWarningNoLine{{pptx-theme}}{{{name} not found; using {fallback}}}%" + "\n"
                       rf"  {command}}}")
        sty.append(command)

    sty.extend(rf"\definecolor{{Pptx{key}}}{{HTML}}{{{colors[key]}}}"
               for key in ("accent", "text", "background", "on_accent"))
    sty.extend([r"\setbeamercolor{normal text}{fg=Pptxtext,bg=Pptxbackground}",
                r"\setbeamercolor{structure}{fg=Pptxaccent}",
                r"\setbeamercolor{itemize item}{fg=Pptxaccent}",
                r"\setbeamercolor{title}{fg=Pptxtext}",
                r"\setbeamertemplate{navigation symbols}{}",
                r"\setbeamerfont{frametitle}{series=\bfseries}",
                r"\setbeamertemplate{itemize items}[square]"])
    if header == "band":
        sty.append(r"\setbeamercolor{frametitle}{fg=Pptxon_accent,bg=Pptxaccent}")
    else:
        sty.append(r"\setbeamercolor{frametitle}{fg=Pptxtext}")
    if logo or footer == "number":
        logo_tex = rf"\includegraphics[width=.16\paperwidth,height=.045\paperheight,keepaspectratio]{{{logo}}}" if logo else ""
        number_tex = r"\scriptsize\insertframenumber" if footer == "number" else ""
        sty.append(r"\setbeamertemplate{footline}{\leavevmode"
                   rf"\hbox to \paperwidth{{\hskip.06\paperwidth\strut {logo_tex}\hfil {number_tex}\hskip.06\paperwidth}}"
                   r"\vskip.02\paperheight}")
    return font_size, "\n".join(sty) + "\n"


def render_frame(frame, labels, image, background, logo):
    layout = choice(frame, "layout", LAYOUTS)
    stage = tex(frame["stage"])
    title = tex(frame.get("title", frame["stage"]))
    body_label = labels["body"]
    image_box = (rf"\includegraphics[width=\linewidth,height=.4\paperheight,keepaspectratio]{{{image}}}"
                 if image else placeholder(labels["figure"], r".88\linewidth", ".28"))
    sample_bullets = [r"\begin{itemize}", rf"  \item {labels['point']}", rf"  \item {labels['evidence']}", r"\end{itemize}"]
    if layout == "cover":
        body = [rf"\title{{{title}}}", rf"\author{{{labels['author']}}}",
                rf"\date{{{labels['date']}}}", r"\begin{frame}[plain]", r"\titlepage"]
        if logo:
            body.insert(3, rf"\titlegraphic{{\includegraphics[width=.18\paperwidth,height=.09\paperheight,keepaspectratio]{{{logo}}}}}")
    elif layout == "divider":
        body = [r"\begin{frame}[plain]", r"\vfill", rf"{{\usebeamerfont{{title}}\color{{Pptxtext}}{title}\par}}",
                r"\smallskip\textcolor{Pptxaccent}{\rule{.22\linewidth}{1pt}}", r"\vfill"]
    else:
        body = [rf"\begin{{frame}}[t]{{{title}}}"]
        if frame.get("body_heading"):
            body.extend([rf"\textbf{{{tex(frame['body_heading'])}}}\par", r"\medskip"])
        if layout == "bullets":
            body.extend(sample_bullets)
        elif layout == "two-column":
            body.extend([r"\begin{columns}[T,onlytextwidth]", r"\column{.48\textwidth}", *sample_bullets,
                         r"\column{.48\textwidth}", r"\centering", image_box, r"\end{columns}"])
        elif layout == "figure":
            body.extend([r"\centering", image_box + r"\par", rf"\medskip {labels['caption']}"])
        elif layout == "formula":
            body.extend([r"\[ f(x) = ax + b \]", rf"{body_label}\par"])
        else:
            body.append(rf"{labels['summary']}\par")
    body.append(r"\end{frame}")
    if background:
        body = [r"\setbeamercolor{background canvas}{bg=}",
                rf"\usebackgroundtemplate{{\includegraphics[width=\paperwidth,height=\paperheight]{{{background}}}}}",
                *body]
    if background or layout == "cover":
        body = [r"\begingroup", *body, r"\endgroup"]
    pages = ", ".join(map(str, frame["reference_pages"])) or "none"
    return "\n".join([f"% {stage}; reference PPTX pages: {pages} (style only unless an asset is included)", *body])


def approved_files(slides, selected, source_sha):
    if any(not isinstance(asset, str) or not re.fullmatch(r"[plm][1-9]\d*:(?:\d+|bg)", asset) for asset in selected):
        raise ValueError("All asset references must be inventory IDs such as p2:4 or m1:bg.")
    folder = project_path(project_path(slides, "figures"), "pptx")
    if not folder.exists():
        if selected:
            raise ValueError("Extract the approved assets before generating.")
        return {}
    manifest = json.loads(project_path(folder, "manifest.json").read_text(encoding="utf-8"))
    if manifest["source_sha256"] != source_sha or {item["id"] for item in manifest["assets"]} != selected:
        raise ValueError("Extract exactly the assets used by the confirmed specification from this reference PPTX.")
    files = {}
    for item in manifest["assets"]:
        stem = item["id"].replace(":", "-")
        if item["path"] not in {f"{stem}.jpg", f"{stem}.png"}:
            raise ValueError(f"Invalid extracted asset filename: {item['path']}")
        if sha256(project_path(folder, item["path"])) != item["sha256"]:
            raise ValueError(f"Extracted asset changed: {item['path']}")
        files[item["id"]] = f"figures/pptx/{item['path']}"
    if {item.name for item in folder.iterdir()} != {"manifest.json", *(Path(path).name for path in files.values())}:
        raise ValueError("Unexpected files in the extracted asset folder. Review before delivery.")
    return files


def generate(root, spec):
    archive = project_path(root, ARCHIVE)
    report = json.loads(project_path(archive, "inventory.json").read_text(encoding="utf-8"))
    source_sha = sha256(project_path(archive, "original.pptx"))
    if spec["source_sha256"] != source_sha or report["sha256"] != source_sha:
        raise ValueError("The template specification must match the inspected PPTX SHA-256.")
    if not project_path(root, "outline.md").is_file():
        raise ValueError("Record the confirmed template design in outline.md before generating.")
    slides = project_path(root, "slides")
    main, style = project_path(slides, "main.tex"), project_path(slides, "pptx-theme.sty")
    if main.exists() or style.exists():
        raise ValueError("Template source already exists. Review or move it before generating again.")
    frames = spec["frames"]
    if not isinstance(frames, list) or not frames:
        raise ValueError("Specify at least one example frame.")
    labels = {key: tex(spec["labels"][key]) for key in ("author", "date", "body", "point", "evidence", "figure", "caption", "summary")}
    selected = set()
    layout_spec = spec["overall"]
    if layout_spec.get("logo"):
        selected.add(layout_spec["logo"])
    for frame in frames:
        layout = choice(frame, "layout", LAYOUTS)
        pages = frame["reference_pages"]
        if not isinstance(pages, list) or any(type(page) is not int or not 1 <= page <= len(report["slides"]) for page in pages):
            raise ValueError("reference_pages must contain 1-based PPTX page numbers (or be empty).")
        if frame.get("image") and layout not in {"figure", "two-column"}:
            raise ValueError("Frame images require figure or two-column layout.")
        if frame.get("logo") and layout != "cover":
            raise ValueError("Frame-specific logos require cover layout.")
        selected.update(frame[key] for key in ("image", "background", "logo") if frame.get(key))
    assets = approved_files(slides, selected, source_sha)
    font_size, sty = theme(layout_spec, report["canvas"], assets.get(layout_spec.get("logo")))
    pages_tex = [render_frame(frame, labels, *(assets.get(frame.get(field)) for field in ("image", "background", "logo")))
                 for frame in frames]
    main.write_text("\n\n".join([rf"\documentclass[{font_size}]{{beamer}}" + "\n" + r"\usepackage{pptx-theme}" + "\n" + r"\begin{document}",
                                 *pages_tex, r"\end{document}"]) + "\n", encoding="utf-8")
    style.write_text(sty, encoding="utf-8")
    return main


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("spec", type=Path, help="JSON specification compiled from the user's confirmed choices")
    args = parser.parse_args()
    try:
        root = project_directory(args.project)
        with project_lock(root):
            print(generate(root, json.loads(args.spec.read_text(encoding="utf-8"))))
    except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
        parser.exit(1, f"Beamer template generation failed: {error}\n")


if __name__ == "__main__":
    main()
