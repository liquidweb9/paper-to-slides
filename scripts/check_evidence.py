#!/usr/bin/env python3
"""Check an outline's local source links against the imported manuscript and supplements."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote

from prepare_sources import sha256, tree_sha256
from project_manager import project_directory


# Inline Markdown links. Angle brackets support filenames with spaces or parentheses.
SOURCE_LINK = re.compile(r"\]\((?:<(sources/[^>\n]+)>|(sources/[^\s)]+))\)")
SLIDE_HEADING = re.compile(r"### (S[0-9]+)(?:\s+.*)?")
EXEMPTION = re.compile(r"Evidence-exempt:\s+(cover|illustrative)\s+[-–—]\s+\S.+")


def check_evidence(root):
    archive = (root / "sources").resolve(strict=True)
    manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
    manuscript = manifest.get("manuscript")
    if not manuscript:
        raise ValueError("Import a full manuscript before checking paper evidence.")
    sources = {}
    tex_tree = None
    issues = []
    for entry in [manuscript, *manifest["supplements"]]:
        path = (archive / entry["archived_path"]).resolve(strict=True)
        if not path.is_relative_to(archive):
            raise ValueError(f"Source path outside archive: {path}")
        sources[path] = entry
        if sha256(path) != entry["sha256"]:
            issues.append(f"Archived file changed: {path}")
    primary = (archive / manuscript["archived_path"]).resolve()
    if "tex_tree_sha256" in manuscript:
        tex_tree = (archive / "manuscript" / "tex").resolve(strict=True)
        if not tex_tree.is_relative_to(archive) or tree_sha256(tex_tree) != manuscript["tex_tree_sha256"]:
            issues.append("Archived manuscript TeX tree changed.")

    primary_cited = False
    checked = 0
    slide = None
    slides = {}
    outline = (root / "outline.md").read_text(encoding="utf-8-sig")
    for number, line in enumerate(outline.splitlines(), start=1):
        heading = SLIDE_HEADING.fullmatch(line.strip())
        if heading:
            slide = heading[1]
            if slide in slides:
                issues.append(f"outline.md:{number}: duplicate slide ID {slide}")
            slides[slide] = {"cited": False, "exempt": False}
        elif re.match(r"#{1,3}\s", line):
            slide = None
        if slide and EXEMPTION.fullmatch(line.strip()):
            slides[slide]["exempt"] = True
        for match in SOURCE_LINK.finditer(line):
            target = match.group(1) or match.group(2)
            file, separator, anchor = target.partition("#")
            if not separator:
                continue  # A link to the whole paper may coexist with precise citations.
            path = (root / unquote(file)).resolve()
            in_tree = tex_tree is not None and path.is_relative_to(tex_tree)
            entry = sources.get(path)
            page = re.fullmatch(r"page=([1-9][0-9]*)", anchor)
            lines = re.fullmatch(r"L([1-9][0-9]*)(?:-L([1-9][0-9]*))?", anchor)
            if entry and page and 1 <= int(page[1]) <= entry.get("page_count", 0):
                pass
            elif (in_tree or entry) and path.suffix.lower() in {".tex", ".ltx", ".sty"} and lines and path.is_file():
                with path.open("rb") as stream:
                    count = sum(1 for _ in stream)
                if not int(lines[1]) <= int(lines[2] or lines[1]) <= count:
                    issues.append(f"outline.md:{number}: line range outside {count} source lines: {target}")
                    continue
            else:
                issues.append(f"outline.md:{number}: unknown source or invalid PDF page / TeX line: {target}")
                continue
            checked += 1
            if slide:
                slides[slide]["cited"] = True
            primary_cited |= path == primary or in_tree
    if not slides:
        issues.append("Use '### S01 Title' headings to identify the slides in outline.md.")
    for slide, coverage in slides.items():
        if not any(coverage.values()):
            issues.append(f"{slide}: missing a valid source locator or an explicit evidence exemption.")
    if not primary_cited:
        issues.append("Add a precise manuscript link to outline.md using #page=N or #Lstart-Lend.")
    return checked, issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    try:
        count, issues = check_evidence(project_directory(args.project))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Evidence check failed: {error}\n")
    if issues:
        parser.exit(1, "\n".join(issues) + "\n")
    print(f"Archive hashes and {count} source locator(s) checked. Compare each claim with the cited material.")


if __name__ == "__main__":
    main()
