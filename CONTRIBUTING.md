# Contributing

Contributions should preserve a portable, evidence-grounded writing Skill and a reproducible release boundary.

## Development Setup

Use Python 3.12. Install the declared project requirements, then run the complete suite, repository validator, and release builder:

```bash
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
python tools/validate_repository.py
python tools/build_release.py
```

## Skill Changes

For Skill behavior changes, use RED-GREEN-REFACTOR: choose a failing static test or a fresh-agent baseline, and observe the RED result when applicable. Add a failing static test or a fresh-agent baseline before changing Skill behavior. Ordinary documentation, security, and configuration changes need only their corresponding static contract tests. Preserve raw evaluation output, use the existing rubric, and do not rewrite a case after seeing the forward result. Keep `SKILL.md` concise and link directly to the reference that supplies detail.

## Source and Copyright Rules

Do not add PDFs, large excerpts, phrase lists, handbook tables, unknown mirrors, or material with unclear rights. Prefer bibliographic facts, page pointers, canonical URLs, and original synthesis. Ordinary changes must not modify `doc/`.

## Pull Request Checklist

- [ ] A behavior change has a failing static test or fresh-agent baseline, with its RED result observed when applicable; ordinary documentation, security, and configuration changes have the corresponding static contract test.
- [ ] `python tools/validate_repository.py` passes.
- [ ] The release builder produces an allowlisted archive.
- [ ] No development artifact or local path is included in the archive.
- [ ] Every writing rule has a source basis and an explicit boundary.
- [ ] Evaluation claims are bounded to their recorded scope.
