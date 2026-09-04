# Declarative Reproduction Experiments

These are verification plans, not reports of new runs. Expected outcomes are directional; exact observed values are stored under `/evidence`.

## E01: Corpus manifest integrity reproduction

- **Verifies**: C02, C06
- **Setup**:
  - Model: Not applicable
  - Hardware: Not specified; ordinary local CPU execution is sufficient
  - Dataset: Current `doc/source-index/inventory.json` and referenced local document tree
  - System: Current corpus script and documented Python environment
- **Procedure**:
  1. Parse every manifest input, link, candidate, blocked, and download record.
  2. Compare candidate and download URL sets and recompute status/topic summaries.
  3. For successful records, resolve paths and recompute SHA-256 values.
  4. Run the corpus `verify` command against the same index and document directory.
- **Metrics**: Record-count consistency, candidate/result coverage, missing path count, missing hash count, hash mismatch count, status distribution, total successful bytes, command exit state
- **Expected outcome**:
  - Candidate and result sets agree, successful artifacts resolve without hash mismatches, and verification completes without errors.
- **Baselines**: An unchecked directory of manually downloaded files
- **Dependencies**: none

## E02: Skill structure and behavior validation

- **Verifies**: C01, C03, C06
- **Setup**:
  - Model: Not applicable for structural validation
  - Hardware: Not specified
  - Dataset: Current Skill tree and corpus unit-test suite
  - System: Official Skill validator plus Python `unittest`
- **Procedure**:
  1. Run the complete corpus unit-test module with bytecode writes disabled.
  2. Run the official quick validator on `research-writing/`.
  3. Resolve every Skill-linked reference and asset.
  4. Inspect the core file for all workflow gates and non-negotiable integrity rules.
- **Metrics**: Test pass/fail state, validator exit state, broken-link count, required-gate coverage
- **Expected outcome**:
  - All implemented tests pass, the Skill validates, referenced resources resolve, and required gates remain present.
- **Baselines**: Missing or malformed Skill package; corpus script without tested policy behavior
- **Dependencies**: none

## E03: Fixed-rubric baseline/forward evaluation

- **Verifies**: C04, C05
- **Setup**:
  - Model: Baseline metadata is preserved in the baseline files; forward-run model metadata is not specified
  - Hardware: Not specified
  - Dataset: The unchanged writing cases, raw baseline outputs, raw forward outputs, and fixed rubric
  - System: Independent manual scoring using only each file's `Raw Output`
- **Procedure**:
  1. Score every output independently on every rubric dimension.
  2. Apply the critical-failure rules separately from descriptive totals.
  3. Compare only dimensions tied to documented baseline gaps.
  4. Recount compression-case words with the documented tokenization convention.
- **Metrics**: Per-dimension scores, descriptive per-case and aggregate scores, critical-failure incidence, compression word count, targeted regression count
- **Expected outcome**:
  - Forward outputs eliminate the observed critical integrity failures and improve each targeted baseline weakness without a scored regression.
- **Baselines**: Preserved unassisted outputs for the same cases
- **Dependencies**: E02

## E04: Restricted-source repository audit

- **Verifies**: C03
- **Setup**:
  - Model: Not applicable
  - Hardware: Not specified
  - Dataset: Current inventory metadata, corpus script, unit tests, and open ARA tree
  - System: Text and manifest audit; the restricted PDF itself remains unopened
- **Procedure**:
  1. Select inventory records whose source filename matches the restricted source.
  2. Confirm that every stored context equals the omission marker.
  3. Confirm that the script contains both redaction and license-restriction guards.
  4. Search the open ARA for protected excerpts or phrase lists; inspect only project-authored files.
- **Metrics**: Non-redacted restricted-context count, guard presence, redaction-test state, protected-excerpt findings
- **Expected outcome**:
  - No protected context or excerpt appears, while metadata and the licensing decision remain auditable.
- **Baselines**: Bundling or reproducing a locally available but redistribution-restricted source
- **Dependencies**: E02
