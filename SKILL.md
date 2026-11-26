---
name: paper-to-slides
description: >-
  Prepare technical LaTeX Beamer slides for a paper discussion, lab meeting,
  journal club, or research group presentation from the original manuscript,
  with optional presenter notes and a paper link. Build a source-backed slide-by-slide outline
  for user approval, then deliver Beamer source and PDF with an optional
  vector-first PPTX with speaker notes. Also export an existing slide PDF to
  PowerPoint with per-page presenter notes. When a user supplies a reference
  PPTX to design a reusable LaTeX Beamer template, ask them to choose the deck
  layout, frame types by presentation stage, and original assets to reuse.
---

# Paper to Slides

Turn the supplied paper materials into a technically substantial group presentation with a review of the slide outline before production.

- To design a reusable LaTeX Beamer template from a **reference PPTX**, go directly to [PPTX → Beamer template](references/pptx-template.md). Inspect the deck and ask the staged design questions before generating LaTeX. No manuscript is needed for a blank or sample template. If the user also requests a paper talk, confirm the template design and then follow the paper workflow below in a separate talk project, including its evidence-backed outline review. Use the selected local theme instead of the default one.
- To convert an existing **slide PDF** to PowerPoint, go directly to [PPTX export](references/pptx-export.md). Treat the supplied slide order and content as final for this conversion. Use the same route after the presenter manually revises LaTeX and generates a new PDF.

## 1. Collect and verify sources

Use [`scripts/project_manager.py`](scripts/project_manager.py) to initialize the talk directory named by the user, or `projects/<talk>` under the current workspace by default. Use the same directory for subsequent commands. Keep archived source files under `sources/`, the approved plan at `outline.md`, authored slides under `slides/`, and generated outputs under `build/`. See [project workflow](references/project-workflow.md) for the directory layout and commands.

A readable full manuscript is sufficient to start. Accept a local PDF, a complete TeX source, or a link from which the full text can be retrieved. Use supplied notes and official links when available. If only an abstract, notes, or slides are available, ask for the full paper before attributing methods, equations, or results to it. For a request explicitly limited to an abstract, identify that scope.

| Input | Use |
| --- | --- |
| Original manuscript (PDF or complete LaTeX source) | Verify definitions, assumptions, equations, algorithms, results, and stated limitations against the version being presented. Prefer matching TeX for equation transcription. Check PDF page images for extracted math, table alignment, and figure details when needed. |
| Presenter's Markdown notes (`.md`) | Preserve the requested emphasis, questions, and interpretations. Label the presenter's interpretation when it goes beyond the paper's evidence. |
| Paper link (DOI, arXiv, publisher page, or official project page) | Verify the version and locate official figures, author demos, appendices, and other supporting material. Record the URL and section or asset. |
| Optional materials | Ask for relevant supplements, figures, or reference slides as needed, and invite the user to specify the audience, duration, or emphasis. |

Run `project_manager.py import-sources` to copy the inputs into `sources/`, index PDF text by page, and record provenance in `sources/manifest.json`. Read from the archive and write any derived figures or edits to the working directories. Check the title, authors, and version against the title page or matching official record. Record the identity as printed and an official link if available. Use a preprint identifier or manuscript date when publication details are unconfirmed. Resolve mismatches before combining a paper, supplement, or notes. See [source preparation](references/source-preparation.md) for PDF links, complete LaTeX source trees, and figures.

Treat extraction errors and OCR guesses as unresolved until checked against the original. Track important claims at the level of the equation, figure, table, section, or page. Match an experimental number to its condition, metric, baseline, and unit. Flag material differences between sources with both locators in the outline or source comments. Work within the supplied sources by default and add external context only when requested.

---

## 2. Write and review the outline

Write `outline.md` in the requested presentation language, defaulting to the user's language. State the paper identity, intended audience, talk objective, scope, and requested duration if known. Organize the talk around the research question and the paper's argument. Fit the main talk to the audience and available time.

### Main-talk sequence

Use the six sections below in order after any cover. In the outline, record the projected page title and the first-level heading in the slide body separately. The page title tells the audience which section they are in. The body heading names the concept, operation, or comparison on that slide. Reuse the same page title across consecutive slides in a section. Start the main talk with a dedicated problem slide and end with one summary and discussion slide. Fit the depth to the audience and duration, and follow any order or scope the user requests.

1. **Main problem (主要问题).** State the question before presenting the solution. Explain the setting, what current approaches leave unresolved, and which constraint makes the problem difficult. Give a concrete failure case or trade-off where the source supports it.
2. **Paper contributions (论文贡献).** Use this page title on a single slide and list the contributions directly in the body. Identify what the authors add, which part of the problem each contribution addresses, and which techniques they reuse.
3. **Prerequisites (前置知识).** Reuse this page title. Give each slide a body heading naming the concept, such as “LoRA” or “联邦聚合”. Introduce the minimum notation, baselines, and assumptions needed for the method, in the order they will be used.
4. **Paper's method (论文方案).** Open the section with a method overview and a flowchart when the method has a meaningful sequence, set of actors, or data flow. Label the steps, inputs, outputs, and decision points. Keep the same page title on subsequent slides and reuse the diagram's step names as body headings in the same order. Carry the relevant output of one step into the next, using the same notation and, where helpful, the same running example. Place each explanation, derivation, and worked example alongside the step it explains. Put a theorem and its assumptions next to the operation or claim they justify.
5. **Experiments (实验).** Use this page title throughout the section. A short qualifier such as “实验｜消融” can distinguish a group of slides. Use body headings for the setup, dataset, metric, comparison, or result. Tie each result back to the method step or claim it tests. Introduce relevant baselines and conditions before interpreting numbers. Include the most informative ablation or failure case available. For a paper without experiments, cover the relevant evidence in its place.
6. **Summary and discussion (总结与讨论).** Use this page title on the closing slide. Under one first-level body heading, write one compact paragraph in a smaller, readable body size. First describe what the paper did and what the evidence supports. Then state a concrete extension, follow-up comparison, or application that builds on the paper. Close with that direction as a declarative sentence. Omit standalone discussion prompts and labels such as “组会提案”.

Place substantive material in the main talk where it is needed. Integrate derivation caveats and implementation details with the matching method step, and sensitivity results with the relevant experiment. Include standalone backup slides only when the user asks for them.

For example, in a FedRot-LoRA talk, three successive frames can all have the page title “论文方案” and the body headings “一轮联邦训练的流程”, “求解硬对齐旋转”, and “将硬旋转软化后上传”. Carry the fitted rotation from the second frame into the interpolation on the third. Explain the SVD projection direction there and introduce the rank and heterogeneity results with the MNLI experiments. When revising an existing deck, use its informative page titles as starting points for body headings and map each former backup topic to the slide that uses it.

### Per-slide plan and review

| Per-slide field | What to record |
| --- | --- |
| ID, page title, and body heading | Stable ID, shared section title, and specific first-level body heading where applicable. The cover and the single contributions slide can go directly to their content. For method slides, record the matching flowchart step and how the slide connects to the one before it. |
| Audience takeaway | The specific point the audience should understand after this slide. |
| Content and explanation | The reasoning the speaker will cover. For method slides, name inputs, outputs, assumptions, symbols, and the role of each key term or step. For result slides, name the comparison, values, and what the evidence supports. |
| Math dependencies and examples | Identify which earlier formula belongs in the upper-right recap, the key derivation steps to show, and any worked example with its inputs, intermediate steps, and output. |
| Evidence and assets | Record exact source locators for factual claims, equations, and results. For visuals, specify the original paper or webpage, the figure or panel to crop, and what the audience should learn from it. Mark unavailable assets and ask for the original or an alternate source before relying on them. |

Follow the [evidence and discussion guide](references/evidence-review.md) when writing the per-slide plan. Put clickable manuscript locators beside substantive claims in `outline.md`, then run [`scripts/check_evidence.py <talk-directory>`](scripts/check_evidence.py) before sharing it. For each central result, plan how the speaker will explain the comparison or proof step and its scope. Use the evidence to develop the concrete follow-up direction for the final slide. Mark unresolved items beside affected slides and omit unsupported numbers or claims.

**Blocking outline review.** Share `outline.md`, call out any material gaps, and ask the user to approve it or request changes. Stop before authoring or editing Beamer slide code, compiling a deck, or exporting slides. Revise the outline in response to feedback and wait for explicit approval of the version to be built. A request to make the presentation or silence does not approve the outline. On resume, require an explicit approval in the conversation or an outline the user explicitly identifies as already approved.

---

## 3. Build the approved Beamer deck

Use the approved outline for slide order, scope, and evidence. Choose layout details during authoring. Return material changes to the outline for review, such as replacing key evidence, omitting a planned technical step, or changing the slide roster.

Write a rebuildable `slides/main.tex` with relative links to local figures and any other required source files. By default, copy [`template/template.tex`](template/template.tex) to `slides/main.tex` and place [`template/template.sty`](template/template.sty) alongside it. Replace the teaching frames and template-guidance appendix with the approved slide order and content. The template uses a 16:9 white canvas, orange and light-blue cover bands and square bullets, Times New Roman Latin text, SimHei cover Chinese, and SimSun content Chinese. Use `\PaperTalkTitleFrame` for the cover, `\author` for the paper authors, `\date` for the venue and year, and normal Beamer `frame` and `itemize` environments for body slides. Use the theme's 28 bp default body text or `\PaperTalkBodySize{24}` / `\PaperTalkBodySize{20}` where the layout needs denser text. The theme requires XeLaTeX and substitutes TeX Gyre Termes or Fandol when an original font is unavailable. Report any substitution. Use a different theme or aspect ratio when requested. The fixed `template/` directory also contains the compiled [preview PDF](template/template.pdf).

### Write for the room

Use the template and its preview for typography, spacing, and math layouts. For titles, closing-slide format, and placement of supporting material, apply the main-talk sequence above when replacing the template examples. Use discussion questions from the evidence guide to develop a specific follow-up direction for the closing paragraph.

Use the approved section title as the Beamer frame title. Put the page-specific topic in a visually subordinate first-level heading in the slide body where the outline calls for one. Put takeaways in the body or in captions where they help interpret the evidence. Keep figure and table credits, author and venue attributions for borrowed assets, source links and locators, and verification notes in `outline.md` or non-rendered TeX comments. Use projected captions for information needed to read the visual, such as the metric, condition, or comparison. Keep the original axes, units, legends, and labels.

### Lay out formulas, derivations, and examples

- **Make the main math readable at presentation size.** Use display math and shared macros for recurring notation. Define symbols at first use, align related lines with `align` or `split`, and use spacing and emphasis to guide the eye. Split dense content across slides rather than shrinking the formulas until they fit.
- **Recall dependencies beside the title.** If understanding the current slide requires an earlier formula, repeat only the necessary expression with `\PaperTalkFormulaRecap[Earlier formula]{$\Delta W=BA$}` immediately after the frame title. The command places a narrow recap box to the right of the title, within the header, without adding a separate body row. Keep the current formula or derivation visually primary. If a recap is too long, keep only the relevant terms or split it into short lines. If native LaTeX typesetting is impractical, pass a cropped vector PDF (or a sharp equation image) to the same command with `\includegraphics[width=\linewidth,height=26bp,keepaspectratio]{...}`; keep the editable formula source and asset locally.
- **Derive key formulas on the slides.** Start from the definitions or assumptions, show the consequential intermediate equalities, inequalities, or substitutions, and explain why each non-obvious step holds and what the result means. When supplying a missing algebraic step, verify it from the stated assumptions. Do not present an illustration or heuristic as the paper's proof.
- **Work through difficult formulas or procedures.** Pick a small numeric, symbolic, or concrete example with the same notation as the method. Show the initial inputs or state, each decisive substitution or transition, the intermediate results, and the output and intuition. Label an example created for the talk as illustrative so it is not mistaken for a reported experiment.

### Capture figures and compile

Inspect the crop itself for a printed source line or surrounding publication caption. Retain the plot, panels, axes, units, legends, and any conditions needed to interpret them. Record provenance in the outline and TeX comments, including when the visible slide uses a redrawn figure.
Extract or crop illustrations, experiment plots, and table panels from the original paper or its official webpage or supplement. Prefer original vector assets or a vector PDF crop. Use [`scripts/render_pdf_page.py`](scripts/render_pdf_page.py) when checking a PDF page visually or making a PNG crop. Preserve the axes, units, legends, labels, and context needed to read the image. Record the exact provenance in the outline or TeX comments. Ask for an alternate source only when a needed asset is missing. If it remains unavailable, use other verified evidence or flag the gap and agree on any material change through the outline review.

Run [`scripts/build_pdf.py`](scripts/build_pdf.py) with `build <talk-directory>` to compile `slides/main.tex` via `latexmk` and XeLaTeX, check the logs and PDF, and render each page for review. Treat archived LaTeX as reading material. See [project workflow](references/project-workflow.md) for the generated files and failure handling.

---

## 4. Verify and deliver

Read `build/check.json` and inspect every image under `build/pages/`. Resolve formula or frame overflow, unresolved references or citations, missing glyphs, and content outside the page. For a wide expression, split it at meaningful terms with `aligned` or `split`, shorten a recap to the terms used on the slide, or divide the derivation across frames. Check for clipping and overlap even when the automated checks pass. Rerun the outline evidence check. With the rendered deck and original pages side by side, verify every reported value, paper equation, theorem, figure caption, and substantive conclusion, including those in the appendix. Recompute presenter-derived values. Correct the deck and rebuild after any change. The [evidence and discussion guide](references/evidence-review.md) gives a worked example.

Read the projected page titles and body headings in order. Check that consecutive pages retain their section title, the method headings follow the flowchart, each experiment connects to the method or claim it evaluates, and the closing paragraph connects the paper's findings to a concrete follow-up direction. Confirm that supporting details sit beside their relevant main-talk content. On dependent slides, check that the correct earlier formula remains legible in the upper-right corner and leaves room for the headings. Verify that visual labels survive the crop and that figure credits, source locators, and audit notes stay off the projected pages.

Deliver the visually reviewed `build/main.pdf`, `slides/main.tex` and its local dependencies, and the approved `outline.md`. LaTeX auxiliary files are isolated in `build/latex/`. Use `project_manager.py clean` when discarding generated products. If the compiler or visual review is unavailable, identify what could be completed, what remains unverified, and the exact dependency or step needed. Report any material source limits.

**Optional PPTX with speaker notes.** When requested, write `speaker-notes.md` from the final PDF in the presentation language. Give each physical page a spoken explanation that the presenter can use in the room. Keep manuscript page numbers, equation and figure locators, source links, and verification comments in the outline or TeX comments.

**Preserve PDF fidelity on export.** Use [the export workflow](references/pptx-export.md) and [`scripts/export_pptx.py`](scripts/export_pptx.py) to embed one SVG picture per slide with editable native PowerPoint notes. Keep text, equations, and line art as vector paths wherever the PDF provides them, and preserve the available detail of embedded raster images. The default export includes a losslessly compressed PNG fallback with a 3840-pixel long edge (3840 × 2160 for 16:9). If SVG export is unavailable or the target viewer requires PNG, use the same high-resolution PNG setting and report the actual format and dimensions. Compare the exported slides with the final PDF at presentation size and when zoomed in. Check small formulas, glyphs, and figure crops, and verify that the notes match the slide order. Deliver the PPTX and its reusable notes file alongside the requested deck materials.
