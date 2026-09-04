# Evidence Index

The tables below distinguish raw project observations from derived audits and interpretation. No source-attributed excerpt, phrase list, or derived corpus from the restricted Phrasebank PDF was intentionally included.

## Tables

| File | Source | Claims | Description |
| --- | --- | --- | --- |
| [tables/observed_corpus_inventory.md](tables/observed_corpus_inventory.md) | `doc/source-index/inventory.json` | C02, C06 | Exact manifest summary, topic/status counts, and computed consistency checks |
| [tables/observed_input_documents.md](tables/observed_input_documents.md) | `inventory.json.inputs` | C02 | Exact filename, page, and extracted-character metadata for all inputs |
| [tables/observed_eval_comparison.md](tables/observed_eval_comparison.md) | `research-writing/evals/comparison.md` plus baseline/forward `Raw Output` files | C04, C05 | Exact per-case scores, aggregates, word counts, and critical-failure incidence |
| [tables/observed_validation_runs.md](tables/observed_validation_runs.md) | Fresh local commands on 2026-08-06 | C01, C02, C03, C06 | Exit codes and exact high-level outcomes for tests and validators |
| [tables/observed_skill_structure.md](tables/observed_skill_structure.md) | `research-writing/SKILL.md` and linked local resources | C01, C03 | Exact workflow-gate, reference, asset, metadata, and validator coverage |
| [tables/observed_license_boundary.md](tables/observed_license_boundary.md) | Inventory, corpus script, and unit test | C03 | Metadata-only audit of restricted-context handling |

## Figures

| File | Source | Claims | Description |
| --- | --- | --- | --- |
| [figures/derived_eval_score_series.md](figures/derived_eval_score_series.md) | Derived from `research-writing/evals/comparison.md` | C04 | Plot-ready baseline/forward score series; no source figure is claimed |

## Evidence-to-experiment binding

| Experiment | Evidence files |
| --- | --- |
| E01 | `observed_corpus_inventory.md`, `observed_input_documents.md`, `observed_validation_runs.md` |
| E02 | `observed_validation_runs.md`, `observed_skill_structure.md`, `observed_license_boundary.md` |
| E03 | `observed_eval_comparison.md`, `derived_eval_score_series.md` |
| E04 | `observed_license_boundary.md` |
