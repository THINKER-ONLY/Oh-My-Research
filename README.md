# Oh My Research

Oh My Research is an open-source, evidence-grounded research-writing Skill for Codex and compatible hosts.

## Install the Skill

V1 is a portable writing Skill. It is not an MCP server, an evaluation harness, an autonomous runtime, a citation manager, or a statistical package.

The recommended distribution is the deterministic ZIP produced by the release
builder. Extract its `research-writing/` directory into the host Skill
directory. Codex uses `$CODEX_HOME/skills/research-writing/` when `CODEX_HOME` is
set; when it is not set, use `~/.codex/skills/research-writing/`. Copying the
source directory is also supported for local development, but do not copy the
repository's development, evaluation, or corpus directories into a runtime
Skill installation.

## Use

Call the Skill with a focused request, for example:

```text
Use $research-writing to turn these notes and results into a traceable paper outline.
```

It supports proportional copyediting, shortening, section drafting, full-paper outlining, citation and integrity audits, and evidence-ledger work. It must not invent facts or citations; missing, uncertain, or conflicting evidence stays visible.

## Repository Layout

- `skills/research-writing/` is the portable runtime Skill.
- `tools/`, `tests/`, `evals/`, and `docs/` are development, validation, evaluation, and synthesis material; they are not runtime inputs.
- `ara/` contains research provenance and management material and is outside the runtime boundary.
- `doc/` contains controlled source and working material and is outside the runtime and release boundaries.

## Source Foundations

The writing rules are original synthesis grounded in multiple supplied PDFs and
verified extension documents. The bundled
`skills/research-writing/references/source-foundations.md` is a deliberately
selected, compact provenance subset: it maps the principles used by the Skill
to source locations and operational rules. It is not a copy of the collected
corpus, a substitute for the original works, or a claim that every linked
document was independently verified. See the [source-foundations matrix](skills/research-writing/references/source-foundations.md) for principle-to-page-to-rule provenance and [docs/corpus-synthesis.md](docs/corpus-synthesis.md) for the broader corpus overview.

## Validation

From the repository root, run:

```bash
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
python tools/validate_repository.py
python tools/build_release.py
```

Corpus verification is optional and can be run with `python tools/corpus.py verify --index doc/source-index/inventory.json --doc doc` when the local corpus is available.

## Release Boundary

Use `python tools/build_release.py --output dist/research-writing.zip` to build
the recommended release archive. The builder validates an explicit
`release-manifest.txt` allowlist and writes deterministic, stored ZIP members;
the archive contains only the legal notices and the nine runtime Skill files.
Releases exclude `doc/`, `ara/`, `tests/`, `evals/`, local absolute paths, and
PDFs, along with any other unallowlisted development files.

`doc/` is controlled source and working material collected during development,
not a runtime dependency or a redistribution grant. Do not publish or copy its
PDFs, downloaded documents, or index history merely because they are present in
the local checkout. The four tracked files under `doc/source-index/` still need
a separate rights review before their complete Git history can be shared. The
allowlisted Skill release and `THIRD_PARTY_NOTICES.md` document the narrower
license/attribution boundary; they do not clear rights for the local corpus.

## Evaluation Scope

The recorded smoke-test result is bounded to that smoke test: 37/64 -> 58/64, with 2 critical failures -> 0. It is not a general benchmark, a model comparison, or a production reliability claim.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development, source, and pull request rules.

## Security

See [SECURITY.md](SECURITY.md) for private reporting and safe reproduction guidance.

## License

This project is distributed under the Apache License 2.0; see [LICENSE](LICENSE). Additional attribution is recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
