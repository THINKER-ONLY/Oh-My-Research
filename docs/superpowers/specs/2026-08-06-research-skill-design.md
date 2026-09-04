# Open Research Writing Skill Design

## Purpose

Build an open-source, portable research skill whose first complete capability is evidence-grounded academic writing. The project must also turn the supplied research corpus into a local, traceable source library without redistributing restricted material.

## Success Criteria

1. Inspect all nine supplied PDFs and preserve a source-level synthesis for each.
2. Extract embedded links with page provenance, normalize and deduplicate them, and attempt every credible downloadable document candidate.
3. Store successful downloads under a small topic taxonomy in `doc/`, with checksums, source URLs, retrieval status, and failure reasons.
4. Keep restricted material available only as local input; do not copy its protected text into the open-source skill.
5. Deliver a valid portable Agent Skill that can plan, draft, revise, and audit a research manuscript without inventing claims or citations.
6. Demonstrate through forward tests that the skill improves traceability, structure, and sentence-level revision over an unassisted baseline.

## Scope

### Included in V1

- Research-writing intake and writing brief
- Evidence and claim ledger
- Paper story and outline construction
- Section-aware drafting for abstract, introduction, related work, methods, experiments/results, discussion, and conclusion
- Paragraph- and sentence-level revision
- Citation and research-integrity checks
- Deterministic corpus inventory, URL extraction, downloading, hashing, and manifest generation
- Corpus synthesis with source/page pointers and license notes
- Portable Skill metadata and validation
- Baseline and forward evaluation fixtures

### Deferred

- A standalone long-running agent runtime
- A networked MCP server
- Automated publisher submission
- OCR installation and scanned-document recognition
- A universal citation-manager replacement
- Mirroring every mutable web page into the repository

## Architecture

The V1 is a portable Agent Skill with deterministic helper scripts. The skill owns procedural judgment; scripts own repeatable operations such as URL extraction, downloads, checksum calculation, and manifest validation. Large or topic-specific guidance lives in references and is loaded only when the active writing phase requires it.

```text
User request + research artifacts
          |
          v
research-writing/SKILL.md
  |       |         |
  v       v         v
brief   evidence   writing/revision workflow
  |       |         |
  +-------+---------+
          |
          v
draft + evidence ledger + audit report

Local corpus PDFs -> corpus tool -> doc/topic folders + source manifest
                                      |
                                      v
                              synthesis and references
```

## Repository Layout

```text
research-writing/
  SKILL.md
  agents/openai.yaml
  scripts/
    corpus.py
  references/
    writing-workflow.md
    section-guides.md
    revision-and-style.md
    evidence-and-integrity.md
  assets/
    writing-brief.md
    evidence-ledger.csv
  evals/
    cases/
    rubric.md
doc/
  writing/
  research-methods/
  agent-systems/
  auto-research/
  source-index/
docs/
  corpus-synthesis.md
  superpowers/specs/
  superpowers/plans/
tests/
  test_corpus.py
ara/
  ... research provenance artifact
```

The topic taxonomy is intentionally small. A document receives one primary category, while the manifest records all secondary tags.

## Corpus Pipeline

1. Read every local PDF with PyMuPDF and extract metadata, page text, and link annotations.
2. Treat annotation URIs as authoritative; use visible-text URL extraction only as a supplement.
3. Reject known example or unsafe targets, including the `evil.com` prompt-injection example in the Agent book.
4. Normalize URLs while retaining the exact original URL and source PDF/page.
5. Probe direct-document candidates with redirects, timeouts, retries, and a descriptive user agent.
6. Stream downloads into temporary files, enforce per-file and total byte limits, verify PDF/file signatures, and compute SHA-256 before final placement.
7. Deduplicate identical bytes while preserving every source-to-file relationship in the manifest.
8. Record unavailable, blocked, oversized, non-document, and license-restricted outcomes without treating them as successful downloads.
9. Preserve dynamic HTML sources as indexed links unless they expose an explicit downloadable artifact. This avoids creating an unlicensed web mirror.

## Writing Workflow

The skill follows a gated writing sequence:

1. **Frame**: establish audience, venue, language, artifact type, research question, contribution, and available evidence.
2. **Ledger**: map each intended claim to evidence, source location, confidence, citation status, and unresolved gaps.
3. **Story**: construct the problem-gap-insight-contribution arc and a section outline before prose.
4. **Draft**: write one section at a time from approved claims; label unsupported material instead of filling gaps.
5. **Revise structure**: check section purpose, paragraph topic flow, transitions, figure/table references, and redundancy.
6. **Revise sentences**: prefer precise subjects and verbs, control qualifiers, remove empty emphasis, define notation before use, and preserve the author's meaning.
7. **Audit**: verify claim-evidence alignment, citation identity, numerical fidelity, limitations, and reproducibility statements.
8. **Deliver**: return the draft, evidence ledger, unresolved-issues list, and a concise revision log.

The workflow may begin from notes, an outline, an existing draft, a paper, code, results, or a mixed project directory. It must never imply that polished prose compensates for missing evidence.

## Source and Copyright Policy

- The Manchester Academic Phrasebank enhanced PDF explicitly prohibits electronic redistribution. Its text remains local-only and is not copied into the skill, test fixtures, documentation, or Git history.
- Public sources are cited by canonical URL and retrieval date. Downloading a file does not by itself establish redistribution rights.
- Downloaded documents remain untracked by default until their license is known.
- The open-source skill contains original procedural synthesis, short attributed facts where appropriate, and links rather than copied handbooks.
- Claims derived from a source retain page or section provenance whenever extraction supports it.

## Error Handling

- Network failures are retried only for transient statuses and then recorded with the final reason.
- A response advertised as PDF but lacking a PDF signature is rejected.
- Filename collisions use stable source identifiers; byte-identical files deduplicate by SHA-256.
- Malformed URLs remain in the inventory with a parse error and are never guessed into a different target.
- Low-text PDFs are flagged for OCR rather than silently treated as empty. OCR is deferred because no OCR engine is installed.
- Missing writing evidence produces an explicit gap, question, or placeholder in an issue ledger, never a fabricated sentence or citation.

## Testing Strategy

### Corpus Tool

- Unit tests cover annotation extraction, unsafe URL rejection, normalization, classification, filename sanitization, PDF signature checks, hashing, deduplication, and manifest output.
- HTTP behavior uses a local test server so tests do not depend on external availability.
- An integration run processes all nine local PDFs and verifies that every input appears in the manifest.

### Skill

- RED: run realistic writing prompts without the skill and preserve the baseline outputs and observed failures.
- GREEN: run the same prompts with the skill and score both outputs with a fixed rubric.
- REFACTOR: tighten instructions where agents still skip evidence mapping, overstate claims, or edit prose without preserving meaning.
- Rubric dimensions: requirement capture, evidence traceability, structural coherence, sentence quality, citation integrity, uncertainty handling, and useful deliverables.

### Completion Gates

- Skill validation passes.
- All corpus-tool tests pass.
- The full corpus inventory and download run completes with a machine-readable manifest.
- Every successful download has a hash and provenance record.
- Every failed candidate has a status and reason.
- Forward tests show no critical integrity violation and improve the targeted baseline failures.

## Future Extension Points

- Expose corpus search and evidence-ledger operations as MCP tools when multiple hosts need them.
- Add a persistent Harness when long-running literature review and experiment loops require resumable state, budgets, and observability.
- Add venue-specific references and language variants as progressive-disclosure modules rather than expanding the core skill.
