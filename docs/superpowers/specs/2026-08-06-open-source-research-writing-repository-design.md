# Open-Source Research Writing Skill Repository Design

**Status:** Approved design

**Date:** 2026-08-06

## Decision

Restructure the project as an open-source repository shell containing one independently installable and releasable Agent Skill at `skills/research-writing/`. Keep development tools, tests, evaluations, research provenance, and the local evidence corpus outside the runtime Skill package.

The first release remains deliberately narrow: it provides evidence-grounded research writing. It does not introduce an MCP server, a persistent harness, or multi-agent orchestration until a demonstrated use case requires those components.

## Goals

1. Make the repository understandable, testable, contributable, and releasable as an open-source project.
2. Make `skills/research-writing/` a minimal, portable Skill package with no evaluation fixtures or project-specific corpus tooling inside it.
3. Preserve the current integrity behavior: no invented citations, no unsupported causal strengthening, no silent semantic drift, and no deletion of conclusion-changing limitations under compression.
4. Make each important writing principle traceable to supplied PDFs and verified extension sources without copying restricted prose.
5. Distinguish universal integrity constraints from genre conventions and author preferences.
6. Leave `doc/` byte-for-byte and metadata-equivalent throughout the refactor.

## Non-Goals

- Redistributing the supplied or downloaded PDFs.
- Editing, moving, deleting, untracking, or regenerating anything under `doc/`.
- Replacing a citation manager, statistical package, or reproducibility platform.
- Claiming that expert writing guidance is controlled empirical evidence of writing effectiveness.
- Forcing one paper structure, disciplinary convention, voice, or prose style onto every manuscript.
- Building a network service, MCP server, persistent harness, or autonomous research runtime in this release.

## Critical Assessment of the Current Skill

The current Skill already has a strong core. Its trigger metadata is specific, its references are progressively disclosed, its operating depth is proportional to the request, and its tests demonstrate meaningful improvements on four fixed cases. The evidence ceiling, semantic preservation rules, citation restraint, and compression gate should remain first-class constraints.

The refactor must correct five design weaknesses.

### 1. Runtime and development concerns are mixed

`research-writing/evals/` is test evidence rather than runtime guidance. `research-writing/scripts/corpus.py` is a repository-specific acquisition and provenance tool that is not routed from `SKILL.md`. Both should move outside the installable Skill package.

### 2. The story pattern is too universal

`problem -> gap -> insight -> contribution` is a useful default for contribution-driven papers, but it is not a universal law. Replication studies, negative results, surveys, methods notes, data papers, tutorials, and descriptive reports may require different progressions. The Skill should select a genre-appropriate argument while retaining claim-to-evidence traceability.

### 3. Evidence-state terminology is inconsistent

The current core and workflow reference use different status vocabularies and mix two distinct concepts:

- `claim_type`: what kind of statement this is;
- `support_status`: how well it is supported.

The canonical model will be:

| Field | Allowed values |
| --- | --- |
| `claim_type` | `observation`, `source-report`, `interpretation`, `hypothesis`, `proposal` |
| `support_status` | `verified`, `partial`, `pending-verification`, `gap`, `not-applicable` |
| `citation_status` | `verified`, `pending-verification`, `not-required` |

An inference or proposal must not be represented as a weakly supported observation. The ledger records these dimensions separately.

Because numeric and comparison drift are low-freedom failures, the ledger also keeps polarity, scope, conditions, qualifiers, numeric value, unit, denominator, comparison/baseline, and evidence summary in separate fields rather than an opaque free-text number column.

### 4. The rationale is not directly traceable

The existing corpus synthesis explains the source families, but the runtime package lacks a direct map from writing principle to source location and Skill rule. A new `references/source-foundations.md` will provide that map and will be loaded only when users ask for rationale, methodology, adaptation, or a design audit.

### 5. The release boundary is implicit

`.gitignore` does not define a safe release. The project needs an explicit allowlist, a deterministic repository validator, and CI that proves the released Skill contains no PDFs, local absolute paths, evaluation fixtures, provenance records, or restricted source content.

## Design Philosophy

The Skill will set freedom according to the fragility of the decision.

| Area | Freedom | Design treatment |
| --- | --- | --- |
| Citation identity, quotations, numbers, units, causal force, limitations | Low | Explicit non-negotiable rules and completion checks |
| Evidence ledger, section purpose, revision order, reproducibility reporting | Medium | Canonical schemas and adaptable workflows |
| Story arc, section ordering, active/passive voice, paragraph style, phrasing | High | Genre-aware heuristics and examples, never universal mandates |

This separation is source-grounded. `Technical Writing (updated).pdf` p.1 identifies some advice as personal preference; the Helsinki guide p.2 says conventions vary by institute, supervisor, forum, and field; Bates p.5 describes its format as general and adaptable; and Gopen and Swan p.12 explicitly describe their reader-expectation guidance as principles rather than fixed rules. These sources support keeping stylistic choices flexible.

The hard integrity constraints have a different basis. *On Being a Scientist* pp.10 and 27-28 grounds accurate reporting, evidence strength, method disclosure, and permanent records in the trust structure of science; pp.48-49 grounds accurate citation and original-source checking. The Machine Learning Reproducibility Checklist p.1 requires explicit claims, assumptions, dataset details, run counts, measures, variation, dependencies, and computing conditions. These justify low-freedom safeguards.

## Source Foundations

`skills/research-writing/references/source-foundations.md` will contain an original synthesis, not copied handbook prose. Each entry will record:

1. the principle;
2. source type and authority;
3. supplied PDF and page that introduced or indexed it;
4. verified extension document and exact PDF page or section;
5. the resulting Skill rule;
6. applicability limits or conflicting advice;
7. canonical public URL and access date.

The initial matrix will cover at least these verified sources:

| Source | Verified design contribution |
| --- | --- |
| Simon Peyton Jones, *How to Write a Great Research Paper*, pp.4-7, 12-24, 36-45 | Write early, identify the central idea, make contributions explicit and refutable, connect claims to evidence, and put the reader first |
| George Whitesides, *Writing a Paper*, pp.1-3 | Treat the outline as a research plan, organize around data, start early, order by importance, and make conclusions add higher-level significance |
| Mike Ashby, *How to Write a Paper*, pp.4-14 | Design for audience, use a concept sheet, draft non-sequentially, separate section purposes, preserve limitations in conclusions |
| Gopen and Swan, *The Science of Scientific Writing*, pp.4-12 | Use subject-verb proximity, topic and stress positions, old-to-new flow, and reader expectations as revisable principles rather than algorithms |
| Knuth, Larrabee, and Roberts, *Mathematical Writing*, pp.4-7 and 114 | Motivate what follows, keep the reader's state in mind, use consistent notation, preserve precision, organize without distracting |
| Helsinki *Scientific Writing Guide*, pp.2-14 | Treat conventions as field-sensitive, use research questions as a structural backbone, distinguish results from discussion, and state validity limits |
| Bates *How to Write Guide*, pp.5, 9-16, 29-30, 59 | Organize and revise iteratively, make figures self-contained, connect statistical support to reported results, and treat wording advice as guidance rather than dogma |
| NASA SP-7084, pp.19, 36-52 | Prefer clear subjects and vigorous verbs, use active voice contextually, preserve parallelism, and distinguish concision from merely minimizing words |
| Machine Learning Reproducibility Checklist, pp.1-2 | Report assumptions, proofs, data splits, exclusions, dependencies, run counts, measures, variation, runtime, and infrastructure |
| *On Being a Scientist*, pp.10, 27-31, 48-49, 70, 73 | Do not make the record stronger than the data, disclose methods and exclusions, correct errors, cite original work accurately, and value coherent contribution over paper count |
| `Technical Writing (updated).pdf`, pp.1-8 | Use roadmaps, contribution questions, explicit assumptions, figure-level messages, defined notation, and reader guidance while marking author preferences as optional |

`writing words.pdf` is a restricted local source. The repository will record only its title/edition metadata, the previously recorded redistribution boundary, and the official Manchester Academic Phrasebank URL. Its body, phrase lists, tables, examples, and derivatives will not be read into the Skill, quoted, paraphrased as a source-specific template, or included in tests.

## Repository Architecture

```text
README.md
LICENSE
CONTRIBUTING.md
SECURITY.md
THIRD_PARTY_NOTICES.md
requirements.txt
release-manifest.txt
.github/
  workflows/
    ci.yml
skills/
  research-writing/
    SKILL.md
    agents/
      openai.yaml
    assets/
      writing-brief.md
      evidence-ledger.csv
    references/
      writing-workflow.md
      section-guides.md
      revision-and-style.md
      evidence-and-integrity.md
      source-foundations.md
tools/
  corpus.py
  validate_repository.py
  build_release.py
tests/
  test_corpus.py
  test_repository.py
evals/
  cases/
  baseline/
  forward/
  runs/
  rubric.md
  comparison.md
docs/
  corpus-synthesis.md
  skill-design-review.md
  superpowers/
ara/
doc/
```

Only `skills/research-writing/` is an installable Agent Skill. Repository documentation, tools, tests, evaluations, `ara/`, and `doc/` are not copied into the Skill installation.

## Runtime Skill Design

### Metadata

The frontmatter will retain only `name` and `description`. The description will continue to describe triggering situations rather than summarizing the workflow. `agents/openai.yaml` will be regenerated or verified against the final Skill text.

### Core body

`SKILL.md` will retain:

- the evidence ceiling;
- reference routing;
- proportional operating depth;
- non-fabrication and semantic-preservation rules;
- the minimal Frame, Ledger, Structure, Draft, Revise, Audit, Deliver workflow;
- the compression safety gate;
- the output contract and completion check.

Detailed section advice, examples, source rationale, and ledger semantics remain in references. Repetition between the core and references will be removed unless an instruction is tied to a demonstrated critical failure and therefore needs to remain visible.

The refactored core should fit within roughly 700 whitespace-delimited words. Genre tables, evidence-state tables, and long examples belong in directly linked references so ordinary invocations do not pay their context cost.

### Genre-aware structure

The former mandatory story arc becomes a default selection rule:

- contribution paper: problem -> gap -> insight -> contribution;
- empirical study: question -> design -> observation -> interpretation -> limits;
- replication or negative result: prior claim -> replication design -> result -> discrepancy/confirmation -> boundary;
- survey: scope -> organizing lens -> synthesis -> unresolved questions;
- methods or data paper: need -> artifact/method -> validation -> usage boundary;
- revision-only task: preserve the supplied local structure unless the user requests restructuring.

These are starting patterns, not required headings.

## Development Tool Boundary

`tools/corpus.py` remains available for local inventory, URL extraction, downloading, hashing, and verification. It is not part of the writing Skill and is not required to install or invoke the Skill.

The public repository validator will not depend on the nine local PDFs. Full-corpus verification remains an optional local integration check. Unit tests will use synthetic, redistributable PDF fixtures created at runtime.

## Licensing and Publication Boundary

The recommended project license is Apache License 2.0 for original repository code, Skill instructions, templates, and original documentation. `THIRD_PARTY_NOTICES.md` will state that supplied/downloaded documents and third-party source material are not covered by that license.

`doc/` will remain untouched. It is a local evidence corpus, not a release input. A release must be built only from `release-manifest.txt`; copying or zipping the working directory is unsupported.

Four `doc/source-index` files are currently tracked and contain extracted source context. This refactor will not edit or untrack them because of the explicit no-touch constraint. Therefore:

- the supported open-source distribution is the allowlisted release artifact;
- CI must prove that no `doc/` path enters that artifact;
- README and third-party notices must disclose that `doc/` is outside the licensed Skill distribution;
- publishing the complete Git history, including tracked source context, still requires a separate rights review outside this task.

## Validation and Evaluation

Changes will follow RED-GREEN-REFACTOR.

### RED

Before migration or Skill edits, add failing repository tests that require:

- the new package path;
- valid frontmatter and agent metadata;
- resolvable direct references;
- the canonical evidence-ledger schema;
- a source-foundations matrix with page-level provenance;
- a release allowlist that excludes `doc/`, `ara/`, `evals/`, PDFs, and local absolute paths;
- no development-only files in the Skill package.

Add evaluation cases for proportional one-sentence editing, genre-sensitive structure selection, and source-rationale retrieval before modifying the Skill behavior.

Preserve earlier baseline and forward artifacts unchanged. New forward runs live under an immutable dated `evals/runs/<run-id>/` directory with the exact Skill revision, date, case path, raw output, and model identifier when the runner exposes it.

### GREEN

Move existing files to the approved boundaries and make the smallest Skill changes that satisfy the failing tests and new cases. Preserve the four existing evaluation cases unchanged so earlier integrity behavior remains comparable.

### REFACTOR

Remove duplicated instructions, align terminology, and tighten reference routing. Re-run the affected forward cases with fresh agents and record raw outputs and run metadata.

### Completion gates

1. All unit and repository tests pass on Windows and Linux CI.
2. The official local Skill validator passes for `skills/research-writing/`.
3. Every link from `SKILL.md` resolves directly.
4. Existing four-case critical failures remain zero.
5. New cases demonstrate proportionality, genre flexibility, and source retrieval without weakening integrity safeguards.
6. The release builder includes only allowlisted files and contains no PDF, `doc/`, `ara/`, `evals/`, local absolute path, or restricted text.
7. The pre- and post-refactor `doc/` file count, byte count, relative paths, sizes, timestamps, per-file content SHA-256 values, and aggregate metadata/content fingerprints match.
8. Git status is reviewed so unrelated user files are not included.

## Error Handling

- If a source cannot be opened or its page cannot be verified, mark the matrix entry `not verified`; do not infer its principle from the title.
- If two guides conflict, preserve both positions, identify their scope, and keep the Skill rule at the least universal level justified by the evidence.
- If a canonical URL is unavailable, retain the verified bibliographic identity and record the unavailable link rather than substituting an unknown mirror.
- If a release file is not allowlisted, fail the build instead of silently including it.
- If `doc/` metadata changes at any point, stop the migration, report the exact paths, and restore only with explicit user authorization.
- If a shorter response would require dropping a conclusion-changing qualifier, return the shortest faithful alternative rather than satisfying the length mechanically.

## Tradeoffs

The repository shell adds several maintenance files and a release step, but it keeps the installed Skill small and makes the publication boundary inspectable. Moving the corpus tool outside the Skill reduces apparent feature breadth, but more accurately represents V1 as a writing capability. Adding source foundations increases reference material, but progressive disclosure prevents that cost from affecting ordinary writing tasks.

The no-touch rule for `doc/` prevents fully correcting the tracked-context licensing risk in this refactor. The design contains that risk at release time and documents it honestly rather than implying that the entire working tree is redistributable.

## Acceptance Result

The refactor is accepted when a contributor can clone the repository, understand and test it from the README, install only `skills/research-writing/`, reproduce deterministic validation in CI, inspect the source basis of every major writing rule, and build an allowlisted release without changing or packaging `doc/`.
