# Training Configuration

This artifact does not train or fine-tune a model.

## Training procedure

- **Value**: Not applicable
- **Rationale**: The deliverable is a portable instruction Skill and deterministic Python corpus tool, not learned weights.
- **Search range**: Not applicable
- **Sensitivity**: Not applicable
- **Source**: `docs/superpowers/specs/2026-08-06-research-skill-design.md`, Architecture and Deferred scope

## Optimization hyperparameters

- **Value**: Not applicable
- **Rationale**: No optimizer, learning rate, batch size, epoch count, or loss function appears in the provided project.
- **Search range**: Not applicable
- **Sensitivity**: Not applicable
- **Source**: Not specified because no training experiment exists

## Random seed

- **Value**: Not applicable
- **Rationale**: Current checks are deterministic unit/structural/manifest validations rather than stochastic training runs.
- **Search range**: Not applicable
- **Sensitivity**: Not applicable
- **Source**: `tests/test_corpus.py` and the documented validation commands
