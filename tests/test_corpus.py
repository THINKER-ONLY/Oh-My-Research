import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "corpus.py"


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

    def test_normalize_url_removes_embedded_line_breaks(self):
        corpus = load_module()
        self.assertEqual(
            corpus.normalize_url("https://example.org/report.\npdf"),
            "https://example.org/report.pdf",
        )

    def test_rejects_unsafe_example_domain(self):
        corpus = load_module()
        self.assertEqual(
            corpus.url_rejection_reason("http://evil.com/payload"),
            "blocked-domain",
        )

    def test_rejects_corrupted_non_ascii_url(self):
        corpus = load_module()
        self.assertEqual(
            corpus.url_rejection_reason("https://example.org/ﬁles/paper.pdf"),
            "non-ascii-url",
        )

    def test_classifies_primary_topics(self):
        corpus = load_module()
        self.assertEqual(
            corpus.classify_source("Technical Writing", "paper writing"),
            "writing",
        )
        self.assertEqual(
            corpus.classify_source("MCP specification", "agent tools"),
            "agent-systems",
        )

    def test_classifies_navigation_links_by_source_and_page(self):
        corpus = load_module()
        self.assertEqual(
            corpus.classify_link(
                "Skill_Harness_MCP_设计哲学与前沿技术资料_2026-08.pdf",
                19,
                "https://example.org/guide.pdf",
                "writing guide",
            ),
            "agent-systems",
        )
        self.assertEqual(
            corpus.classify_link(
                "Research_资源全景图_论文写作_实验设计_AI技术博客_AutoResearch_2026-08.pdf",
                13,
                "https://pub.sakana.ai/ai-scientist-v2/paper/paper.pdf",
                "AI Scientist",
            ),
            "auto-research",
        )

    def test_github_blob_page_is_not_a_download_candidate(self):
        corpus = load_module()
        self.assertFalse(
            corpus.is_download_candidate(
                "https://github.com/example/project/blob/main/README.md"
            )
        )

    def test_pdf_signature_is_required(self):
        corpus = load_module()
        self.assertTrue(corpus.is_pdf_bytes(b"%PDF-1.7\n"))
        self.assertFalse(corpus.is_pdf_bytes(b"<html>login</html>"))

    def test_sanitized_filename_stays_portable(self):
        corpus = load_module()
        self.assertEqual(corpus.safe_filename("A:B / paper?.pdf"), "A-B-paper.pdf")

    def test_extract_pdf_sources_preserves_page_and_uri(self):
        corpus = load_module()
        import fitz

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "input.pdf"
            pdf = fitz.open()
            page = pdf.new_page()
            page.insert_text((72, 72), "source")
            page.insert_link(
                {
                    "kind": fitz.LINK_URI,
                    "from": fitz.Rect(70, 60, 130, 80),
                    "uri": "https://example.org/paper.pdf",
                }
            )
            pdf.save(path)
            pdf.close()
            metadata, links = corpus.extract_pdf_sources(path)

        self.assertEqual(metadata["pages"], 1)
        self.assertEqual(links[0]["page"], 1)
        self.assertEqual(links[0]["url"], "https://example.org/paper.pdf")

    def test_extract_pdf_sources_redacts_restricted_context(self):
        corpus = load_module()
        import fitz

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "writing words.pdf"
            pdf = fitz.open()
            page = pdf.new_page()
            page.insert_text((72, 72), "protected phrase content")
            page.insert_link(
                {
                    "kind": fitz.LINK_URI,
                    "from": fitz.Rect(70, 60, 190, 80),
                    "uri": "https://example.org/source",
                }
            )
            pdf.save(path)
            pdf.close()
            _, links = corpus.extract_pdf_sources(path)

        self.assertEqual(links[0]["context"], "[restricted source context omitted]")

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
        import threading
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as raw:
                result = corpus.download_document(
                    f"http://127.0.0.1:{server.server_port}/x.pdf",
                    Path(raw) / "x.pdf",
                    1024,
                )
            self.assertEqual(result["status"], "rejected-signature")
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

    def test_download_document_writes_valid_pdf_and_hash(self):
        corpus = load_module()
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        payload = b"%PDF-1.7\nminimal test payload\n"

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        import threading
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as raw:
                target = Path(raw) / "paper.pdf"
                result = corpus.download_document(
                    f"http://127.0.0.1:{server.server_port}/paper.pdf", target, 1024
                )
                self.assertEqual(result["status"], "downloaded")
                self.assertEqual(result["bytes"], len(payload))
                self.assertEqual(result["sha256"], corpus.sha256_file(target))
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

    def test_build_inventory_marks_pdf_candidate_and_blocked_link(self):
        corpus = load_module()
        import fitz

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "guide.pdf"
            pdf = fitz.open()
            page = pdf.new_page()
            for index, url in enumerate(
                ("https://example.org/paper.pdf", "http://evil.com/payload")
            ):
                page.insert_link(
                    {
                        "kind": fitz.LINK_URI,
                        "from": fitz.Rect(70, 60 + index * 20, 180, 75 + index * 20),
                        "uri": url,
                    }
                )
            pdf.save(path)
            pdf.close()
            inventory = corpus.build_inventory(root)

        self.assertEqual([row["url"] for row in inventory["candidates"]], ["https://example.org/paper.pdf"])
        self.assertEqual(inventory["blocked"][0]["status"], "blocked-domain")

    def test_run_downloads_resumes_verified_success_without_network(self):
        corpus = load_module()
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "paper.pdf"
            path.write_bytes(b"%PDF-1.7\nexisting\n")
            digest = corpus.sha256_file(path)
            inventory = {
                "candidates": [
                    {
                        "url": "https://example.org/paper.pdf",
                        "topic": "writing",
                        "sources": [],
                    }
                ],
                "downloads": [
                    {
                        "url": "https://example.org/paper.pdf",
                        "status": "downloaded",
                        "path": str(path),
                        "bytes": path.stat().st_size,
                        "sha256": digest,
                    }
                ],
            }
            with patch.object(corpus, "download_document") as download:
                summary = corpus.run_downloads(
                    inventory, Path(raw), 1024 * 1024, 10 * 1024 * 1024
                )

        download.assert_not_called()
        self.assertEqual(summary["downloaded"], 1)
        self.assertEqual(summary["retried"], 0)

    def test_merge_previous_downloads_keeps_matching_urls_only(self):
        corpus = load_module()
        inventory = {
            "candidates": [{"url": "https://example.org/current.pdf"}],
        }
        previous = {
            "downloads": [
                {"url": "https://example.org/current.pdf", "status": "downloaded"},
                {"url": "https://example.org/removed.pdf", "status": "downloaded"},
            ]
        }

        corpus.merge_previous_downloads(inventory, previous)

        self.assertEqual(
            inventory["downloads"],
            [{"url": "https://example.org/current.pdf", "status": "downloaded"}],
        )

    def test_write_manifests_uses_portable_utf8_lf(self):
        corpus = load_module()
        inventory = {
            "links": [
                {
                    "url": "https://example.org/paper.pdf",
                    "source_file": "source.pdf",
                    "page": 1,
                    "link_kind": "annotation",
                    "context": "context  ",
                }
            ],
            "downloads": [],
        }

        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            corpus.write_manifests(inventory, output)
            payloads = [path.read_bytes() for path in output.iterdir()]

        for payload in payloads:
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r\n", payload)
            for line in payload.splitlines():
                self.assertEqual(line, line.rstrip())


if __name__ == "__main__":
    unittest.main()
