#!/usr/bin/env python3
"""Build and check a managed project's Beamer PDF with XeLaTeX."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from prepare_sources import tree_sha256
from project_manager import clean_build, project_directory, project_lock, project_path


BLOCKING_DIAGNOSTICS = (
    (re.compile(r"^(?:! |.+\.(?:tex|sty|cls|bbl):\d+: )"), "latex_error"),
    (re.compile(r"^Overfull \\[hv]box\b"), "overfull_box"),
    (re.compile(r"^Missing character:"), "missing_glyph"),
    (re.compile(r"Warning:.*\b(?:undefined|multiply defined)\b", re.IGNORECASE), "reference"),
    (re.compile(r"Warning:.*(?:may have changed|rerun)", re.IGNORECASE), "rerun_needed"),
)


def latex_diagnostics(log):
    issues = []
    for number, line in enumerate(log.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        for pattern, category in BLOCKING_DIAGNOSTICS:
            if pattern.search(line):
                issue = {"severity": "error", "kind": category, "log_line": number, "message": line}
                source_lines = re.search(r"\bat lines? (\d+(?:--\d+)?)", line)
                if source_lines:
                    issue["tex_lines"] = source_lines.group(1)
                issues.append(issue)
                break
        else:
            if re.search(r"^(?:LaTeX|Class \S+|Package \S+).*\bWarning:", line):
                issues.append({"severity": "warning", "kind": "latex_warning", "log_line": number, "message": line})
    return issues


def inspect_pdf(pdf, pages_dir):
    try:
        import pymupdf
    except ImportError as error:
        raise ValueError("PDF inspection requires PyMuPDF (python -m pip install pymupdf).") from error

    issues = []
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir()
    with pymupdf.open(pdf) as document:
        if not document.is_pdf or document.needs_pass or not document.page_count:
            raise ValueError(f"Expected a readable, nonempty PDF: {pdf}")
        for number, page in enumerate(document, start=1):
            page.get_pixmap(dpi=120).save(pages_dir / f"page-{number:03d}.png")
            # Extract with an unbounded clip so text drawn beyond the crop box is visible to the check.
            text = page.get_text("rawdict", clip=pymupdf.INFINITE_RECT(), flags=pymupdf.TEXTFLAGS_RAWDICT & ~pymupdf.TEXT_PRESERVE_IMAGES)
            bounds = page.rect * page.derotation_matrix
            bounds += (-1, -1, 1, 1)
            outside = []
            for block in text["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        chars = [char["c"] for char in span["chars"]
                                 if not char["c"].isspace() and not bounds.contains(pymupdf.Rect(char["bbox"]))]
                        if chars:
                            outside.append("".join(chars))
            if outside:
                issues.append({"severity": "error", "kind": "off_page_text", "pdf_page": number,
                               "message": "Text crosses the PDF page boundary", "sample": " ".join(outside)[:200]})
        return document.page_count, issues


def save_report(build, issues, page_count=0):
    passed = not any(issue["severity"] == "error" for issue in issues)
    report = {"automated_checks_passed": passed, "page_count": page_count,
              "review_pages": "pages/" if page_count else None, "issues": issues}
    report_path = project_path(build, "check.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(report_path)
    return passed


def check_build(build, slides):
    latex = project_path(build, "latex")
    pdf = latex / "main.pdf"
    log = latex / "main.log"
    published = build / "main.pdf"
    published.unlink(missing_ok=True)
    if not pdf.is_file() or not log.is_file():
        raise ValueError("No completed XeLaTeX build to check. Run the build command first.")
    fingerprint = build / "slides.sha256"
    if not fingerprint.is_file() or fingerprint.read_text(encoding="utf-8").strip() != tree_sha256(slides):
        return save_report(build, [{"severity": "error", "kind": "stale_build",
                                    "message": "Slide sources changed. Rebuild before checking the PDF."}])

    issues = latex_diagnostics(log)
    try:
        page_count, pdf_issues = inspect_pdf(pdf, project_path(build, "pages"))
    except (OSError, ValueError, RuntimeError) as error:
        issues.append({"severity": "error", "kind": "pdf_inspection", "message": str(error)})
        return save_report(build, issues)
    if not save_report(build, issues + pdf_issues, page_count):
        return False
    staged = project_path(latex, "checked.pdf")
    shutil.copyfile(pdf, staged)
    staged.replace(published)
    print(published)
    return True


def build_pdf(root, slides):
    clean_build(root)
    build = root / "build"
    build.mkdir()
    main = project_path(slides, "main.tex")
    if not main.is_file() or not (root / "outline.md").is_file():
        return save_report(build, [{"severity": "error", "kind": "missing_input",
                                    "message": "Expected outline.md and slides/main.tex. Build after outline approval."}])
    latexmk = shutil.which("latexmk")
    if not latexmk or not shutil.which("xelatex"):
        return save_report(build, [{"severity": "error", "kind": "missing_compiler",
                                    "message": "A TeX installation with latexmk and xelatex on PATH is required."}])

    latex = build / "latex"
    latex.mkdir()
    fingerprint = tree_sha256(slides)
    command = [latexmk, "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
               "-latexoption=-no-shell-escape", f"-outdir={latex}", "main.tex"]
    with (build / "compile.log").open("wb") as console:
        result = subprocess.run(command, cwd=slides, stdout=console, stderr=subprocess.STDOUT)
    log = latex / "main.log"
    if result.returncode or not (latex / "main.pdf").is_file() or not log.is_file():
        issues = latex_diagnostics(log) if log.is_file() else []
        issues.append({"severity": "error", "kind": "compile_failed", "exit_code": result.returncode,
                       "message": "XeLaTeX did not produce a complete PDF. See compile.log and latex/main.log."})
        return save_report(build, issues)
    (build / "slides.sha256").write_text(fingerprint + "\n", encoding="utf-8")
    return check_build(build, slides)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    try:
        root = project_directory(args.project)
        slides = project_path(root, "slides")
        with project_lock(root):
            passed = (build_pdf(root, slides) if args.command == "build"
                      else check_build(project_path(root, "build"), slides))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"PDF workflow failed: {error}\n")
    if not passed:
        parser.exit(1, "Automated PDF checks failed. See build/check.json.\n")


if __name__ == "__main__":
    main()
