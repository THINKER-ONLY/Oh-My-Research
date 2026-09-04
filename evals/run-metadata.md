# Evaluation Run Metadata

- Legacy Cases 01-04 preserve their raw baseline and forward outputs. The baseline artifacts identify `gpt-5.6-terra`, with reasoning `high` for Cases 01-03 and `low` for Case 04; the forward artifacts do not record model identity.
- Beyond those baseline reasoning labels, the legacy artifacts do not expose decoding parameters or exact runner commands. Those details were not recorded and must not be reconstructed from memory.
- The formal post-refactor run described below did not complete a case and therefore supplies no new case scores. Cases 05-07 must not be assigned scores from this run.
- Comparison totals are descriptive smoke-test results, not a benchmark or causal experiment.

## Formal run: blocked before a scorable case

The latest recorded attempt is intentionally retained as a failure record rather than converted into a score.

| Field | Recorded value |
| --- | --- |
| Run ID | `2026-08-31-formal-custom-5dea777` |
| UTC interval | `2026-08-31T13:57:11.613306Z` to `2026-08-31T13:58:42.439589Z` (90.82799999997951 s) |
| Commit | `5dea7779d3ac5d810d14c417828d2cfda656a5e4` |
| Root tree | `dec7e22c542467cfaf6f6145a739501684b1dc2f` |
| Runner blob (`tools/run_evals.py`) | `c6a10d9a9ae26d3d914a8c3e20931656b5cb9a48` |
| Runner SHA-256 | `7ca26ddf847f7cf44786821b7593f0883a7c67ed8217c549acb201611e9fbb0e` |
| Config blob (`evals/runner-config.json`) | `bbc5377dd7ad7ae1e8959cd5bd4a1e62c3d7f98d` |
| Skill tree | `340a55f6f013dd0902f28a7df9e306e8a4367f7a` |
| Codex executable | `codex-cli 0.147.0-alpha.6.5`; length `293478192`; SHA-256 `115518500b45188e410a15d3224c2bbc87df6f2209729bf327aaf7808ca9d5a6` |
| Provider/model | Configured alias `custom`; model `gpt-5.6-sol`; the operator's temporary configuration used a custom Responses endpoint. No API key is recorded here. |
| Preflight | Passed: version, feature, MCP, and plugin probes returned zero. |
| Case result | Case `01-outline` stopped at `case:01-outline:audit-events`; no valid forward score. Cases 02-07 were not run. |

The case artifacts are retained outside the repository for audit. Their recorded hashes are: `prompt.bin` (862 bytes, `b417bacfd1351b1c5730f64230ba1cc03b86897f46669f66a6efbc2f45fecaf9`), `events.jsonl` (10515 bytes, `d10d94e1a2ca93cc295ca8678f41671de1b176f4be3948cdb32a6e96333c7d6a`), `stderr.bin` (2929 bytes, `68cd72c62c152d0d295cda1a1050004a3138ea87e0120b5819709d830c9d1121`), `raw.md` (155 bytes, `6418ee89587eb49064362083e9f88de4148df00336c583bde80c9037337d9f3d`), and `audit.json` (6786 bytes, `b5df7982f4bef369a52522762af0c51c661826e547ec1f8470f768bc50bd20ce`). The manifest hash is `158e01cfd2f4c50765a3cf92c46847d896d782d45de55ff11d50e7fb0fe64147`.

### Why the run is not scorable

The pinned CLI requires the global `--ask-for-approval never` option before the `exec` subcommand; the runner now places it correctly. Strict config loading also depends on the caller's Codex home. The ordinary user config on this machine contains the stale `disable_response_storage` field, so a clean temporary `CODEX_HOME` was used for the successful preflight. This home and the provider endpoint are environment-specific and are not part of the Skill release.

The model then emitted Windows shell-wrapper commands such as an absolute `powershell.exe -Command 'Get-Content -LiteralPath case.md'`. The command failed with exit code `-65536` and UTF-16-looking output. The runner's intentionally small grammar accepts only the canonical relative read forms, so it rejected the event stream with `command_execution is not in the small read-only command grammar`. This is a harness/CLI interoperability failure, not evidence about Skill quality. It leaves the raw response unusable for rubric scoring.

The custom provider is also not interchangeable with OpenAI's hosted provider: the local API key used by the operator authenticated against the custom endpoint and returned `401` against `api.openai.com`. Reproducing this run requires the caller to supply their own valid credentials and provider configuration; credentials must never be copied into manifests, logs, prompts, or commits.

Until a run completes all seven cases with a documented command grammar and independently audited artifacts, the repository makes no post-refactor forward-quality claim.
