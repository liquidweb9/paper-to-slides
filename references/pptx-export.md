# Export a slide PDF with speaker notes

Use the final slide PDF as the visual source. The exporter reads that PDF on each run. It needs Python 3.11+, PyMuPDF and python-pptx. Install missing Python packages with `python -m pip install pymupdf python-pptx`. Vector export also uses Poppler's `pdftocairo` on PATH. PowerPoint and LaTeX are optional for this step.

## Write the speaker notes

Read the actual pages in order. Adapt supplied presenter notes to those pages or draft the narration from the visible content and available verified material. Use the talk's language. For a method page, walk the audience through the decisive operation. For a result, tell them which comparison to look at and explain what it supports. Keep numbers, assumptions and interpretations consistent with the slide. A cover or transition usually needs only a short opening or bridge.

Save UTF-8 plain text as `speaker-notes.md` at the project root. The file begins with `## 1` and has one numbered section per physical PDF page, including overlays, cover and backup pages. The exporter puts only the text below each heading into the native PowerPoint notes field. Blank lines separate spoken paragraphs.

```markdown
## 1
今天我们讨论一个具体问题：怎样把多个客户端学到的低秩更新合并起来，同时保留每个客户端应有的权重？

## 2
先看这两个因子的乘积。我们只给其中一个因子乘上客户端权重。如果两边都乘，最终更新里出现的就是权重的平方。

大家可以用一个小数心算一下：权重取一半时，乘两次就只剩四分之一。
```

Keep the speaker's words free of source navigation, including phrases such as “原文第六页”, “见论文表 1”, “according to Eq. (11)”, source paths, or pasted evidence links. Say what the formula does or what the plotted quantities mean. Leave precise attribution in the approved outline or TeX comments. The exporter flags common Chinese and English locator patterns and reports the affected page. Read the notes once for natural speech and other locator phrasing the pattern check may miss.

## Run or repeat the export

From the skill directory, use project mode or pass the finished PDF directly.

```sh
python scripts/export_pptx.py "projects/example"
python scripts/export_pptx.py "revised slides.pdf" --notes "speaker-notes.md" --output "group meeting.pptx"
python scripts/export_pptx.py "revised slides.pdf" --format png --png-long-edge 3840 --output "group meeting PNG.pptx"
```

Project mode reads `build/main.pdf` and `speaker-notes.md` and writes `build/main.pptx`. Standalone mode accepts a manually compiled PDF in any directory. Its defaults are `speaker-notes.md` beside that PDF and a sibling PPTX with the PDF's basename. An explicit output directory must already exist.

After a LaTeX change, compile the new PDF, compare its pages with the numbered notes, and rerun the exporter. Reordering slides can change the mapping even if the page count stays the same. After a notes-only change, rerun just the export. Keep durable edits in the Markdown file, since rerunning the command replaces the generated deck.

By default each slide uses one SVG picture with a PNG fallback for viewers without SVG support. PDF text and vector graphics remain scalable. Text is converted to outlines so the viewer does not need the original fonts. Raster images already in the PDF retain the detail available in the source. Use `--format png` for a PNG-only deck. The fallback and PNG-only modes use a 3840-pixel long edge by default, equivalent to 3840 × 2160 on a 16:9 page. Set the long edge explicitly with `--png-long-edge`.

The first PDF page sets the canvas ratio. Pages with a different ratio are centered with margins so their full content remains visible. Before replacing the output, the script reopens the PPTX and checks the slide count, image bytes, SVG references, placement and speaker text in order. Inspect the resulting slides and notes together, including any overlays or pages whose order changed.
