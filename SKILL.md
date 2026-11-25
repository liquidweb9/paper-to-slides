---
name: paper-to-slides
description: >-
  Prepare technical LaTeX Beamer slides for a paper discussion, lab meeting,
  journal club, or research group presentation from the original manuscript,
  Markdown notes, and a paper link. Build a source-backed slide-by-slide outline
  for user approval, then deliver Beamer source and PDF with an optional
  image-based PPTX.
---

# Paper to Slides

Turn the supplied paper materials into a technically substantial group presentation with a review of the slide outline before production.

## 1. Collect and verify sources

Work in the output directory named by the user. For a new talk without a specified location, create a distinct directory under the project's `projects/` directory if present, or under the current workspace. Keep source inputs intact. Record source paths or URLs and the manuscript version in `outline.md`.

Ask the user to provide all three core inputs when invoking the skill. Check that they are readable, and ask for any missing or inaccessible item by name. Ask for a paper or project link if none was supplied; if no webpage exists or can be accessed, ask for an alternate link, offline copy, or the needed original assets. If the user confirms an input is unavailable, state the resulting limits in the outline and draft only what the available sources support.

| Input | Use |
| --- | --- |
| Original manuscript (PDF or complete LaTeX source) | Verify definitions, assumptions, equations, algorithms, results, and stated limitations against the version being presented. Prefer matching TeX for equation transcription. Check PDF page images for extracted math, table alignment, and figure details when needed. |
| Presenter's Markdown notes (`.md`) | Preserve the requested emphasis, questions, and interpretations. Label the presenter's interpretation when it goes beyond the paper's evidence. |
| Paper link (DOI, arXiv, publisher page, or official project page) | Verify the version and locate official figures, author demos, appendices, and other supporting material. Record the URL and section or asset. |
| Optional materials | Ask for relevant supplements, figures, or reference slides as needed, and invite the user to specify the audience, duration, or emphasis. |

Extract or index text as needed for reading and retrieval. Treat extraction errors and OCR guesses as unresolved until checked against the original. Track important claims at the level of the equation, figure, table, section, or page. Match an experimental number to its condition, metric, baseline, and unit. Flag material differences between sources with both locators in the outline or source comments. Work within the supplied sources by default and add external context only when requested.

---

## 2. Write and review the outline

Write `outline.md` in the requested presentation language, defaulting to the user's language. State the paper identity, intended audience, talk objective, scope, and requested duration if known. Organize the talk around the research question and the paper's argument. Fit the main talk to the audience and available time.

### Main-talk sequence

1. **Problem introduction, if needed.** Use one or a few slides before the contributions to explain the key question, why it matters, and what existing approaches leave unresolved. Skip standalone introduction slides if the contributions slide can make the problem and the gap immediately clear.
2. **Main contributions.** State what the paper adds, how it addresses the key problem, and what evidence supports its strongest claims. Distinguish the paper's contribution from existing techniques it uses.
3. **Prerequisites.** Introduce the concepts, notation, and assumptions the audience needs for the method, proof, or results. Explain how each will be used; introduce later details where they first matter.
4. **Approach or method.** Walk through the inputs, outputs, and main steps. Explain why the core design works or addresses the gap. Plan the derivations of key formulas and worked examples for formulas or processes that are hard to follow.
5. **Proof, when applicable.** State the result and assumptions, then show the proof idea and the steps the conclusion depends on. Keep essential reasoning in the main talk; move routine algebra and secondary lemmas to backup slides as needed. Omit the proof section if the paper has no relevant proof.
6. **Experiments.** Explain the evaluation question, setup, baselines, and metrics before interpreting the key results. Include ablations or failure cases when they explain what works and when. If the paper has no experiments, identify what evidence it does provide; do not invent an evaluation.
7. **Summary.** Return to the key question and state what the paper establishes, what remains uncertain, and a limitation or promising next direction when supported. Label presenter proposals as such.

**Decide whether to add a problem introduction.** After hearing the contributions slide, could the intended audience say what the paper is trying to achieve, what makes it hard, and how the contribution addresses that obstacle? If yes, start with contributions. For example, “Full fine-tuning stores a separate set of weights for each task. We share the base weights and learn a much smaller update per task” can stand on its own for an audience familiar with fine-tuning. “We propose a low-rank adaptation method” does not explain the obstacle. For an audience unfamiliar with fine-tuning, first show why two tasks would otherwise need two copies of the weights, then ask what could be shared. The [template](template/template.tex) includes both layouts: toggle `\PaperTalkProblemIntrotrue` in place of `\PaperTalkProblemIntrofalse` to preview the optional introduction before contributions. Its appendix compares the two cases.

### Per-slide plan and review

| Per-slide field | What to record |
| --- | --- |
| ID, title, and placement | Stable ID, informative title, and main talk or appendix. |
| Audience takeaway | The specific point the audience should understand after this slide. |
| Content and explanation | The reasoning the speaker will cover. For method slides, name inputs, outputs, assumptions, symbols, and the role of each key term or step. For result slides, name the comparison, values, and what the evidence supports. |
| Math dependencies and examples | Identify which earlier formula belongs in the upper-right recap, the key derivation steps to show, and any worked example with its inputs, intermediate steps, and output. |
| Evidence and assets | Record exact source locators for factual claims, equations, and results. For visuals, specify the original paper or webpage, the figure or panel to crop, and what the audience should learn from it. Mark unavailable assets and ask for the original or an alternate source before relying on them. |

Give the core method enough space to connect the problem, method, and evidence. Distinguish measured outcomes from authors' explanations or the presenter's hypotheses. Keep the steps needed to follow key derivations in the main talk, even when full derivations, tables, and secondary experiments go into backup slides. Mark unresolved items in the outline beside the affected slides and omit unsupported numbers or claims.

**Blocking outline review.** Share `outline.md`, call out any material gaps, and ask the user to approve it or request changes. Stop before authoring or editing Beamer slide code, compiling a deck, or exporting slides. Revise the outline in response to feedback and wait for explicit approval of the version to be built. A request to make the presentation or silence does not approve the outline. On resume, require an explicit approval in the conversation or an outline the user explicitly identifies as already approved.

---

## 3. Build the approved Beamer deck

Use the approved outline for slide order, scope, and evidence. Choose layout details during authoring. Return material changes to the outline for review, such as replacing key evidence, omitting a planned technical step, or changing the slide roster.

Write a rebuildable `main.tex` with relative links to local figures and any other required source files. By default, copy [`template/template.tex`](template/template.tex) to the talk directory as `main.tex` and place [`template/template.sty`](template/template.sty) alongside it. Replace the teaching example and its template-guidance appendix with the approved slide content. The template demonstrates the full main-talk sequence, including a derivation, a worked example, and an optional proof. The template uses a 16:9 white canvas, orange and light-blue cover bands and square bullets, Times New Roman Latin text, SimHei cover Chinese, and SimSun content Chinese. Use `\PaperTalkTitleFrame` for the cover, `\author` for the paper authors, `\date` for the venue and year, and normal Beamer `frame` and `itemize` environments for body slides. Use the theme's 28 bp default body text or `\PaperTalkBodySize{24}` / `\PaperTalkBodySize{20}` where the layout needs denser text. The theme requires XeLaTeX and substitutes TeX Gyre Termes or Fandol when an original font is unavailable; report any substitution. Use a different theme or aspect ratio when requested. The fixed `template/` directory also contains the compiled [preview PDF](template/template.pdf).

### Write for the room

Use audience-facing titles, bullets, and captions that explain the idea or result directly. Keep audit notes, exact source locators, and verification status in `outline.md` or non-rendered `%` comments next to the corresponding TeX content. For example, show “The regularizer limits how far the update moves from the reference model” on the slide and put `% Source: manuscript §3.2, Eq. (5)` in the TeX. A compact scholarly attribution next to a borrowed figure is fine; captions should explain what to look for rather than telling the audience where to find it in the paper.

### Lay out formulas, derivations, and examples

- **Make the main math readable at presentation size.** Use display math and shared macros for recurring notation. Define symbols at first use, align related lines with `align` or `split`, and use spacing and emphasis to guide the eye. Split dense content across slides rather than shrinking the formulas until they fit.
- **Recall dependencies beside the title.** If understanding the current slide requires an earlier formula, repeat only the necessary expression with `\PaperTalkFormulaRecap[Earlier formula]{$\Delta W=BA$}` immediately after the frame title. The command places a narrow recap box to the right of the title, within the header, without adding a separate body row. Keep the current formula or derivation visually primary. If a recap is too long, keep only the relevant terms or split it into short lines. If native LaTeX typesetting is impractical, pass a cropped vector PDF (or a sharp equation image) to the same command with `\includegraphics[width=\linewidth,height=26bp,keepaspectratio]{...}`; keep the editable formula source and asset locally.
- **Derive key formulas on the slides.** Start from the definitions or assumptions, show the consequential intermediate equalities, inequalities, or substitutions, and explain why each non-obvious step holds and what the result means. When supplying a missing algebraic step, verify it from the stated assumptions. Do not present an illustration or heuristic as the paper's proof.
- **Work through difficult formulas or procedures.** Pick a small numeric, symbolic, or concrete example with the same notation as the method. Show the initial inputs or state, each decisive substitution or transition, the intermediate results, and the output and intuition. Label an example created for the talk as illustrative so it is not mistaken for a reported experiment.

### Capture figures and compile

Extract or crop illustrations, experiment plots, and table panels from the original paper or its official webpage or supplement. Prefer original vector assets or a vector PDF crop; otherwise use a clear export or screenshot. Preserve the axes, units, legends, labels, and context needed to read the image. Record the exact provenance in the outline or TeX comments. If no webpage is available, ask the user for a link or an offline source; if the paper and available webpages do not contain the needed asset, ask the user to provide it. Do not invent a substitute for missing evidence. If the user cannot provide the asset, flag the gap and agree on any material change through the outline review.

Use a project-aware XeLaTeX compiler or run `latexmk -xelatex main.tex` from the talk directory. Treat supplied LaTeX as reading material and compile the authored talk.

---

## 4. Verify and deliver

Check the compiled PDF against the approved outline and the source locators. Review compiler diagnostics for unresolved references or citations, missing glyphs, and overfull frames. Render and inspect the PDF pages for clipped equations, illegible figure labels, and distracting layout shifts. Spot-check substantive claims, signs, subscripts, numeric values, units, and citations against the sources. Fix at the source and rebuild before delivery.

Check that the talk answers the key question, keeps the needed prerequisites and derivation steps in the main slides, and walks through challenging material with examples. On each dependent slide, verify that the correct earlier formula is legible in the upper-right corner and does not crowd the main content. Confirm that figure crops preserve the details the audience needs and that audit notes and source-locator prose do not appear in the projected slides.

After verifying the final PDF, clean generated LaTeX auxiliary files (for example, run `latexmk -c main.tex`, then remove any remaining `main.nav`, `main.snm`, and `main.synctex*` files). Deliver the verified PDF, `main.tex` and its local dependencies, and the approved `outline.md`. If the compiler or visual review is unavailable, identify what could be completed, what remains unverified, and the exact dependency or step needed. Report any material source limits.

**Optional PPTX.** When requested, build it from the verified PDF by placing one high-resolution page image on each slide. Match the PDF aspect ratio, order, and page count. Verify the generated package and visually check image sizing. Identify the PPTX as image based and deliver the PDF and TeX source alongside it.
