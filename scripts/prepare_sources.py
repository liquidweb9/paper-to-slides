#!/usr/bin/env python3
"""Archive paper inputs and create a page-indexed reading copy for each PDF."""

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def tree_sha256(root):
    files = {file.relative_to(root).as_posix(): sha256(file)
             for file in sorted(root.rglob("*")) if file.is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode("utf-8")).hexdigest()


def pdf_url(url):
    parsed = urlsplit(url)
    if parsed.hostname in {"arxiv.org", "www.arxiv.org"} and parsed.path.startswith("/abs/"):
        return parsed._replace(path=parsed.path.replace("/abs/", "/pdf/", 1), fragment="").geturl()
    if parsed.hostname in {"openreview.net", "www.openreview.net"} and parsed.path == "/forum":
        if parse_qs(parsed.query).get("id"):
            return parsed._replace(path="/pdf", fragment="").geturl()
    return url


def download_pdf(url, target):
    request = Request(pdf_url(url), headers={"User-Agent": "paper-to-slides/1.0"})
    with urlopen(request, timeout=30) as response:
        header = response.read(1024)
        if b"%PDF-" not in header:
            raise ValueError(f"{url} did not return a PDF. Resolve the full-text PDF URL or supply a local copy.")
        with target.open("wb") as stream:
            stream.write(header)
            shutil.copyfileobj(response, stream)
        return response.geturl()


def pdf_index(path, reading_path):
    try:
        import pymupdf
    except ImportError as error:
        raise ValueError("PDF processing requires PyMuPDF (python -m pip install pymupdf).") from error

    pages_without_text = []
    with pymupdf.open(path) as document:
        if not document.is_pdf or document.needs_pass or not document.page_count:
            raise ValueError(f"Expected a readable PDF with at least one page: {path.name}")
        with reading_path.open("w", encoding="utf-8") as stream:
            stream.write("# Extracted PDF text\n\nHeadings give 1-based PDF page positions. "
                         "Check formulas, tables, and figures against the PDF.\n")
            for number, page in enumerate(document, start=1):
                page_text = page.get_text(sort=True).strip()
                stream.write(f"\n## PDF page {number}\n\n")
                if not page_text:
                    pages_without_text.append(number)
                    page_text = "[No extractable text. Inspect the page image.]"
                stream.write(page_text + "\n")
        metadata = document.metadata or {}
        return {
            "page_count": document.page_count,
            "metadata": {key: metadata[key] for key in ("title", "author") if metadata.get(key)},
            "pages_without_text": pages_without_text,
        }


def archive(root, slot, value, tex_root=None):
    directory = root / slot
    directory.mkdir(parents=True)
    origin = {}
    if value.startswith(("https://", "http://")):
        stored = directory / "original.pdf"
        origin = {"input_url": value, "resolved_pdf_url": download_pdf(value, stored),
                  "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    else:
        source = Path(value).resolve(strict=True)
        if not source.is_file():
            raise ValueError(f"Expected a file: {source}")
        origin["original_path"] = str(source)
        if tex_root:
            origin["original_tex_root"] = str(tex_root)
            tree = directory / "tex"
            shutil.copytree(tex_root, tree, ignore=shutil.ignore_patterns(".git"))
            stored = tree / source.relative_to(tex_root)
            origin["tex_tree_sha256"] = tree_sha256(tree)
        else:
            stored = directory / "original" / Path(value).name
            stored.parent.mkdir()
            shutil.copyfile(source, stored)

    entry = {**origin, "archived_path": stored.relative_to(root).as_posix(), "sha256": sha256(stored)}
    if stored.suffix.lower() == ".pdf":
        reading = directory / "reading.md"
        entry.update(pdf_index(stored, reading))
        entry["reading_path"] = reading.relative_to(root).as_posix()
    return entry


def prepare(args):
    destination = args.output_dir.resolve()
    if destination.exists():
        raise ValueError(f"Output already exists: {destination}. Choose a new directory for a new source set.")
    if not any((args.manuscript, args.notes, args.paper_url, args.supplement)):
        raise ValueError("Provide at least one source.")
    if args.paper_url:
        parsed = urlsplit(args.paper_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("--paper-url requires an HTTP(S) link.")
    if args.notes:
        if args.notes.startswith(("http://", "https://")) or Path(args.notes).suffix.lower() not in {".md", ".markdown"}:
            raise ValueError("--notes requires a local Markdown file (.md or .markdown).")
    tex_root = None
    local_manuscript = args.manuscript and not args.manuscript.startswith(("http://", "https://"))
    if local_manuscript and Path(args.manuscript).suffix.lower() not in {".pdf", ".tex"}:
        raise ValueError("--manuscript requires a PDF, a LaTeX entry file, or a paper PDF URL.")
    if args.tex_root:
        if not local_manuscript or Path(args.manuscript).suffix.lower() != ".tex":
            raise ValueError("--tex-root requires a local .tex manuscript entry file.")
        tex_root = args.tex_root.resolve(strict=True)
        if not tex_root.is_dir() or not Path(args.manuscript).resolve().is_relative_to(tex_root):
            raise ValueError("--tex-root must be a directory containing the .tex entry file.")
        if destination.is_relative_to(tex_root):
            raise ValueError("Choose an output directory outside --tex-root.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".paper-sources-", dir=destination.parent) as temp:
        root = Path(temp) / "sources"
        root.mkdir()
        manifest = {
            "paper_url": args.paper_url,
            "manuscript_version": args.version,
            "manuscript": archive(root, "manuscript", args.manuscript, tex_root) if args.manuscript else None,
            "notes": archive(root, "notes", args.notes) if args.notes else None,
            "supplements": [archive(root, f"supplements/{index:02d}", value)
                            for index, value in enumerate(args.supplement, start=1)],
        }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        root.rename(destination)
    return destination / "manifest.json"


def add_source_arguments(parser):
    parser.add_argument("--manuscript", help="Local PDF, .tex entry file, direct PDF URL, arXiv abstract or OpenReview forum URL")
    parser.add_argument("--tex-root", type=Path, help="Copy this LaTeX source tree, preserving paths to included files and figures")
    parser.add_argument("--notes", help="Local presenter notes (.md or .markdown)")
    parser.add_argument("--paper-url", help="Official paper or project URL to record")
    parser.add_argument("--version", help="Verified version identifier, e.g. arXiv:2401.01234v2")
    parser.add_argument("--supplement", action="append", default=[], help="Local supplemental file or PDF URL (repeatable)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path, help="New archive directory, e.g. projects/my-talk/sources")
    add_source_arguments(parser)
    args = parser.parse_args()
    try:
        print(prepare(args))
    except (HTTPException, OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Source preparation failed: {error}\n")


if __name__ == "__main__":
    main()
