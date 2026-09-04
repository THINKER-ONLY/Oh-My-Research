# Falsifiable Claims

## C01: Portable evidence-grounded writing workflow

- **Statement**: The V1 repository contains a valid portable Agent Skill that implements the ordered Frame → Ledger → Story → Draft → Revise → Audit → Deliver workflow, with dedicated references and reusable brief/ledger assets.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: Any required workflow gate is absent from `research-writing/SKILL.md`, a referenced resource is missing, or the official Skill validator fails on the current tree.
- **Proof**: [E02]
- **Evidence basis**: The Skill file names all seven gates, routes four phase-specific references, links two reusable assets, and passed the official structural validator; the structural audit is recorded in `evidence/tables/observed_skill_structure.md`.
- **Interpretation**: This establishes implementation and structural validity, not general writing effectiveness.
- **Dependencies**: none
- **Tags**: agent-skill, writing-workflow, evidence-ledger, portability

## C02: Traceable corpus manifest and download outcomes

- **Statement**: The current corpus manifest records 9 inputs, 583 links, 80 candidates and matching download records; 70 records are downloaded, 10 are failed, and successful records account for exactly 174,784,070 bytes with no missing hash or path in the manifest audit.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: Recomputing the current inventory produces different stored counts, a candidate lacks a download record, a success lacks its path/hash, or corpus verification reports an error.
- **Proof**: [E01]
- **Evidence basis**: Exact raw fields and derived consistency checks from `doc/source-index/inventory.json`, plus a successful `verify` command.
- **Interpretation**: The manifest is internally consistent at the recorded revision; this does not establish source quality, open licensing, or future URL availability.
- **Dependencies**: none
- **Tags**: corpus, provenance, download, checksum, manifest

## C03: Restricted-source boundary is encoded and tested

- **Statement**: The corpus implementation treats `writing words.pdf` as restricted, replaces its inventory contexts with a fixed omission marker, and includes a passing unit test for that behavior; the open ARA intentionally includes no source-attributed excerpt, phrase list, or derived corpus from it.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: Any restricted-source inventory link contains non-redacted context, the redaction test fails, the download path does not contain the license-restriction guard, or an intentional/source-attributed excerpt, phrase list, or derived corpus appears in this ARA.
- **Proof**: [E02, E04]
- **Evidence basis**: The script constant and extraction branch, the named passing unit test, and an audit of 22 restricted-source link records with 0 non-redacted contexts; the repository audit records only metadata, policy, and the omission marker.
- **Interpretation**: This is a software and repository boundary, not a legal opinion about every linked resource.
- **Dependencies**: C02
- **Tags**: licensing, restricted-source, redaction, integrity

## C04: Fixed-case forward outputs score higher on targeted behavior

- **Statement**: Under the unchanged eight-dimension rubric on the four supplied cases, the descriptive total changes from 37/64 for baseline outputs to 58/64 for forward outputs, while critical failures change from 2 of 4 cases to 0 of 4.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: Re-scoring the preserved raw outputs under the documented rubric does not reproduce the per-case scores, aggregate totals, or critical-failure classifications in `research-writing/evals/comparison.md`.
- **Proof**: [E03]
- **Evidence basis**: Exact per-case scores are 10→16, 12→14, 9→14, and 6→14 out of 16; the comparison file documents every dimension and critical-failure rationale.
- **Interpretation**: The result meets the documented V1 comparison rule on this fixed set and does not demonstrate general superiority.
- **Dependencies**: C01
- **Tags**: evaluation, baseline, forward-test, bounded-evidence

## C05: Fixed compression output avoids the observed evidence drift

- **Statement**: In the fixed compression case, the 21-word baseline changed association to causation and removed material limitations, whereas the 25-word forward sentence retained association, pilot scope, missing controls, missing significance tests, missing replication, and unestablished causality/generalizability.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: The preserved raw sentences do not contain the stated causal/qualifier contrast, their documented word counts are not 21 and 25, or the unchanged critical-failure rubric does not classify the baseline as failing and the forward output as non-failing.
- **Proof**: [E03]
- **Evidence basis**: `research-writing/evals/baseline/04-compression.md`, `research-writing/evals/forward/04-compression.md`, and the case-specific scoring in the comparison file.
- **Interpretation**: The forward output is consistent with the intended compression safety gate on one adversarial fixture; this uncontrolled comparison does not isolate a causal gate effect or generalize to other summarization tasks.
- **Dependencies**: C01, C04
- **Tags**: compression, causality, qualifiers, semantic-preservation

## C06: Recorded structural and execution checks pass

- **Statement**: On 2026-08-06, the pre-ARA tracked tree at commit `f4ddb534adbfff99d1dbe8a041cffff08549bdaf` passed all 17 corpus unit tests, passed the official Skill validator, and passed corpus hash/path verification with an empty error list.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: Re-running any recorded command against the anchored tracked tree returns a nonzero exit code or reports a failed check.
- **Proof**: [E01, E02]
- **Evidence basis**: The command-level output captured in `evidence/tables/observed_validation_runs.md`.
- **Interpretation**: Passing checks establish conformance to the tested behaviors, not absence of untested defects.
- **Dependencies**: C01, C02, C03
- **Tags**: validation, tests, seal, reproducibility
