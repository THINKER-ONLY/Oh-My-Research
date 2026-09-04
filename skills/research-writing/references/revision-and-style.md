# Revision and Style

Treat active voice, topic and stress positions, sentence length, and paragraph patterns as diagnostics. Apply them only when they improve reader comprehension without changing meaning or violating field convention.

Revision improves readability while preserving the author's claim. Protect one canonical meaning vector for every material sentence: proposition, scope, polarity, causal force, temporal order, design, intervention exposure, group assignment, comparison, method-result relation, population, conditions, qualifiers, quantities, units, uncertainty, and conclusion-changing limitations. The five familiar anchors (proposition, scope, polarity, qualifiers, and numbers) are a minimum subset, not a substitute for the full vector.

## Meaning vector

The meaning vector is the complete record to capture before editing: proposition, scope, polarity, causal force, temporal order, design, intervention exposure, group assignment, comparison, method-result relation, population, conditions, qualifiers, quantities, units, uncertainty, and conclusion-changing limitations, along with its ledger ID. Compare every element after editing; restore drift or disclose an evidence-authorized substantive change.

## Two-Pass Revision

1. **Anchor.** Copy the five anchors and the linked ledger ID. Mark what the evidence establishes and what it does not establish.
2. **Edit and compare.** Improve order, subject-verb clarity, terminology, repetition, and notation. Then compare every anchor with the original. Restore an anchor or label the change if the meaning moved.

Prefer concrete subjects and verbs, defined terms, short logical units, and direct transitions. Remove empty emphasis such as "clearly," "definitely," or "novel" when it adds no evidence. Define abbreviations and notation before use.

## Guardrails

| Preserve | Unsafe drift | Safer treatment |
| --- | --- | --- |
| Association | "caused," "improved," "reduced" | "was associated with," "coincided with" |
| Scope | One model, pilot, one setting | Keep the population, model, and setting visible |
| Polarity | No effect, uncertainty, limitation | Retain the negation or uncertainty explicitly |
| Qualifier | preliminary, may, no test | Keep it, or use an equally limiting replacement |
| Number | value, unit, denominator, direction | Recheck against the source before shortening |

Do not convert a before/after count into an intervention effect without a design that supports causal inference. Do not turn "not established" into "unlikely," "likely," or "demonstrated."

## Design-sensitive wording

Before using `prediction`, `mediation`, `mechanism`, `intervention`, or `causal identification`, check the design and analysis that identify the relation. Treat `effect`, `impact`, `improved`, `reduced`, `demonstrated`, `proved`, `robust`, `generalizes`, `significant`, `novel`, and `SOTA` as conditional wording, not decorations: use a term only when the ledger records the required comparison, uncertainty, scope, and design; otherwise qualify it or replace it with an observation or explicitly labeled hypothesis.

## Compression

Cut in this order: duplicated framing, ornamental modifiers, repeated labels, then optional examples. Keep the smallest set of words that preserves the evidence type, scope, result, and conclusion-changing limitation. If a word limit makes that impossible, report the constraint rather than dropping a material caveat.

For output-only requests, keep an unresolved compression constraint internal and do not append commentary; deliver the shortest faithful text without meaning or evidence drift. For CJK (Chinese, Japanese, or Korean) or mixed text, declare a character or language-aware counting convention; do not assume whitespace.

Example pattern: "The outcome changed after the procedure, but the uncontrolled comparison does not establish that the procedure caused the change." This preserves the observation and the causal limit without supplying task-specific facts.

## Revision Log

For substantive edits, record `location | original anchor | revision | reason | ledger ID | meaning changed?`. If the user requests only revised prose, keep the log internal unless a material uncertainty must be surfaced.
