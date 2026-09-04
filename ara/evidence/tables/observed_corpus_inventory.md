# Observed corpus inventory and download summary

**Source**: `doc/source-index/inventory.json`, generated at `2026-08-06T09:57:51.915142+00:00`

**Caption**: Exact stored manifest fields and deterministic consistency checks computed over the full current JSON object.

**Extraction type**: raw_project_observation_with_derived_audit

## Raw top-level and summary values

| Field | Exact value |
| --- | ---: |
| inputs | 9 |
| links | 583 |
| candidates | 80 |
| blocked | 20 |
| downloads | 80 |
| download_summary.attempted | 80 |
| download_summary.network_attempted | 11 |
| download_summary.retried | 11 |
| download_summary.downloaded | 70 |
| download_summary.deduplicated | 0 |
| download_summary.failed | 10 |
| download_summary.bytes | 174,784,070 |

## Candidate and successful-download topics

| Topic | Candidates | Downloaded | Failed |
| --- | ---: | ---: | ---: |
| agent-systems | 15 | 15 | 0 |
| auto-research | 5 | 5 | 0 |
| research-methods | 18 | 16 | 2 |
| writing | 42 | 34 | 8 |
| **Total** | **80** | **70** | **10** |

## Blocked and failure status counts

| Record family | Status | Exact count |
| --- | --- | ---: |
| blocked | blocked-domain | 1 |
| blocked | non-ascii-url | 19 |
| download failure | http-error | 6 |
| download failure | network-error | 3 |
| download failure | rejected-signature | 1 |

## Derived full-manifest consistency checks

| Check | Exact observed value |
| --- | ---: |
| Successful-record byte sum | 174,784,070 |
| Successful records missing SHA-256 | 0 |
| Successful records missing path | 0 |
| Duplicate candidate URLs | 0 |
| Duplicate download URLs | 0 |
| Candidate URLs without a download record | 0 |
| Download URLs without a candidate record | 0 |

These values establish manifest consistency only. They do not establish semantic quality, source authenticity, licensing, or future network availability.
