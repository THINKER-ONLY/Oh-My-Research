from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

import fitz
import requests


BLOCKED_DOMAINS = {"evil.com"}
RESTRICTED_LOCAL_FILENAMES = {"writing words.pdf"}
TRACKING_KEYS = {"utm_campaign", "utm_content", "utm_medium", "utm_source", "utm_term"}
TOPICS = ("writing", "research-methods", "agent-systems", "auto-research")
USER_AGENT = "open-research-skill-corpus/0.1 (+local provenance; respectful rate limits)"
TRANSIENT_STATUSES = {429, 500, 502, 503, 504}
URL_RE = re.compile(r"https?://[^\s<>\"\]\)】）]+", re.IGNORECASE)
DOWNLOAD_EXTENSIONS = {".pdf", ".docx", ".pptx", ".zip", ".tar", ".gz", ".json", ".ipynb", ".txt", ".md"}


def normalize_url(url: str) -> str:
    """Normalize a URL without changing its resource identity."""
    raw = url.strip().rstrip(".,;:，。；：)]}>»")
    parts = urlsplit(raw)
    query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() not in TRACKING_KEYS
        ]
    )
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, query, ""))


def url_rejection_reason(url: str) -> str | None:
    if any(ord(character) > 127 for character in url):
        return "non-ascii-url"
    try:
        parts = urlsplit(url)
    except ValueError:
        return "malformed-url"
    if parts.scheme not in {"http", "https"}:
        return "unsupported-scheme"
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        return "malformed-url"
    if host in BLOCKED_DOMAINS or any(host.endswith("." + domain) for domain in BLOCKED_DOMAINS):
        return "blocked-domain"
    return None


def classify_source(title: str, context: str) -> str:
    text = f"{title} {context}".lower()
    if any(key in text for key in ("agent", "skill", "harness", "mcp", "a2a")):
        return "agent-systems"
    if any(key in text for key in ("auto research", "ai scientist", "deep research", "自动化科研")):
        return "auto-research"
    if any(key in text for key in ("writing", "phrasebank", "论文", "写作", "academic english")):
        return "writing"
    return "research-methods"


def classify_link(source_file: str, page: int, url: str, context: str) -> str:
    source = source_file.lower()
    if "ai-agents-in-depth" in source or "skill_harness_mcp" in source or "skill·harness" in source:
        return "agent-systems"
    if "technical writing" in source or "writing words" in source or "可直接下载" in source:
        return "writing"
    if "research_资源全景图" in source:
        if page >= 12:
            return "auto-research"
        if page >= 9:
            return "research-methods"
        return "writing"
    if "research_ai_sources" in source or "科研方法与前沿" in source:
        return "research-methods"
    return classify_source(url, context)


def is_pdf_candidate(url: str) -> bool:
    parts = urlsplit(url.lower())
    path = parts.path.rstrip("/")
    return (
        path.endswith(".pdf")
        or path.endswith("/pdf")
        or "/pdf/" in path
        or "/bitstream/" in path
        or "download=1" in parts.query
    )


def is_download_candidate(url: str) -> bool:
    """Return true for explicit document endpoints, not ordinary article pages."""
    if url_rejection_reason(url) is not None:
        return False
    parts = urlsplit(url.lower())
    path = parts.path.rstrip("/")
    if parts.netloc == "github.com" and "/blob/" in path:
        return False
    if is_pdf_candidate(url):
        return True
    if path.endswith(tuple(DOWNLOAD_EXTENSIONS)):
        return True
    if any(token in path for token in ("/download", "/downloads/", "/files/", "/attachment/")):
        return True
    if parts.netloc == "raw.githubusercontent.com":
        return True
    return False


def is_pdf_bytes(prefix: bytes) -> bool:
    return prefix.startswith(b"%PDF-")


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[<>:\"/\\|?*]+", "-", unquote(name)).replace(" ", "-")
    cleaned = re.sub(r"-+", "-", cleaned).strip(".-")
    cleaned = re.sub(r"-+\.", ".", cleaned)
    return cleaned or "download"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _page_context(text: str, limit: int = 500) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def extract_pdf_sources(pdf_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract metadata and annotation/text URLs with 1-based page provenance."""
    document = fitz.open(pdf_path)
    metadata = document.metadata or {}
    links: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for page_index, page in enumerate(document):
        page_number = page_index + 1
        text = page.get_text("text") or ""
        context = (
            "[restricted source context omitted]"
            if pdf_path.name.lower() in RESTRICTED_LOCAL_FILENAMES
            else _page_context(text)
        )
        candidates: list[tuple[str, str]] = []
        for annotation in page.get_links():
            uri = annotation.get("uri")
            if uri:
                candidates.append((uri, "annotation"))
        for match in URL_RE.findall(text):
            candidates.append((match, "text"))
        for raw_url, link_kind in candidates:
            try:
                url = normalize_url(raw_url)
            except (TypeError, ValueError):
                continue
            if not url:
                continue
            key = (url, page_number, link_kind)
            if key in seen:
                continue
            seen.add(key)
            links.append(
                {
                    "url": url,
                    "source_file": pdf_path.name,
                    "page": page_number,
                    "link_kind": link_kind,
                    "context": context,
                }
            )
    result = {
        "file": pdf_path.name,
        "title": metadata.get("title") or pdf_path.stem,
        "author": metadata.get("author") or "",
        "pages": len(document),
        "text_chars": sum(len(page.get_text("text") or "") for page in document),
    }
    document.close()
    return result, links


def _result(url: str, status: str, **fields: Any) -> dict[str, Any]:
    base = {
        "url": url,
        "final_url": "",
        "status": status,
        "path": "",
        "bytes": 0,
        "sha256": "",
        "content_type": "",
        "error": "",
    }
    base.update(fields)
    return base


def _filename_from_url(url: str) -> str:
    path_name = Path(unquote(urlsplit(url).path)).name
    if not path_name or path_name in {".", ".."}:
        path_name = "download.pdf" if is_pdf_candidate(url) else "download"
    return safe_filename(path_name)


def download_document(
    url: str,
    destination: Path,
    max_bytes: int,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Stream one resource to a temporary file and validate it before rename."""
    rejection = url_rejection_reason(url)
    if rejection:
        return _result(url, rejection)
    client = session or requests.Session()
    expected_pdf = is_pdf_candidate(url)
    part_path = destination.with_name(destination.name + ".part")
    destination.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            response = client.get(
                url,
                stream=True,
                allow_redirects=True,
                timeout=(15, 45),
                headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,application/octet-stream,*/*"},
            )
        except requests.RequestException as exc:
            if attempt < 2:
                time.sleep(0.25 * (attempt + 1))
                continue
            return _result(url, "network-error", error=str(exc))
        try:
            if response.status_code in TRANSIENT_STATUSES and attempt < 2:
                time.sleep(0.25 * (attempt + 1))
                continue
            if response.status_code >= 400:
                return _result(url, "http-error", final_url=response.url, error=f"HTTP {response.status_code}")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            advertised = response.headers.get("Content-Length")
            if advertised and advertised.isdigit() and int(advertised) > max_bytes:
                return _result(url, "too-large", final_url=response.url, content_type=content_type)
            total = 0
            prefix = bytearray()
            with part_path.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    if total + len(chunk) > max_bytes:
                        part_path.unlink(missing_ok=True)
                        return _result(url, "too-large", final_url=response.url, content_type=content_type)
                    if len(prefix) < 1024:
                        prefix.extend(chunk[: 1024 - len(prefix)])
                    stream.write(chunk)
                    total += len(chunk)
            if expected_pdf and not is_pdf_bytes(bytes(prefix)):
                part_path.unlink(missing_ok=True)
                return _result(
                    url,
                    "rejected-signature",
                    final_url=response.url,
                    content_type=content_type,
                    bytes=total,
                )
            os.replace(part_path, destination)
            return _result(
                url,
                "downloaded",
                final_url=response.url,
                path=str(destination),
                bytes=total,
                sha256=sha256_file(destination),
                content_type=content_type,
            )
        finally:
            response.close()
    return _result(url, "network-error", error="retry budget exhausted")


def build_inventory(input_dir: Path) -> dict[str, Any]:
    inputs: list[dict[str, Any]] = []
    all_links: list[dict[str, Any]] = []
    for pdf_path in sorted(input_dir.glob("*.pdf")):
        metadata, links = extract_pdf_sources(pdf_path)
        inputs.append(metadata)
        all_links.extend(links)
    candidates: dict[str, dict[str, Any]] = {}
    blocked: list[dict[str, Any]] = []
    for link in all_links:
        url = link["url"]
        rejection = url_rejection_reason(url)
        if rejection:
            blocked.append({**link, "status": rejection})
            continue
        if not is_download_candidate(url):
            continue
        entry = candidates.setdefault(
            url,
            {
                "url": url,
                "topic": classify_link(
                    link["source_file"], link["page"], link["url"], link["context"]
                ),
                "sources": [],
            },
        )
        source_ref = {key: link[key] for key in ("source_file", "page", "link_kind")}
        if source_ref not in entry["sources"]:
            entry["sources"].append(source_ref)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "links": all_links,
        "candidates": list(candidates.values()),
        "blocked": blocked,
    }


def _manifest_row(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in fields:
        value = row.get(key, "")
        result[key] = value.strip() if isinstance(value, str) else value
    return result


def write_manifests(inventory: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "inventory.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    source_fields = ["url", "source_file", "page", "link_kind", "context"]
    with (output_dir / "sources.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=source_fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(_manifest_row(row, source_fields) for row in inventory.get("links", []))
    downloads = inventory.get("downloads", [])
    fields = ["url", "final_url", "status", "path", "bytes", "sha256", "content_type", "error"]
    with (output_dir / "downloads.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(_manifest_row(row, fields) for row in downloads)
    with (output_dir / "failures.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            _manifest_row(row, fields)
            for row in downloads
            if row.get("status") not in {"downloaded", "deduplicated", "license-restricted"}
        )


def merge_previous_downloads(inventory: dict[str, Any], previous: dict[str, Any]) -> None:
    current_urls = {row.get("url") for row in inventory.get("candidates", [])}
    inventory["downloads"] = [
        row for row in previous.get("downloads", []) if row.get("url") in current_urls
    ]
    if previous.get("download_summary"):
        inventory["download_summary"] = previous["download_summary"]


def run_downloads(
    inventory: dict[str, Any],
    doc_dir: Path,
    max_file_bytes: int,
    max_total_bytes: int,
) -> dict[str, Any]:
    previous = {row.get("url"): row for row in inventory.get("downloads", []) if row.get("url")}
    downloads: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    counted_paths: set[str] = set()
    total = 0
    retried = 0
    network_attempted = 0
    for candidate in inventory.get("candidates", []):
        url = candidate["url"]
        sources = candidate.get("sources", [])
        prior = previous.get(url)
        if prior and prior.get("status") in {"downloaded", "deduplicated"}:
            prior_path = Path(prior.get("path", ""))
            if prior_path.exists() and (
                not prior.get("sha256") or sha256_file(prior_path) == prior.get("sha256")
            ):
                downloads.append(prior)
                digest = prior.get("sha256", "")
                if digest:
                    hashes[digest] = str(prior_path)
                if str(prior_path) not in counted_paths:
                    counted_paths.add(str(prior_path))
                    total += int(prior.get("bytes", prior_path.stat().st_size))
                continue
        if prior and prior.get("status") == "license-restricted":
            downloads.append(prior)
            continue
        if prior:
            retried += 1
        source_names = {item.get("source_file", "").lower() for item in sources}
        if "writing words.pdf" in source_names:
            downloads.append(_result(url, "license-restricted"))
            continue
        if total >= max_total_bytes:
            downloads.append(_result(url, "total-budget-exhausted"))
            continue
        filename = _filename_from_url(url)
        target = doc_dir / candidate.get("topic", "research-methods") / filename
        if target.exists():
            target = target.with_name(f"{target.stem}-{hashlib.sha1(url.encode()).hexdigest()[:8]}{target.suffix}")
        network_attempted += 1
        result = download_document(url, target, min(max_file_bytes, max_total_bytes - total))
        result["topic"] = candidate.get("topic", "research-methods")
        result["sources"] = sources
        if result.get("status") == "downloaded":
            total += int(result.get("bytes", 0))
            digest = result.get("sha256", "")
            if digest in hashes:
                Path(result["path"]).unlink(missing_ok=True)
                result["status"] = "deduplicated"
                result["path"] = hashes[digest]
            else:
                hashes[digest] = result["path"]
        downloads.append(result)
    inventory["downloads"] = downloads
    inventory["download_summary"] = {
        "attempted": len(downloads),
        "network_attempted": network_attempted,
        "retried": retried,
        "downloaded": sum(row["status"] == "downloaded" for row in downloads),
        "deduplicated": sum(row["status"] == "deduplicated" for row in downloads),
        "failed": sum(row["status"] not in {"downloaded", "deduplicated", "license-restricted"} for row in downloads),
        "bytes": total,
    }
    return inventory["download_summary"]


def verify_inventory(index_path: Path, doc_dir: Path) -> tuple[bool, list[str]]:
    inventory = json.loads(index_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for row in inventory.get("downloads", []):
        if row.get("status") not in {"downloaded", "deduplicated"}:
            continue
        path = Path(row.get("path", ""))
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            errors.append(f"missing: {path}")
            continue
        if row.get("sha256") and sha256_file(path) != row["sha256"]:
            errors.append(f"hash-mismatch: {path}")
    return not errors, errors


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inventory and archive research source documents")
    sub = parser.add_subparsers(dest="command", required=True)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("--input", type=Path, default=Path("."))
    inventory.add_argument("--output", type=Path, required=True)
    download = sub.add_parser("download")
    download.add_argument("--index", type=Path, required=True)
    download.add_argument("--doc", type=Path, required=True)
    download.add_argument("--max-file-mb", type=int, default=200)
    download.add_argument("--max-total-mb", type=int, default=3500)
    verify = sub.add_parser("verify")
    verify.add_argument("--index", type=Path, required=True)
    verify.add_argument("--doc", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "inventory":
        inventory = build_inventory(args.input)
        previous_path = args.output / "inventory.json"
        if previous_path.exists():
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
            merge_previous_downloads(inventory, previous)
        write_manifests(inventory, args.output)
        print(json.dumps({"status": "ok", "inputs": len(list(args.input.glob("*.pdf")))}, ensure_ascii=False))
        return 0
    if args.command == "download":
        inventory = json.loads(args.index.read_text(encoding="utf-8"))
        run_downloads(inventory, args.doc, args.max_file_mb * 1024 * 1024, args.max_total_mb * 1024 * 1024)
        write_manifests(inventory, args.index.parent)
        print(json.dumps(inventory["download_summary"], ensure_ascii=False))
        return 0
    ok, errors = verify_inventory(args.index, args.doc)
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
