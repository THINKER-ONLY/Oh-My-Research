# Research-Writing Skill Design Review

## Verdict

The V1 integrity core addresses the observed critical failures in its fixed smoke cases. That evidence is narrow. The current package makes the repository boundary, source traceability, canonical evidence vocabulary, and genre-aware structure selection explicit; it does not turn the fixed smoke result into a general quality claim.

## What remains hard-constrained

Citation identity, quotation fidelity, numbers, units, causal force, claim scope, and conclusion-changing limitations remain low-freedom rules because mistakes are difficult to detect after fluent prose is produced.

## What becomes adaptable

The `Structure` phase selects an outline appropriate to genre, venue, field, and user intent. Problem-gap-contribution storytelling, IMRaD order, active voice, topic/stress-position heuristics, and section-level conventions remain adaptable defaults rather than universal requirements.

## Resolved design defects

The repository separates runtime files from development evidence and tooling, uses one canonical evidence-ledger schema with separate claim type, support status, and citation status axes, records atomic page-level source provenance in a two-layer source matrix, and builds releases from an explicit allowlist. The matrix separates the supplied-PDF locator from the verified extension-document locator for each principle-source contribution. The current genre-aware Structure phase (`Structure`) keeps evidence safeguards distinct from adaptable presentation choices.

## Progressive-disclosure audit

The current core is at most 700 words. It conditionally routes the bundled source-foundations matrix: the matrix is loaded only for rationale, adaptation, or design-audit requests and is not loaded for ordinary drafting or revision. The matrix is a limited runtime rationale reference, distinct from broader development provenance records such as corpus acquisition, evaluations, tests, release tooling, and research traces, which remain outside the Skill.

## Why V1 is a Skill, not a harness or MCP server

Writing guidance is primarily procedural knowledge plus reusable templates. V1 has no demonstrated need for a persistent service, MCP protocol, background state, or autonomous multi-agent runtime. Adding those components now would increase permissions, dependencies, and maintenance without improving the tested writing cases.

## Known boundary

`doc/` remains unchanged and excluded from the release. The source matrix explicitly preserves unresolved upstream introducing/indexing locator gaps rather than implying that they were verified. Replacing those markers requires a separately authorized corpus audit. The four tracked source-index files still require a separate rights review before publishing the complete Git history; this refactor licenses and supports the allowlisted Skill artifact, not the local evidence corpus.

## Evaluation limit

The evaluations are narrow smoke tests. Improvements on fixed cases show that the safeguards address observed failures, but they do not establish universal writing-quality gains or controlled causal effectiveness. No post-refactor forward evaluation results are claimed in this review.

The latest formal attempt (`2026-08-31-formal-custom-5dea777`, commit
`5dea7779d3ac5d810d14c417828d2cfda656a5e4`, root tree
`dec7e22c542467cfaf6f6145a739501684b1dc2f`, runner blob
`c6a10d9a9ae26d3d914a8c3e20931656b5cb9a48`) passed the pinned CLI preflight but
did not produce a scorable case. Case 01 failed during event auditing because
the Windows Codex client emitted an absolute `powershell.exe -Command` wrapper
for a read that the runner's small relative-path grammar could not accept; the
underlying command also returned `-65536` with UTF-16-looking output. Cases
02-07 were not run, so there is no seven-case score or post-refactor quality
claim to report. The archived four-case `37/64 -> 58/64` comparison remains a
descriptive historical smoke result only.

This failure exposes a design boundary in the evaluation harness, not a defect
in the Skill's writing rules. The harness must either normalize a narrowly
allowlisted Windows shell wrapper to the same relative read operation or make
the CLI emit a canonical command form. Permitting arbitrary shell text would
weaken the read-only audit and would be inconsistent with the repository's
evidence-first design.

The run also used a provider alias named `custom` and a temporary, sanitized
Codex home. This is deliberately not treated as a portable runtime
dependency: the operator's API key authenticated to a custom endpoint and was
not valid for `api.openai.com`, and no key or endpoint credential is bundled in
the Skill. A reproducible future evaluation must declare the provider/model,
temporary-home policy, strict-config behavior, exact argv, and artifact hashes
without recording secrets. Provider-specific success must not be presented as
provider-independent evidence.

## Remaining limitations

The source matrix is dominated by scientific and technical writing guidance, English-language conventions, and a small fixed evaluation set. The Skill does not validate statistics, retrieve paywalled sources, manage a bibliography database, or decide field-specific venue compliance without user-supplied rules. Future features should begin with a failing case rather than feature accumulation.
