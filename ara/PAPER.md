---
title: "Oh My Research: Evidence-Grounded Research Writing Skill and Traceable Corpus Pipeline"
authors:
  - "Not specified"
year: 2026
venue: "Not applicable — research software artifact"
doi: "Not specified"
ara_version: "1.0"
domain: "research software, academic writing, provenance, agent skills"
keywords:
  - research writing
  - evidence ledger
  - claim auditing
  - corpus provenance
  - agent skill
  - citation integrity
  - compression safety
  - research software
claims_summary:
  - "The repository implements a portable, evidence-grounded research-writing workflow with explicit claim, revision, and integrity gates."
  - "The corpus manifest records 9 inputs, 583 link records, 80 download candidates, 70 successful downloads, and 10 recorded failures with provenance."
  - "On the four fixed evaluation cases, forward outputs had no critical integrity failure and addressed every targeted baseline failure."
abstract: "This Agent-Native Research Artifact describes a research-software project that combines a portable research-writing Skill with a deterministic PDF-link inventory and download pipeline. The writing workflow externalizes claims in an evidence ledger, preserves meaning and uncertainty during revision, and treats citation and license checks as completion gates. The local corpus manifest and fixed baseline/forward evaluation provide bounded execution evidence. Downloaded binaries remain local, and no source-attributed excerpt, phrase list, or derived corpus from the restricted Phrasebank PDF was intentionally included; no claim of general writing superiority is made beyond the supplied evaluation fixtures."
---

# Oh My Research: Evidence-Grounded Research Writing Skill and Traceable Corpus Pipeline

## Overview

The artifact captures the implemented V1 as research software rather than as a paper. Its two coupled parts are a portable Agent Skill for evidence-grounded academic writing and a deterministic corpus tool for extracting, classifying, downloading, hashing, and verifying document references.

Observed values are kept in `/evidence`; `/logic/experiments.md` contains only declarative reproduction plans. The local restricted Phrasebank PDF was not inspected for this ARA, and no source-attributed excerpt, phrase list, or derived corpus from it was intentionally included.

## Layer Index

### Cognitive Layer (`/logic`)

| File | Description |
| --- | --- |
| [problem.md](logic/problem.md) | Observed project facts, gaps, key insight, and assumptions |
| [claims.md](logic/claims.md) | 6 falsifiable, evidence-bounded claims (C01–C06) |
| [concepts.md](logic/concepts.md) | 9 formal concepts used by the writing and corpus workflows |
| [experiments.md](logic/experiments.md) | 4 declarative reproduction and audit plans (E01–E04) |
| [architecture.md](logic/solution/architecture.md) | Component graph, interfaces, and data flow |
| [algorithm.md](logic/solution/algorithm.md) | Formal claim-admissibility, revision, compression, and corpus procedures |
| [constraints.md](logic/solution/constraints.md) | Scope, licensing, evaluation, and implementation limitations |
| [heuristics.md](logic/solution/heuristics.md) | 6 implementation heuristics with code references |
| [related_work.md](logic/related_work.md) | Typed map of the nine supplied source families |

### Physical Layer (`/src`)

| File | Description | Claims |
| --- | --- | --- |
| [training.md](src/configs/training.md) | Training configuration; explicitly not applicable to this artifact | C01, C06 |
| [model.md](src/configs/model.md) | Portable runtime/model assumptions and unspecified fields | C01, C04 |
| [research_writing_pipeline.py](src/execution/research_writing_pipeline.py) | Typed execution stub for ledger, semantic, corpus, evaluation, and license gates | C01, C02, C03, C05 |
| [environment.md](src/environment.md) | Documented Python/dependency environment and unknowns | C02, C06 |

### Exploration Graph (`/trace`)

| File | Description |
| --- | --- |
| [exploration_tree.yaml](trace/exploration_tree.yaml) | 11-node explicit/inferred research DAG with decisions and dead ends |
| [session_index.yaml](trace/sessions/session_index.yaml) | Cross-session index for the recorded project epilogue |

### Staging (`/staging`)

| File | Description |
| --- | --- |
| [observations.yaml](staging/observations.yaml) | Unclassified observations awaiting future promotion; currently empty |

### Evidence (`/evidence`)

| File | Description |
| --- | --- |
| [README.md](evidence/README.md) | Claim-to-evidence index for 6 tables and 1 derived score series |
| [observed_corpus_inventory.md](evidence/tables/observed_corpus_inventory.md) | Exact manifest counts, status totals, and integrity checks |
| [observed_input_documents.md](evidence/tables/observed_input_documents.md) | Exact input-file page and extracted-character metadata |
| [observed_eval_comparison.md](evidence/tables/observed_eval_comparison.md) | Exact per-case and aggregate fixed-rubric scores |
| [observed_validation_runs.md](evidence/tables/observed_validation_runs.md) | Exact command-level validation outcomes from 2026-08-06 |
| [observed_skill_structure.md](evidence/tables/observed_skill_structure.md) | Exact Skill workflow, reference, asset, metadata, and validator coverage |
| [observed_license_boundary.md](evidence/tables/observed_license_boundary.md) | Exact restricted-context audit values without protected text |
| [derived_eval_score_series.md](evidence/figures/derived_eval_score_series.md) | Derived plotting series for baseline and forward scores |
