# Observed restricted-source boundary

**Source**: `doc/source-index/inventory.json`, `research-writing/scripts/corpus.py`, and `tests/test_corpus.py`

**Caption**: Metadata-only audit of the restricted local source. The source PDF was not opened or quoted for this ARA.

**Extraction type**: derived_project_audit

| Audit item | Exact observed value |
| --- | --- |
| Restricted filename configured | `writing words.pdf` |
| Inventory link records from restricted source | 22 |
| Restricted records with non-redacted context | 0 |
| Stored context marker | `[restricted source context omitted]` |
| Redaction unit test | `test_extract_pdf_sources_redacts_restricted_context` — pass |
| Pre-download license guard in `run_downloads` | present |
| Protected phrase/text excerpts in this evidence file | 0 |

The only source-specific content retained is filename-level metadata, the omission marker, and the project-authored licensing decision.
