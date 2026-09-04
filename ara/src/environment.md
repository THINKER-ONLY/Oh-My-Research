# Environment

- **Python**: 3.12 specified by the implementation plan; exact patch version not recorded
- **Framework**: Not applicable; standard-library Python script with PyMuPDF (`fitz`) and `requests`
- **Hardware**: Not specified; no GPU requirement is documented
- **Key dependencies**: PyMuPDF and `requests`; exact installed versions are not specified in the provided project files
- **Random seeds**: Not applicable
- **Operating system**: Windows/PowerShell workspace observed for the recorded validation; portable Skill behavior is not intended to be OS-specific
- **Network**: Required only for new downloads; inventory parsing, resumption checks, tests, and local verification can operate without external network access
- **Source**: `docs/superpowers/plans/2026-08-06-research-writing-skill-v1.md`, Tech Stack; `research-writing/scripts/corpus.py`
