# Implementation Heuristics

## H01: Ledger before substantive claim creation

- **Provenance**: ai-suggested
- **Rationale**: Claims drafted before support status is explicit can acquire plausible but unverified detail.
- **Sensitivity**: high
- **Bounds**: Required for new or materially strengthened claims; optional as a visible deliverable for faithful copyedits.
- **Code ref**: [src/execution/research_writing_pipeline.py]
- **Source**: `research-writing/SKILL.md`, Workflow steps 1–3; `references/writing-workflow.md`, Ledger

## H02: Freeze conclusion-changing meaning atoms before compression

- **Provenance**: ai-suggested
- **Rationale**: In the fixed length-pressure case, the baseline output exhibited association-to-causation and limitation-removal failures.
- **Sensitivity**: high
- **Bounds**: Freeze causal force, scope, quantities, comparison, uncertainty, and material limitations; reject a target that cannot preserve them.
- **Code ref**: [src/execution/research_writing_pipeline.py]
- **Source**: `research-writing/SKILL.md`, Compression safety gate; `evals/comparison.md`, Case 04

## H03: Separate raw observation from interpretation

- **Provenance**: ai-suggested
- **Rationale**: Exact counts can be valid observations while causal or general claims remain unsupported.
- **Sensitivity**: high
- **Bounds**: Raw values stay in evidence; broader implications must be labeled and cannot outrun the study design.
- **Code ref**: [src/execution/research_writing_pipeline.py]
- **Source**: `references/evidence-and-integrity.md`, Inference Boundaries

## H04: Keep integrity rules core and load detail progressively

- **Provenance**: ai-suggested
- **Rationale**: Progressive disclosure saves context, but evidence, citation, licensing, and completion gates are too consequential to rely on optional loading.
- **Sensitivity**: medium
- **Bounds**: Section and style guidance may load on demand; non-fabrication and semantic-preservation rules remain in `SKILL.md`.
- **Code ref**: [src/execution/research_writing_pipeline.py]
- **Source**: `research-writing/SKILL.md`, Load only what the task needs; `docs/corpus-synthesis.md`, conflicts and trade-offs

## H05: Script repetitive, fragile corpus operations

- **Provenance**: ai-suggested
- **Rationale**: URL normalization, bounded retries, signature checking, hashing, and manifest reconciliation are more auditable as deterministic code than repeated prose instructions.
- **Sensitivity**: medium
- **Bounds**: Use scripts for mechanical operations; preserve human/model judgment for source quality, licensing, and scientific interpretation.
- **Code ref**: [src/execution/research_writing_pipeline.py]
- **Source**: `docs/superpowers/specs/2026-08-06-research-skill-design.md`, Corpus Pipeline

## H06: Fail visibly at evidence and license boundaries

- **Provenance**: ai-suggested
- **Rationale**: Silent omission or plausible substitution hides unresolved risk.
- **Sensitivity**: high
- **Bounds**: Use gaps, pending verification, recorded download errors, or license-restricted status; never guess a replacement citation, URL, or protected phrase.
- **Code ref**: [src/execution/research_writing_pipeline.py]
- **Source**: `research-writing/SKILL.md`, Non-negotiable rules; `docs/corpus-synthesis.md`, download and repository boundary
