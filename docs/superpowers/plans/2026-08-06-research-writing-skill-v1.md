# Research Writing Skill V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate a portable evidence-grounded research-writing skill while archiving every credible downloadable document referenced by the supplied PDF corpus.

**Architecture:** A single Python corpus tool owns deterministic PDF-link extraction, URL filtering, downloading, hashing, and manifests. A portable Agent Skill owns the judgment-heavy writing workflow and progressively loads focused references. Downloaded binaries stay local and untracked; source metadata, synthesis, tests, and the skill are versioned.

**Tech Stack:** Python 3.12 standard library, PyMuPDF (`fitz`), `requests`, `unittest`, Markdown, YAML

---

## File Map

- `.gitignore`: exclude downloaded binaries, temporary files, caches, and restricted local sources from Git.
- `tests/test_corpus.py`: behavior tests for inventory and download operations.
- `research-writing/scripts/corpus.py`: corpus inventory/download CLI and reusable functions.
- `research-writing/SKILL.md`: concise trigger metadata and core writing gates.
- `research-writing/agents/openai.yaml`: product-facing skill metadata.
- `research-writing/references/*.md`: phase-specific writing, section, revision, and integrity guidance.
- `research-writing/assets/*`: reusable brief and evidence-ledger templates.
- `research-writing/evals/*`: baseline/forward cases, outputs, and scoring rubric.
- `doc/source-index/*`: local machine-readable download and provenance manifests.
- `docs/corpus-synthesis.md`: human-readable synthesis of all nine inputs and downloaded source families.
- `ara/*`: end-of-session provenance record.

### Task 1: Protect Local and Restricted Material

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Write the repository exclusions**

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
*.tmp
*.part

# Downloaded/reference binaries are local research inputs until their licenses are reviewed.
doc/writing/
doc/research-methods/
doc/agent-systems/
doc/auto-research/

# Supplied PDFs include material that is not redistributable.
/*.pdf
```

- [ ] **Step 2: Verify restricted inputs are ignored**

Run: `git check-ignore -v "writing words.pdf"`

Expected: `.gitignore` rule `/*.pdf` is reported.

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: protect local research sources"
```

### Task 2: Define Corpus Tool Behavior with Failing Tests

**Files:**
- Create: `tests/test_corpus.py`
- Create: `research-writing/scripts/corpus.py` after the RED run

- [ ] **Step 1: Write tests against the wished-for API**

```python
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "research-writing" / "scripts" / "corpus.py"


def load_module():
    spec = importlib.util.spec_from_file_location("corpus", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CorpusHelpersTest(unittest.TestCase):
    def test_normalize_url_removes_fragment_and_tracking(self):
        corpus = load_module()
        self.assertEqual(
            corpus.normalize_url("https://example.org/a.pdf?utm_source=x&id=7#page=2"),
            "https://example.org/a.pdf?id=7",
        )

    def test_rejects_unsafe_example_domain(self):
        corpus = load_module()
        self.assertEqual(corpus.url_rejection_reason("http://evil.com/payload"), "blocked-domain")

    def test_classifies_primary_topics(self):
        corpus = load_module()
        self.assertEqual(corpus.classify_source("Technical Writing", "paper writing"), "writing")
        self.assertEqual(corpus.classify_source("MCP specification", "agent tools"), "agent-systems")

    def test_pdf_signature_is_required(self):
        corpus = load_module()
        self.assertTrue(corpus.is_pdf_bytes(b"%PDF-1.7\n"))
        self.assertFalse(corpus.is_pdf_bytes(b"<html>login</html>"))

    def test_sanitized_filename_stays_portable(self):
        corpus = load_module()
        self.assertEqual(corpus.safe_filename("A:B / paper?.pdf"), "A-B-paper.pdf")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_corpus -v`

Expected: FAIL because `research-writing/scripts/corpus.py` does not exist.

- [ ] **Step 3: Commit the failing specification**

```bash
git add tests/test_corpus.py
git commit -m "test: specify corpus inventory behavior"
```

### Task 3: Implement Inventory and Download Primitives

**Files:**
- Create: `research-writing/scripts/corpus.py`
- Modify: `tests/test_corpus.py`

- [ ] **Step 1: Implement the minimal helper API**

```python
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

BLOCKED_DOMAINS = {"evil.com"}
TRACKING_KEYS = {"utm_campaign", "utm_content", "utm_medium", "utm_source", "utm_term"}


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                       if k.lower() not in TRACKING_KEYS])
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, query, ""))


def url_rejection_reason(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        return "unsupported-scheme"
    if (parts.hostname or "").lower() in BLOCKED_DOMAINS:
        return "blocked-domain"
    return None


def classify_source(title: str, context: str) -> str:
    text = f"{title} {context}".lower()
    if any(k in text for k in ("writing", "phrasebank", "论文", "写作")):
        return "writing"
    if any(k in text for k in ("agent", "skill", "harness", "mcp", "a2a")):
        return "agent-systems"
    if any(k in text for k in ("auto research", "ai scientist", "deep research")):
        return "auto-research"
    return "research-methods"


def is_pdf_bytes(prefix: bytes) -> bool:
    return prefix.startswith(b"%PDF-")


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[<>:\"/\\|?*]+", "-", name).replace(" ", "-")
    cleaned = re.sub(r"-+", "-", cleaned).strip(".-")
    return cleaned or "download"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

- [ ] **Step 2: Run tests and verify GREEN**

Run: `python -m unittest tests.test_corpus -v`

Expected: all helper tests PASS.

- [ ] **Step 3: Add real-PDF extraction and local-server download tests**

Append these concrete tests to `CorpusHelpersTest`:

```python
    def test_extract_pdf_sources_preserves_page_and_uri(self):
        corpus = load_module()
        import fitz
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "input.pdf"
            pdf = fitz.open()
            page = pdf.new_page()
            page.insert_text((72, 72), "source")
            page.insert_link({"kind": fitz.LINK_URI, "uri": "https://example.org/paper.pdf"})
            pdf.save(path)
            metadata, links = corpus.extract_pdf_sources(path)
        self.assertEqual(metadata["pages"], 1)
        self.assertEqual(links[0]["page"], 1)
        self.assertEqual(links[0]["url"], "https://example.org/paper.pdf")

    def test_download_document_rejects_html_payload(self):
        corpus = load_module()
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                payload = b"<html>not a PDF</html>"
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            def log_message(self, *_args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        try:
            with tempfile.TemporaryDirectory() as raw:
                result = corpus.download_document(
                    f"http://127.0.0.1:{server.server_port}/x.pdf",
                    Path(raw) / "x.pdf", 1024,
                )
            self.assertEqual(result["status"], "rejected-signature")
        finally:
            server.shutdown()
```

- [ ] **Step 4: Run the new tests and verify RED**

Run: `python -m unittest tests.test_corpus -v`

Expected: FAIL because extraction/download functions are missing.

- [ ] **Step 5: Implement extraction, probing, download, and manifests**

Implement the following concrete call contract in `corpus.py`; each function must return the shown fields so later tasks do not need to infer types.

```python
metadata, links = extract_pdf_sources(Path("source.pdf"))
# metadata: {"file", "title", "pages", "text_chars"}
# links: [{"url", "source_file", "page", "link_kind", "context"}]

candidate = is_download_candidate("https://example.org/report.pdf")
# candidate is True only for explicit document/download paths or known PDF hosts.

result = download_document(url, destination, max_bytes, session=None)
# result: {"url", "final_url", "status", "path", "bytes", "sha256", "content_type", "error"}

inventory = build_inventory(Path("."))
# inventory: {"generated_at", "inputs", "links", "candidates", "blocked"}

write_manifests(inventory, Path("doc/source-index"))
summary = run_downloads(inventory, Path("doc"), 200 * 1024**2, 3500 * 1024**2)
# summary: {"attempted", "downloaded", "deduplicated", "failed", "bytes"}
```

The implementation must stream in 1 MiB chunks, stop before `max_bytes`, retry only 429/5xx responses twice, write to a `.part` file, validate the `%PDF-` signature for PDF candidates, atomically rename successful files, and append one manifest row for every attempted URL.

The CLI exposes `inventory`, `download`, and `verify` subcommands through `argparse`.

- [ ] **Step 6: Run the full tests and verify GREEN**

Run: `python -m unittest tests.test_corpus -v`

Expected: all tests PASS with no network dependency.

- [ ] **Step 7: Commit**

```bash
git add research-writing/scripts/corpus.py tests/test_corpus.py
git commit -m "feat: add traceable corpus downloader"
```

### Task 4: Inventory and Download the Real Corpus

**Files:**
- Create: `doc/source-index/inventory.json`
- Create: `doc/source-index/sources.csv`
- Create: `doc/source-index/downloads.csv`
- Create: `doc/source-index/failures.csv`
- Create local binaries under: `doc/writing/`, `doc/research-methods/`, `doc/agent-systems/`, `doc/auto-research/`

- [ ] **Step 1: Build the inventory**

Run: `python research-writing/scripts/corpus.py inventory --input . --output doc/source-index`

Expected: nine local PDFs and all normalized annotation URLs appear in the manifests.

- [ ] **Step 2: Review the candidate set**

Run: `python research-writing/scripts/corpus.py verify --index doc/source-index/inventory.json`

Expected: no blocked-domain URL is eligible; malformed visible-text URLs remain non-downloadable records.

- [ ] **Step 3: Download all credible document candidates**

Run: `python research-writing/scripts/corpus.py download --index doc/source-index/inventory.json --doc doc --max-file-mb 200 --max-total-mb 3500`

Expected: successful artifacts are classified and hashed; failures are recorded without aborting the batch.

- [ ] **Step 4: Re-run verification**

Run: `python research-writing/scripts/corpus.py verify --index doc/source-index/inventory.json --doc doc`

Expected: every success points to an existing matching hash; every attempted failure has a reason.

### Task 5: Compile the Corpus Synthesis

**Files:**
- Create: `docs/corpus-synthesis.md`

- [ ] **Step 1: Read every supplied PDF and downloaded document index**

Capture per-source purpose, central claims or practices, writing-skill implications, conflicts, version caveats, and redistribution status. Use page-level source pointers for supplied PDFs.

- [ ] **Step 2: Write the cross-source synthesis**

Organize it as corpus overview, per-document summaries, convergent principles, disagreements/tensions, V1 design consequences, copyright notes, and download statistics.

- [ ] **Step 3: Verify coverage**

Run: `Select-String -Path docs/corpus-synthesis.md -Pattern 'AI-Agents-in-Depth|research_ai_sources|Research_资源全景图|Skill_Harness_MCP|Skill·Harness·MCP|Technical Writing|writing words|可直接下载|科研方法与前沿'`

Expected: all nine supplied filenames are represented.

- [ ] **Step 4: Commit metadata and synthesis**

```bash
git add doc/source-index docs/corpus-synthesis.md
git commit -m "docs: catalog and synthesize research corpus"
```

### Task 6: Establish a Failing Skill Baseline

**Files:**
- Create: `research-writing/evals/cases/01-outline.md`
- Create: `research-writing/evals/cases/02-revision.md`
- Create: `research-writing/evals/cases/03-integrity.md`
- Create: `research-writing/evals/rubric.md`
- Create: `research-writing/evals/baseline/*.md`

- [ ] **Step 1: Define three realistic prompts and the scoring rubric**

The cases test story-first outlining, meaning-preserving sentence revision, and refusal to fabricate evidence/citations. The rubric scores requirement capture, traceability, structure, sentence quality, citation integrity, uncertainty handling, and deliverables from 0 to 2, with any fabricated citation as a critical failure.

- [ ] **Step 2: Run fresh agents without the skill**

Save raw outputs under `evals/baseline/` and score only observable behavior. Record exact baseline omissions and rationalizations.

- [ ] **Step 3: Confirm RED**

Expected: at least one targeted behavior is absent or inconsistent, establishing a concrete reason for the skill.

- [ ] **Step 4: Commit baseline evidence**

```bash
git add research-writing/evals
git commit -m "test: capture research writing baseline"
```

### Task 7: Implement the Portable Skill

**Files:**
- Create: `research-writing/SKILL.md`
- Create: `research-writing/agents/openai.yaml`
- Create: `research-writing/references/writing-workflow.md`
- Create: `research-writing/references/section-guides.md`
- Create: `research-writing/references/revision-and-style.md`
- Create: `research-writing/references/evidence-and-integrity.md`
- Create: `research-writing/assets/writing-brief.md`
- Create: `research-writing/assets/evidence-ledger.csv`

- [ ] **Step 1: Initialize with the official skill scaffold**

Run `init_skill.py` with name `research-writing`, output path `.`, resources `scripts,references,assets`, and interface values:

```text
display_name=Research Writing
short_description=Evidence-grounded academic writing workflow
default_prompt=Use $research-writing to turn my research materials into a traceable paper draft.
```

Preserve the tested `scripts/corpus.py` when reconciling the generated scaffold.

- [ ] **Step 2: Write the minimal core skill**

The core contains only the Frame -> Ledger -> Story -> Draft -> Revise -> Audit -> Deliver gates, conditional reference-loading rules, non-fabrication requirements, and output contract. Detailed section/style guidance stays in references.

- [ ] **Step 3: Add original references and reusable assets**

Do not copy Academic Phrasebank text. Convert cross-source principles into original procedures and checklists with source citations in `docs/corpus-synthesis.md`.

- [ ] **Step 4: Generate and validate metadata**

Run: `python C:/Users/31933/.codex/skills/.system/skill-creator/scripts/quick_validate.py research-writing`

Expected: `Skill is valid!`

- [ ] **Step 5: Commit**

```bash
git add research-writing
git commit -m "feat: add evidence-grounded research writing skill"
```

### Task 8: Forward-Test, Refactor, and Record Provenance

**Files:**
- Create: `research-writing/evals/forward/*.md`
- Modify: `research-writing/SKILL.md` or one of `research-writing/references/*.md` only when a forward-test failure identifies a specific missing instruction
- Create: `ara/*`

- [ ] **Step 1: Run the same cases with the skill**

Use fresh agents with only the case and skill path. Save raw outputs and score with the unchanged rubric.

- [ ] **Step 2: Compare baseline and forward results**

Require zero fabricated citations, explicit evidence gaps, and improvement in every targeted baseline failure. Do not claim general quality gains outside the tested cases.

- [ ] **Step 3: Refactor and re-test any remaining loopholes**

Tighten only instructions tied to observed failures, then repeat affected cases.

- [ ] **Step 4: Run full verification**

```bash
python -m unittest tests.test_corpus -v
python C:/Users/31933/.codex/skills/.system/skill-creator/scripts/quick_validate.py research-writing
python research-writing/scripts/corpus.py verify --index doc/source-index/inventory.json --doc doc
git status --short
```

Expected: tests and validators exit 0; status contains only intentionally untracked local downloads or provenance updates.

- [ ] **Step 5: Record the research epilogue**

Use `ara-research-manager` to record the user-approved Skill decision, baseline and forward experiments, download results, copyright boundary, and remaining work with correct provenance tags.

- [ ] **Step 6: Commit final tracked artifacts**

```bash
git add research-writing/evals ara
git commit -m "test: validate research writing skill"
```
