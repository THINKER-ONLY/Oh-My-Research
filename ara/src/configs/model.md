# Model and Architecture Configuration

## Runtime language model

- **Value**: Not fixed by the portable Skill
- **Rationale**: `research-writing/SKILL.md` encodes host-independent workflow behavior.
- **Search range**: Not specified
- **Sensitivity**: high for empirical output quality; not measured beyond the preserved fixtures
- **Source**: `research-writing/SKILL.md`; `agents/openai.yaml`

## Agent topology

- **Value**: One portable Skill with deterministic helper script
- **Rationale**: V1 intentionally defers a persistent Harness, MCP server, and multi-agent runtime.
- **Search range**: Not evaluated
- **Sensitivity**: medium
- **Source**: `docs/superpowers/specs/2026-08-06-research-skill-design.md`, Architecture and Deferred scope

## Context-loading strategy

- **Value**: Core integrity rules always present; workflow, section, revision, and evidence references loaded by task need
- **Rationale**: Preserve critical gates while avoiding unnecessary context expansion.
- **Search range**: Not evaluated
- **Sensitivity**: medium
- **Source**: `research-writing/SKILL.md`, Load only what the task needs

## Baseline evaluation model metadata

- **Value**: `gpt-5.6-terra`; reasoning `high` for Cases 01–03 and `low` for Case 04
- **Rationale**: Preserved as observed baseline metadata, not selected as a production requirement.
- **Search range**: Not specified
- **Sensitivity**: high; no cross-model study was performed
- **Source**: `research-writing/evals/baseline/*.md`

## Forward evaluation model metadata

- **Value**: Not specified in the provided forward-output files
- **Rationale**: Inventing it would make the evaluation record less reliable.
- **Search range**: Not specified
- **Sensitivity**: unknown
- **Source**: `research-writing/evals/forward/*.md`
