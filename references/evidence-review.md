# Reviewing a paper for a group meeting

## Prepare the outline with the original open

For each substantive slide, put the claim, the evidence for it, and the line of reasoning the speaker will explain together in `outline.md`. A source shared by several statements on one slide can be cited once when the mapping is clear. Record a precise pointer beside each distinct result or equation. Use the archived PDF page position plus the printed equation, section, figure, panel, or table cell in the link text. For a TeX manuscript, link to the file containing the actual expression or statement.

```markdown
[Table 1, Llama / Homo / Wizard, MT-bench column](<sources/manuscript/original/FLoRA_2409.05976.pdf#page=7>)
[Eq. (11), stacking and weight placement](<sources/manuscript/original/FLoRA_2409.05976.pdf#page=6>)
```

Use the paths from the project's manifest. For TeX, an inline link can end in `sections/method.tex#L42-L49` or `main.tex#L42`. Use `<...>` around link targets with spaces or parentheses. For a borrowed web asset, record its official URL and panel or caption. Keep presenter questions and teaching examples clearly identified in the language of the talk.

Run `python scripts/check_evidence.py <talk-directory>` before outline review and again when checking the final deck. It compares the archived manuscript and supplements with their import hashes, checks local PDF page and TeX line links in the outline, and requires a precise manuscript link. For each substantive slide, the reviewer must still open the cited passage, compare it with the slide, and check the wording. A link to the wrong row on an existing page can pass the script.

## What to check on the projected slides

| Material | Check against the original | What the speaker should be able to explain |
| --- | --- | --- |
| Measured result | Read the row, column, caption, and footnote together. Verify dataset and split, model, setting, baseline, metric, unit, and direction where applicable. Preserve meaningful rounding and reported uncertainty. | What changed, by how much, under which comparison? For a calculated difference, show the operands in the outline and distinguish percentage points from relative change. Use claims of statistical significance only when supported by the reported analysis. |
| Formula or theorem | Compare the typeset expression with the same-version TeX or the visible original. Check signs, indices, bounds, normalization, dimensions, assumptions, and quantifiers. For a reformulation, record the notation mapping or intermediate step. | Which term makes the method work? What changes if an assumption is removed? Identify presenter derivations explicitly. If an apparent typo materially changes the result, document it and leave the uncertain step out until resolved. |
| Figure or plot | Verify the panel, axes, scale, legend, and meaning of error bars. Use labeled values or released data for exact figures. Identify any estimates read from a curve as approximate. | Which comparison can the audience actually see? Which larger conclusion would need another condition, control, or measurement? |
| Interpretation | Check whether the authors measured an effect, proposed an explanation, or proved a statement. Attribute each accordingly. Separate a presenter hypothesis or local application from the paper's findings. | For a claim like “more efficient,” name the resource, comparator, and setting. If only parameter count was measured, leave runtime and memory open. |

Choose a central question that survives beyond the paper's abstract. For an empirical paper, walk through the most informative comparison and a nearby result that changes or bounds the interpretation, when available. For a theoretical paper, trace the decisive proof step and identify the assumption it uses. For a system or dataset paper, follow one design or construction choice through to its evaluation or coverage. A discussion prompt can ask the group to predict a result, choose a comparison, or name an observation that would distinguish two explanations. Connect it to the group's own setup only when that setup is known.

## Worked example from a real paper

In *FLoRA: Federated Fine-Tuning Large Language Models with Heterogeneous Low-Rank Adaptations*, the archived preprint identifies itself as arXiv:2409.05976v1. The following two slides could anchor a discussion of how a mathematical change connects to an empirical result. [Manuscript, v1](https://arxiv.org/pdf/2409.05976v1)

- **Method.** On PDF page 6, Eq. (11) weights each client’s `A_k` by `p_k` before stacking and stacks the `B_k` factors unweighted. Ask the room what coefficient the product would give a client's update if both factors carried the weight. Multiplying the two factors gives `p_k²` in place of `p_k`. This algebra explains the placement of the weight. It supplies no numerical prediction for a benchmark score.
- **Result.** On PDF page 7, Table 1 reports MT-bench scores on the Llama model fine-tuned on Wizard. With homogeneous rank 16, FedIT scores 3.07 and FLoRA scores 4.21. The presenter's subtraction gives a 1.14-point difference. The centralized LoRA row in the same column scores 4.38. Keep all three values when discussing whether this experiment justifies replacing centralized training.
- **Discussion.** If the group wants to attribute the score difference specifically to the weight placement, what would it hold fixed and what would it vary? The method comparison in Table 1 changes the aggregation procedure. A test isolating a single component would need to keep the other choices fixed. Identify this question as the presenter's interpretation and consult the paper's ablations before proposing a new experiment.
