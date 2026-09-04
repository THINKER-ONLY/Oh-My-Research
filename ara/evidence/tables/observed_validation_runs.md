# Observed validation runs

**Source**: Fresh local execution in `C:\Users\31933\Desktop\Oh-My-Research` on 2026-08-06, with `PYTHONDONTWRITEBYTECODE=1`

**Caption**: Exact command exit states and high-level outputs captured immediately before ARA generation, anchored to the tracked pre-ARA tree.

**Extraction type**: raw_execution_observation

| Command | Exit code | Exact observed result |
| --- | ---: | --- |
| `git rev-parse HEAD` | 0 | `f4ddb534adbfff99d1dbe8a041cffff08549bdaf` |
| `git diff --check` | 0 | No output; no whitespace error reported in the pre-ARA tracked/untracked worktree |
| `python -m unittest tests.test_corpus -v` | 0 | 17 tests ran in 1.951s; all reported `ok`; final result `OK` |
| `python C:\Users\31933\.codex\skills\.system\skill-creator\scripts\quick_validate.py research-writing` | 0 | `Skill is valid!` |
| `python research-writing/scripts/corpus.py verify --index doc/source-index/inventory.json --doc doc` | 0 | `{"ok": true, "errors": []}` |

The full stdout/stderr transcript was not retained as a separate log; this table is a contemporaneous command summary tied to the recorded Git anchor. Execution time is an observed runtime detail, not a performance guarantee.
