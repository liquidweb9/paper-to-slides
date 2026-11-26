# Paper to Slides

[简体中文](README.md) · **English**

Turn research papers into technical presentations for lab meetings, paper discussions, or journal clubs. Build a Beamer deck from a paper, design a reusable LaTeX template from a reference PPTX, or export an existing slide PDF to PowerPoint with native speaker notes. [Preview the default 16:9 Beamer template](template/template.pdf).

## Quick start: Use an agent

Open the **repository root** in your client. The commands are scoped to the repository and do not need to be installed in your home directory. In Claude Code, Antigravity, and OpenCode, use the `/command-name` forms below. In Codex, type `$` and select the skill with the same name, for example `$slides-init "projects/my-talk"`.

| Command | Example or purpose |
| --- | --- |
| `/paper-to-slides` | `/paper-to-slides "paper.pdf" --project "projects/my-talk"`: approve the slide outline, then build LaTeX and PDF. |
| `/pptx-to-template` | `/pptx-to-template "reference.pptx" --project "projects/my-template"`: confirm layouts and assets, then generate a template. |
| `/pdf-to-pptx` | `/pdf-to-pptx "my-slides.pdf" --notes "speaker-notes.md"`: preserve page order and export native notes. |
| `/slides-init` | `/slides-init "projects/my-talk"`: initialize a project. |
| `/slides-import` | `/slides-import "projects/my-talk" --manuscript "paper.pdf"`: archive source materials. |
| `/slides-build` | `/slides-build "projects/my-talk"`: recompile existing LaTeX sources. |
| `/slides-check` | `/slides-check "projects/my-talk" --mode pdf`: check the PDF build; use `evidence` for source links or `both` for both checks. |
| `/pdf-crop` | `/pdf-crop "paper.pdf" --page 7 --output "page-07.png"`: render a page, or add `--crop` to select a region. |
| `/slides-status` | `/slides-status "projects/my-talk"`: see which project files and outputs exist. |
| `/slides-clean` | `/slides-clean "projects/my-talk"`: remove only `build/`. |
| `/slides-delete` | `/slides-delete "projects/my-talk"`: remove the entire project after confirmation. |

See the [command reference (Chinese)](references/agent-commands.md) for arguments and client-specific details. You can also run the Python commands below from the repository root. The presenter or agent writes the outline, LaTeX content, and speaker notes.

## Requirements

| Task | Dependencies |
| --- | --- |
| Run the scripts | Python 3.11 or later |
| Index, render, or inspect PDFs | PyMuPDF |
| Inspect a reference PPTX and extract approved images | python-pptx. A PDF exported from PowerPoint is helpful for visual comparison. |
| Build a Beamer PDF | `latexmk`, `xelatex`, and the Beamer, xeCJK, unicode-math, and TikZ packages |
| Export PPTX | PyMuPDF and python-pptx. Default SVG export also requires Poppler's `pdftocairo`. |

```sh
python -m pip install pymupdf python-pptx
python --version
latexmk -v
xelatex --version
pdftocairo -v
```

Put the tools you need on `PATH`. A standalone PDF-to-PPTX export does not require TeX. The default theme uses Times New Roman for Latin text, SimSun for Chinese body text, and SimHei for Chinese cover text. If a font is unavailable, the theme substitutes TeX Gyre Termes or Fandol and records it in the build log.

## Start from a paper

### 1. Create a project and archive materials

Keep the original PDF outside the managed project directory, for example as `paper.pdf` at the repository root, or pass its absolute path. Use a new or empty directory for the project.

```sh
python scripts/project_manager.py init "projects/my-talk"
python scripts/project_manager.py import-sources "projects/my-talk" --manuscript "paper.pdf"
python scripts/project_manager.py status "projects/my-talk"
```

The import copies materials into `sources/`, records SHA-256 hashes, and indexes PDF text by page. Keep the archive read-only. Verify formulas, figures, and unclear extracted text against the original page, and save working crops to `source-review/` or `slides/figures/`.

`--manuscript` also accepts a direct PDF URL, an arXiv abstract URL, an OpenReview forum URL, or a local TeX entry point. Use `--paper-url` for the official link, `--version` for the verified version, `--notes` for reading notes, and repeat `--supplement` as needed. For a complete TeX tree, pass `--tex-root` to preserve relative paths. Import each source set together and use a separate project for a different manuscript version. See [source preparation and figure cropping](references/source-preparation.md).

### 2. Write and approve an evidence-backed outline

In `outline.md`, record the manuscript version, audience, talk objective, and each slide's section title, body heading, content, and evidence. The default sequence is **main problem → contributions → prerequisites → method → experiments → summary and discussion**.

- Reuse the section title across consecutive slides and give each slide a heading that names its specific point. Keep the contributions on one slide.
- When the method has a meaningful sequence, start with an overview diagram. Put formulas, derivations, and examples next to the steps they explain.
- Introduce datasets, settings, metrics, and baselines before discussing numbers. Keep attributions in the outline or TeX comments and preserve the axes, units, and legends needed to read the figures.
- Close with what the evidence supports and one concrete follow-up direction.

Use precise links such as `[Eq. (2)](sources/manuscript/original/paper.pdf#page=3)` for reported values, equations, and central claims. PDF page numbers are one-based.

```sh
python scripts/check_evidence.py "projects/my-talk"
```

The script checks archive hashes and locators; compare the claims themselves with the cited materials. Label any worked examples you create as illustrative. The [agent workflow](SKILL.md) requires explicit approval of the current outline before authoring or building slides. See [evidence review and discussion](references/evidence-review.md).

### 3. Build and review the PDF

Copy [`template/template.tex`](template/template.tex) to `slides/main.tex` and [`template/template.sty`](template/template.sty) alongside it. Replace the example frames with the approved content and reference local styles and figures by relative path.

```sh
python scripts/build_pdf.py build "projects/my-talk"
python scripts/build_pdf.py check "projects/my-talk"
```

`build` runs XeLaTeX via `latexmk`, checks the logs and PDF, and renders page previews. A passing PDF is published as `build/main.pdf`. `check` rechecks the existing build and detects changes to `slides/` since compilation.

Read `build/check.json` and inspect each preview under `build/pages/` for overlap, cropping, and readability. Automated checks detect problems such as overfull boxes, missing glyphs, unresolved references, and off-page text. Failed builds leave diagnostics in `build/compile.log` and, when available, `build/latex/main.log`. Rebuilding recreates `build/`; export any previously generated PPTX again afterwards.

## Design a template from a reference PPTX

Use `/pptx-to-template` (Codex: `$pptx-to-template`). The agent inventories the actual pages, layouts, masters, and candidate objects, then asks in three rounds:

1. **Overall layout:** aspect ratio, spacing, typography, colors, titles, and footers.
2. **Layouts by stage:** which pages to reference for the cover, method, results, and other stages, and which regions to leave editable as placeholders.
3. **Asset reuse:** for each candidate, recreate the style, reuse the specified original in an agreed scope, or use a placeholder or omit it.

After you approve the design, the workflow delivers `slides/main.tex`, a local theme, and a PDF preview. Selecting a reference page does not authorize copying its contents. A template project does not require a manuscript, and the generated template can compile without the original PPTX. The extraction script supports approved embedded PNG and JPEG images; complex charts or vector assets may need manual work. See the [PPTX template workflow (Chinese)](references/pptx-template.md) for inspection, selective extraction, and generation commands.

## Export PowerPoint with native speaker notes

Write a UTF-8 `speaker-notes.md` with a numbered `## N` section for each physical PDF page, including the cover and pages produced by Beamer overlays. Write notes to be spoken; keep exact evidence locators in the outline or TeX comments.

```markdown
## 1
When does averaging low-rank updates across clients introduce error?

## 2
First average the two factors separately. Multiplying those averages introduces cross-client terms.
```

To export `build/main.pdf` and the project-root notes as `build/main.pptx`:

```sh
python scripts/export_pptx.py "projects/my-talk"
```

To export a standalone slide PDF, including one compiled outside the project:

```sh
python scripts/export_pptx.py "my-slides.pdf" --notes "speaker-notes.md" --output "my-slides.pptx"
```

By default, each slide contains one SVG image with a lossless PNG fallback. Vector text, equations, and line art remain scalable paths; the projected content is an image, while the notes are editable in PowerPoint. Edit the LaTeX source to change the slide content or layout. The fallback has a default long edge of 3840 pixels (3840 × 2160 at 16:9). For PNG-only export:

```sh
python scripts/export_pptx.py "my-slides.pdf" --notes "speaker-notes.md" --format png --png-long-edge 3840 --output "my-slides-png.pptx"
```

The exporter verifies slide count, images, placement, SVG references, and notes. Compare the result with the PDF in your target viewer. Update the notes when page order changes. If you edit only the notes, rerun just the export. See the [PPTX export guide](references/pptx-export.md).

## Project layout and cleanup

```text
projects/my-talk/
├── .paper-to-slides          Managed-project marker
├── sources/                  Archived papers, notes, supplements, and manifest.json
├── template-source/          Reference PPTX and inventory for template projects
├── template-spec.json        Optional generator configuration for template projects
├── outline.md                Slide outline with evidence links, or template design
├── speaker-notes.md          Notes in PDF page order
├── source-review/            Optional source screenshots and crops
├── slides/
│   ├── main.tex              Beamer entry point
│   ├── *.sty                 Local theme
│   └── figures/              Figures used by the slides
└── build/
    ├── main.pdf              PDF that passed automated checks
    ├── main.pptx             Optional PowerPoint export
    ├── check.json            Automated check report
    ├── compile.log           latexmk output
    ├── latex/                Intermediate files and XeLaTeX log
    └── pages/                Page previews
```

Use `clean` to discard build outputs only. Use `delete --yes` only when you intend to remove the entire managed project, including its archive, outline, slide sources, and notes.

```sh
python scripts/project_manager.py clean "projects/my-talk"
python scripts/project_manager.py delete "projects/my-talk" --yes
```

Git ignores `projects/`, which keeps source materials and generated decks local. Share the PDF, PPTX, notes, or a copy of the LaTeX sources with their local styles and figures as needed. See the [project workflow](references/project-workflow.md).
