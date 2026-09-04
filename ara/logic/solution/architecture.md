# Solution Architecture

## Component Graph

```text
Local source PDFs
       |
       v
Corpus Pipeline -----> source-index manifest -----> corpus synthesis
       |                       |
       |                       +----> hashes, failures, page provenance
       v
topic folders (local, untracked)

Research materials + user constraints
       |
       v
Writing Workflow: Frame -> Evidence Ledger -> Story -> Draft -> Revise -> Audit -> Deliver
                              ^                         |
                              |                         v
                     Evidence Boundary <---- Meaning/Compression Gate
                              |
                              v
                       License Boundary

Baseline outputs + forward outputs + fixed rubric
       |
       v
Evaluation Harness -----> bounded comparison evidence
```

## Writing Workflow

- **Purpose**: Route a writing task through the minimum sequence that protects its substantive claims.
- **Inputs**: Research materials, user constraints, artifact type, audience, requested deliverable.
- **Outputs**: Draft or revision, plus proportional evidence gaps, ledger entries, or audit notes.
- **Interactions**: Creates or updates the Evidence Ledger; loads focused references; sends substantive edits through the Meaning/Compression Gate; completes only after Audit.
- **Key design choices**: The core Skill retains integrity rules, while section/style details load progressively. A one-sentence copyedit may use a smaller path than a new paper.

## Evidence Ledger

- **Purpose**: Externalize claim status, support location, qualifiers, numbers, and unresolved actions.
- **Inputs**: Intended manuscript claims and available evidence artifacts.
- **Outputs**: Structured claim records marked supported, qualified, gap, pending-verification, or not-applicable.
- **Interactions**: Constrains Story and Draft; receives updates after substantive Revision; supplies the Audit mapping.
- **Key design choices**: Compound claims are split until independently auditable. Linguistic plausibility never changes evidence status.

## Meaning and Compression Gate

- **Purpose**: Prevent a revision or shortening operation from changing proposition, scope, polarity, causal force, quantities, uncertainty, or conclusion-changing limitations.
- **Inputs**: Structured meaning atoms for original and revised text, plus an optional word budget.
- **Outputs**: A safe/unsafe result and named semantic differences.
- **Interactions**: Runs before revised prose can return to the Writing Workflow.
- **Key design choices**: Redundant framing is cut before qualifiers. When budget and fidelity conflict, fidelity wins.

## Corpus Pipeline

- **Purpose**: Deterministically inventory page-level links, classify credible document candidates, download with bounded retries, verify signatures, hash files, resume, and write manifests.
- **Inputs**: Local PDFs, byte budgets, current manifest, and network responses.
- **Outputs**: `inventory.json`, source/download/failure CSVs, classified local documents, hashes, and explicit failure reasons.
- **Interactions**: Supplies provenance to the corpus synthesis and Evidence Boundary; calls the License Boundary before a restricted-source download.
- **Key design choices**: Annotation URLs are authoritative; visible text supplements them. Unsafe/malformed examples are retained as blocked records. Download success does not imply redistribution permission.

## Evaluation Harness

- **Purpose**: Compare raw baseline and forward outputs on unchanged cases and rubric anchors.
- **Inputs**: Case files, raw outputs, fixed rubric, and scoring convention.
- **Outputs**: Per-dimension scores, critical-failure decisions, bounded aggregate summaries, and targeted-change notes.
- **Interactions**: Tests the Writing Workflow and Meaning/Compression Gate; provides evidence for C04 and C05.
- **Key design choices**: Scores only `Raw Output`; reports aggregates as descriptive; refuses generalization beyond fixtures.

## Evidence Boundary

- **Purpose**: Separate raw observation, source-reported claims, project interpretation, planned work, and gaps.
- **Inputs**: Ledger records, source provenance, validation outputs, and evaluator judgments.
- **Outputs**: Evidence-bounded claim wording and explicit unresolved issues.
- **Interactions**: Governs Writing Workflow, Corpus Pipeline interpretation, and ARA claim strength.
- **Key design choices**: Exact observed values live in evidence files; experiments contain directional reproduction expectations only.

## License Boundary

- **Purpose**: Distinguish permitted indexing/local use from unsupported open redistribution.
- **Inputs**: Source filename, known license notes, requested action.
- **Outputs**: Allow, deny, or unknown policy state with a conservative default.
- **Interactions**: Redacts restricted source context and prevents protected text from entering open Skill/ARA resources.
- **Key design choices**: Metadata and lawful links may be retained; restricted prose, phrase lists, derived corpora, and binaries are excluded.
