# Constraints and Limitations

## Evidence and writing boundaries

- The Skill cannot create missing experiments, citations, quotations, datasets, numerical results, or source locations.
- Ledger status still depends on accurate source inspection by the user or agent; fluent summaries are not independent verification.
- Meaning-atom extraction is judgment-heavy and is represented as structured input in the execution stub rather than solved by a deterministic parser.
- Causal claims require an appropriate design and analysis; a before/after observation alone remains descriptive or associative.

## Evaluation boundaries

- The baseline/forward comparison contains only four synthetic fixtures.
- The forward-run model identity and reasoning setting are not specified in the preserved files.
- Descriptive rubric totals are evaluator judgments, not statistical estimates.
- Zero critical failures in the fixtures does not imply zero failure risk on real papers, other disciplines, languages, models, or adversarial prompts.

## Corpus boundaries

- URL availability is time-dependent. The recorded network and HTTP failures are point-in-time observations.
- `verify_inventory` checks successful local paths and hashes; it does not establish semantic quality, authenticity, citation relevance, or license status.
- Candidate selection favors explicit document endpoints and can omit useful dynamic pages that do not expose a direct artifact.
- OCR is deferred; low-text scanned documents may require a separate OCR workflow.
- The downloader validates PDF magic bytes for PDF candidates but does not perform malware analysis or full-format conformance checking.
- Byte budgets and network retries limit resource use but may leave large or intermittently available sources unresolved.

## Licensing and repository boundaries

- `writing words.pdf` is local-only and restricted. This ARA contains no excerpt, phrase list, table, derivative corpus, or reconstructed wording from it.
- Downloaded binaries remain local and untracked until licenses are reviewed; download success is not redistribution authorization.
- This artifact records a conservative engineering policy, not legal advice.

## Product boundaries

- V1 is an Agent Skill plus deterministic helper script, not a persistent Harness, networked MCP server, publisher submission system, or universal citation manager.
- Long-running state, multi-agent orchestration, and external service authentication are deferred.
- Authors, venue, DOI, training configurations, learned weights, and hardware requirements are not specified because they are not applicable or absent from the provided project.
