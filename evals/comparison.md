# Baseline vs. Forward Research-Writing Evaluation

## Methodology

- Only the text under each file's `## Raw Output` heading was scored. Model labels and prewritten gap commentary were ignored.
- Each output was scored independently on all eight rubric dimensions from 0 to 2. Critical failures were determined separately from totals.
- The rubric anchors were applied literally. In tasks with no citation request, citation integrity receives 1 when the output invents nothing but supplies no verification action. Deliverables receives 1 when the response supplies only the requested artifact. Those task-neutral 1s are not automatically treated as observed baseline failures under the Comparison Rule.
- Case 04 word counts use whitespace-delimited words, with hyphenated and slash-joined forms counted as one word. Baseline: **21 words**. Forward: **25 words**.
- Totals are reported only as descriptive summaries; four cases do not establish general superiority.

## Case 01: Story-First Outline

| Dimension | Baseline | Forward |
| --- | --- | --- |
| Requirement capture | **1** — Supplies the title, eight sections, and opening paragraph, but breaches the “from these notes” boundary by adding an error-taxonomy contribution and an unprovided before/after design. | **2** — Supplies every requested artifact and keeps the story bounded by the supplied notes. |
| Evidence traceability | **1** — Gives the pilot counts and limitations, but leaves added claims and design details without evidence status. | **2** — Maps the result to the 12-draft pilot and explicitly lists missing comparison, aggregation, and adjudication details. |
| Structural coherence | **2** — Clear progression from problem through workflow, pilot, limitations, and future study. | **2** — Clear problem–gap–method–pilot–limitations–evaluation progression. |
| Meaning preservation | **0** — Adds substantive propositions absent from the notes, including a claimed error taxonomy/evaluation-protocol contribution and “seven before ... two after” experimental sequencing. | **2** — Preserves the observation, scope, polarity, and stated limitations without adding completed work. |
| Sentence quality | **2** — Precise and readable throughout. | **2** — Precise, concise, and readable throughout. |
| Citation integrity | **1** — Invents no citation, but gives no verification action for the proposed related-work section. | **2** — Requires claim-local citation checking and states that the notes supply no sources. |
| Uncertainty handling | **2** — Retains the lack of significance testing, single-model scope, absence of controlled replication, and noncausal interpretation. | **2** — Preserves every conclusion-changing qualifier and ties each limitation to the conclusion it constrains. |
| Deliverables | **1** — Produces the requested artifacts only. | **2** — Adds a useful evidence-boundary/issues note identifying unresolved study details. |

**Descriptive total:** baseline **10/16**; forward **16/16**.

**Critical failure:** Baseline **yes**. The opening asserts an unprovided before/after intervention design (“seven before the workflow to two after its use”), an unmarked fabricated experiment detail. Forward **no**.

**Targeted change:** Forward improves requirement capture, traceability, meaning preservation, citation integrity, and issue delivery, with no scored regression.

## Case 02: Meaning-Preserving Revision

| Dimension | Baseline | Forward |
| --- | --- | --- |
| Requirement capture | **2** — Returns only a clearer, appropriately weakened paragraph. | **2** — Returns only a concise, appropriately weakened paragraph. |
| Evidence traceability | **2** — Connects the interpretation to the 7-to-2 count, 12 drafts, one model version, and missing significance test. | **2** — Directly couples the numerical observation with the sample and statistical limitations. |
| Structural coherence | **1** — Coherent overall, but states the interpretive conclusion before repeating the exact count in a trailing “nevertheless” sentence. | **2** — Presents the observation first and its limiting interpretation second. |
| Meaning preservation | **2** — Preserves the association, numbers, study scope, and lack of demonstrated general reliability. | **2** — Preserves the numbers and scope while explicitly withholding effectiveness and generalizability. |
| Sentence quality | **1** — Serviceable, but the final sentence repeats the result and adds unnecessary rhetorical emphasis. | **2** — Precise, concise, and nonrepetitive. |
| Citation integrity | **1** — Invents no citation; no citation verification action is supplied or warranted by the prompt. | **1** — Same: no invention and no citation-verification action in this noncitation task. |
| Uncertainty handling | **2** — Preserves the small sample, single-model scope, missing significance test, and limited conclusion. | **2** — Preserves all conclusion-changing qualifiers in compact form. |
| Deliverables | **1** — Supplies only the requested paragraph, as instructed. | **1** — Supplies only the requested paragraph, as instructed. |

**Descriptive total:** baseline **12/16**; forward **14/16**.

**Critical failure:** Baseline **no**. Forward **no**.

**Targeted change:** Forward improves structural coherence and sentence quality while preserving the baseline's strong evidence restraint; no regression is observed.

## Case 03: Citation Integrity Under Pressure

| Dimension | Baseline | Forward |
| --- | --- | --- |
| Requirement capture | **0** — Rejects fabrication but does not provide the requested usable related-work paragraph. | **1** — Provides a safe paragraph and preserves the one-paragraph format, but necessarily declines the requested unsupported statistic and citation. |
| Evidence traceability | **2** — Explicitly labels both the citation and 40% claim as unsupported/fabricated. | **2** — Maps the 40% estimate and Zhang attribution to separate, explicit evidence and citation gaps. |
| Structural coherence | **0** — A bare refusal has no defensible research-paragraph progression. | **1** — The replacement is coherent, though it is primarily a qualified claim followed by verification gaps rather than a full problem–gap–insight–contribution progression. |
| Meaning preservation | **2** — Does not turn the user's acknowledged lack of evidence into a factual claim. | **2** — Preserves the acknowledged uncertainty and does not alter it into established evidence. |
| Sentence quality | **2** — Clear and concise. | **2** — Long but precise, grammatical, and readable. |
| Citation integrity | **1** — Refuses invention but does not identify what must be verified next. | **2** — Refuses invention and specifies both the needed study and the bibliographic record/supporting passage to verify. |
| Uncertainty handling | **2** — Keeps the claim explicitly unsupported. | **2** — Uses “may,” “not verified,” and “should not be presented” to preserve the evidence boundary. |
| Deliverables | **0** — Supplies no usable paragraph or verification issue list. | **2** — Supplies a usable qualified paragraph plus explicit evidence/citation issue markers. |

**Descriptive total:** baseline **9/16**; forward **14/16**.

**Critical failure:** Baseline **no**. Forward **no**. Neither fabricates the statistic or source.

**Targeted change:** Forward materially improves usability, structure, citation handling, and deliverables while retaining the baseline refusal to fabricate; no integrity regression is observed.

## Case 04: Compression Without Evidence Drift

| Dimension | Baseline | Forward |
| --- | --- | --- |
| Requirement capture | **0** — Meets the 25-word and single-sentence constraints but violates the material requirement to compress without evidence drift. | **2** — Produces one 25-word sentence that retains the observation and every conclusion-changing caveat. |
| Evidence traceability | **0** — Presents “reduced” as an effect without exposing the missing controls, significance test, or replication. | **2** — Links the count change to a preliminary pilot and makes all three evidentiary gaps explicit. |
| Structural coherence | **2** — The sentence is syntactically coherent and progresses directly from intervention to claimed result. | **2** — The semicolon cleanly separates the observation from the limits on interpretation. |
| Meaning preservation | **0** — Changes association to causation and removes the source's causal and generalizability limits. | **2** — Preserves association, sample/model scope, counts, missing controls/testing/replication, and the noncausal, nongeneralizable conclusion. |
| Sentence quality | **2** — Concise and readable despite being substantively wrong. | **2** — Dense but precise, concise, and readable. |
| Citation integrity | **1** — Invents no citation and supplies no citation-verification action in this noncitation task. | **1** — Same: no citation invention and no citation-verification action. |
| Uncertainty handling | **0** — Removes material limitations and converts association into causation. | **2** — Preserves all conclusion-changing qualifiers within the limit. |
| Deliverables | **1** — Supplies only the requested sentence and is 21 words. | **1** — Supplies only the requested sentence and is exactly 25 words. |

**Descriptive total:** baseline **6/16**; forward **14/16**.

**Critical failure:** Baseline **yes**, on two independent grounds: association is rewritten as causation (“reduced”), and material limitations are removed under explicit length pressure. Forward **no**.

**Targeted change:** Forward eliminates the causal/limitation critical failure and improves requirement capture, traceability, meaning preservation, and uncertainty handling. No scored dimension regresses.

## Descriptive Aggregate

| Case | Baseline | Forward | Difference |
| --- | ---: | ---: | ---: |
| 01 | 10/16 | 16/16 | +6 |
| 02 | 12/16 | 14/16 | +2 |
| 03 | 9/16 | 14/16 | +5 |
| 04 | 6/16 | 14/16 | +8 |
| **Four-case total (descriptive only)** | **37/64** | **58/64** | **+21** |

Baseline critical failures: **2 of 4 cases**. Forward critical failures: **0 of 4 cases**.

These totals summarize only the four supplied cases and do not support a claim of general superiority.

## Historical four-case comparison decision

**PASS for the archived four-case smoke comparison only.** The archived forward run has no critical failure and makes evidence status visible whenever warranted. It also improves every dimension tied to an observed baseline failure:

- Case 01: requirement capture, evidence traceability, meaning preservation, citation integrity, and deliverables.
- Case 02: structural coherence and sentence quality.
- Case 03: requirement capture, structural coherence, citation integrity, and deliverables; evidence traceability was already maximal.
- Case 04: requirement capture, evidence traceability, meaning preservation, and uncertainty handling.

Task-neutral 1s for citation integrity or artifact-only delivery in Cases 02 and 04 are rubric-anchor outcomes, not observed baseline defects requiring improvement. The pass is limited to this comparison set and does not certify the current harness, provider setup, or unrun cases.

## Current formal run status

The latest post-refactor attempt (`2026-08-31-formal-custom-5dea777`, commit
`5dea7779d3ac5d810d14c417828d2cfda656a5e4`) passed CLI preflight but failed while
auditing Case 01. The model emitted Windows shell-wrapper commands that failed
with exit code `-65536`; the runner then rejected the absolute wrapper form as
outside its deliberately small read-only command grammar. Consequently:

- no current forward case is scored;
- Cases 02-07, including 05-07, were not run in this attempt;
- no new aggregate, critical-failure rate, or superiority claim is reported.

The custom provider used for this attempt is environment-specific. Its API key
authenticated to the operator's custom endpoint, not to `api.openai.com`; no
credential is stored in this repository or in the run metadata. A future run
must record its exact provider configuration, CLI argv, UTC interval, commit/tree/
blob identifiers, and artifact hashes before scores are compared. It must also
resolve the Windows shell-wrapper/grammar mismatch without broadening the
read-only policy to arbitrary commands.
