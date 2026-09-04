# Observed Skill structure audit

**Source**: `research-writing/SKILL.md`, `research-writing/agents/openai.yaml`, four files under `research-writing/references/`, two files under `research-writing/assets/`, and the official Skill validator

**Caption**: Exact local structure and link-resolution observations for the portable research-writing Skill at pre-ARA tracked commit `f4ddb534adbfff99d1dbe8a041cffff08549bdaf`.

**Extraction type**: raw_project_observation_with_structural_audit

| Audit item | Exact observed value |
| --- | --- |
| Required frontmatter fields | `name` and `description` present |
| Ordered workflow gates | 7: Frame, Ledger, Story, Draft, Revise, Audit, Deliver |
| Numbered non-negotiable rules | 7 |
| Linked reference files | 4 present, 0 missing |
| Linked reusable assets | 2 present, 0 missing |
| Agent metadata | `research-writing/agents/openai.yaml` present |
| Official validator exit code | 0 |
| Official validator result | `Skill is valid!` |

This audit establishes package structure and link presence. It does not establish general writing effectiveness.
