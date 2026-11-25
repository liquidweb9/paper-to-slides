# Source preparation

Run these examples from the skill directory or use the full script path. Paths for the inputs and talk directory are relative to the current working directory. The scripts require Python 3.11 or later. PDF processing uses PyMuPDF (`python -m pip install pymupdf`).

## Archive the talk inputs

```sh
python scripts/project_manager.py init "projects/example"
python scripts/project_manager.py import-sources "projects/example" --manuscript "paper.pdf"
```

- `--manuscript` accepts a local PDF, a local `.tex` entry file, a direct HTTP(S) PDF URL, an arXiv abstract URL, or an OpenReview forum URL. For arXiv, use a versioned URL when the version is known. For a DOI, publisher page, or project page, use `--paper-url` to record the official entry and locate the full-text PDF to pass as `--manuscript`. If the download requires sign-in or the response is a webpage, use an authorized local PDF. Confirm the manuscript version against the archived document and official record. `--version` records the identifier supplied by the caller.
- To preserve relative `\input`, bibliography, and figure paths, pass `--manuscript "paper-src/main.tex" --tex-root "paper-src"`. Point `--tex-root` at the directory that contains the complete source tree and put the talk directory outside it. The script archives the TeX sources for reading.
- Pass optional Markdown notes with `--notes "reading notes.md"` and additional local files or PDF URLs with repeatable `--supplement`. Include the available materials in one import. If a source is unavailable, omit its option and document any resulting gap in the outline. Import creates the project's `sources/` archive. Reuse it for the same source set and initialize another project directory when preparing a different source version.

`manifest.json` lists the original paths or URLs, the archived files, SHA-256 hashes, and the PDF reading indexes. Paths for archived files are relative to the manifest directory. For remote PDFs it records the final download URL and UTC download time. A LaTeX tree entry includes the SHA-256 of the entry file and a separate digest covering the copied tree.

Each archived PDF has a `reading.md` with one heading per 1-based PDF page position. Check `pages_without_text` for pages that need visual review or OCR. Use the PDF itself for formulas, table alignment, figures, and numbers. Distinguish the PDF page position from the page label printed on the manuscript.

## Inspect a page or crop a figure

```sh
python scripts/render_pdf_page.py "projects/example/sources/manuscript/original/paper.pdf" --page 7 --output "projects/example/source-review/page-07.png"
python scripts/render_pdf_page.py "projects/example/sources/manuscript/original/paper.pdf" --page 7 --crop 60 125 540 360 --dpi 300 --output "projects/example/slides/figures/figure-2.png"
```

The crop uses `X0 Y0 X1 Y1` in PDF points measured from the top-left of the displayed page (72 points per inch). The command prints JSON with the PDF page, crop, DPI, and output dimensions. In the outline or TeX comments, record the paper's figure or panel identifier as well as the PDF page position and crop bounds. When producing the deck, use a vector original or vector PDF crop where available.
