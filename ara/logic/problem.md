# Problem Specification

## Observations

### O1: The supplied corpus is large enough to require deterministic provenance

- **Statement**: The current manifest contains 9 input PDFs, 583 page-provenanced link records, 80 unique download candidates, 20 blocked records, and 80 download result records.
- **Evidence**: `evidence/tables/observed_corpus_inventory.md` and `evidence/tables/observed_input_documents.md`.
- **Implication**: Manual copying is insufficient for reproducible classification, failure reporting, hashing, and source-to-file tracing.

### O2: The unassisted baseline contains integrity-sensitive failures

- **Statement**: On the four fixed cases, baseline outputs scored 37/64 descriptively and had critical failures in 2 of 4 cases; the failures included an unprovided experimental sequence and association-to-causation drift under compression.
- **Evidence**: `evidence/tables/observed_eval_comparison.md` and the raw files under `research-writing/evals/baseline/`.
- **Implication**: A writing capability needs explicit evidence and semantic-preservation gates, especially under deadline or word-limit pressure.

### O3: The forward evaluation addresses the targeted baseline failures

- **Statement**: On the same cases and rubric, forward outputs scored 58/64 descriptively and had 0 of 4 critical failures.
- **Evidence**: `evidence/tables/observed_eval_comparison.md` and the raw files under `research-writing/evals/forward/`.
- **Implication**: The V1 instructions are supported for these fixtures, while broader effectiveness remains untested.

### O4: The deterministic implementation passes its current checks

- **Statement**: A fresh run on 2026-08-06 completed 17 unit tests successfully, the Skill validator reported `Skill is valid!`, and corpus verification returned `{"ok": true, "errors": []}`.
- **Evidence**: `evidence/tables/observed_validation_runs.md`.
- **Implication**: The checked structure and manifest are internally consistent at this recorded revision.

### O5: One supplied source has a hard redistribution boundary

- **Statement**: The project identifies `writing words.pdf` as restricted; its 22 inventory link records all carry the placeholder `[restricted source context omitted]`, with 0 non-redacted contexts.
- **Evidence**: `evidence/tables/observed_license_boundary.md`; no protected prose is reproduced.
- **Implication**: The open artifact must encode the licensing rule without incorporating or deriving a phrasebank from the protected text.

## Gaps

### G1: Fluent prose can obscure unsupported scientific claims

- **Statement**: Writing quality alone does not expose whether a claim is supported, inferred, proposed, or missing evidence.
- **Caused by**: O2.
- **Existing attempts**: Unassisted drafting and revision.
- **Why they fail**: In the fixed baseline, time and compression pressure produced invented experimental detail and causal drift.

### G2: A local source library can lose provenance and failure information

- **Statement**: Downloaded files without a manifest do not retain the originating PDF, page, URL, status, checksum, or reason for failure.
- **Caused by**: O1.
- **Existing attempts**: Manual browser downloads and ad hoc folders.
- **Why they fail**: They are not deterministic, resumable, or independently verifiable.

### G3: Availability and redistribution permission are different properties

- **Statement**: A downloadable file cannot be assumed to be licensed for inclusion in an open repository.
- **Caused by**: O5 and the corpus synthesis.
- **Existing attempts**: Treating “downloadable” as synonymous with “open.”
- **Why they fail**: Retrieval status does not establish copyright or license rights.

### G4: Current evaluation coverage is narrow

- **Statement**: The evaluation contains four synthetic fixtures and does not specify the forward-run model metadata.
- **Caused by**: O3.
- **Existing attempts**: A fixed baseline/forward comparison.
- **Why they fail**: The comparison can test targeted regressions but cannot establish general superiority across disciplines, models, venues, or real manuscripts.

## Key Insight

- **Insight**: Separate judgment-heavy research writing from repeatable corpus mechanics, while binding both to explicit evidence states and independent completion checks.
- **Derived from**: O1, O2, O4, and O5.
- **Enables**: A small portable Skill for Frame → Ledger → Story → Draft → Revise → Audit → Deliver, paired with a deterministic corpus script and a bounded evaluation harness.

## Assumptions

- A1: The supplied project files and manifest are the authoritative record for this ARA revision.
- A2: The downloaded documents remain local research inputs unless their licenses are separately reviewed.
- A3: External URLs and network availability are mutable; a recorded failure is a time-bound observation, not proof of permanent unavailability.
- A4: Forward-evaluation scores describe only the supplied cases and unchanged rubric.
- A5: No training run, learned model, venue submission, DOI, or named project author is specified.
