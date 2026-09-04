"""Typed core stubs for the evidence-grounded component graph and architecture.

The functions operate on already-structured claims and meaning atoms. They intentionally
do not pretend to solve citation retrieval, scientific judgment, or natural-language
semantic parsing deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Sequence


class SupportStatus(str, Enum):
    """Permitted states in the Evidence Ledger."""

    SUPPORTED = "supported"
    QUALIFIED = "qualified"
    GAP = "gap"
    PENDING_VERIFICATION = "pending-verification"
    NOT_APPLICABLE = "not-applicable"


class WritingWorkflowStage(str, Enum):
    """Ordered stages in the Writing Workflow."""

    FRAME = "frame"
    LEDGER = "ledger"
    STORY = "story"
    DRAFT = "draft"
    REVISE = "revise"
    AUDIT = "audit"
    DELIVER = "deliver"


@dataclass(frozen=True)
class MeaningAtoms:
    """Conclusion-relevant semantics protected by the Meaning/Compression Gate."""

    proposition: str
    scope: str
    polarity: str
    comparison: str
    causal_force: str
    numbers: tuple[str, ...]
    uncertainty: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class ClaimRecord:
    """One auditable row in the Evidence Ledger."""

    claim_id: str
    claim_text: str
    evidence_id: str
    evidence_location: str
    status: SupportStatus
    qualifiers: tuple[str, ...] = ()
    action: str = ""


@dataclass(frozen=True)
class AuditFinding:
    """A deterministic finding emitted by a gate or pipeline audit."""

    code: str
    message: str
    blocking: bool


def build_evidence_ledger(records: Iterable[ClaimRecord]) -> dict[str, ClaimRecord]:
    """Build a unique claim-id mapping and reject duplicate ledger identifiers."""

    ledger: dict[str, ClaimRecord] = {}
    for record in records:
        if record.claim_id in ledger:
            raise ValueError(f"duplicate claim_id: {record.claim_id}")
        ledger[record.claim_id] = record
    return ledger


def draftable_claims(ledger: Mapping[str, ClaimRecord]) -> tuple[ClaimRecord, ...]:
    """Return only supported or explicitly qualified records for factual drafting."""

    allowed = {SupportStatus.SUPPORTED, SupportStatus.QUALIFIED}
    return tuple(record for record in ledger.values() if record.status in allowed)


def compare_meaning_atoms(before: MeaningAtoms, after: MeaningAtoms) -> tuple[str, ...]:
    """Name every protected semantic field changed by revision."""

    differences: list[str] = []
    for field_name in MeaningAtoms.__dataclass_fields__:
        if getattr(before, field_name) != getattr(after, field_name):
            differences.append(field_name)
    return tuple(differences)


def compression_safety_gate(
    before: MeaningAtoms,
    after: MeaningAtoms,
    revised_text: str,
    word_limit: int | None = None,
) -> tuple[AuditFinding, ...]:
    """Audit semantic fidelity and an optional word budget without parsing prose."""

    findings = [
        AuditFinding(
            code="meaning-drift",
            message=f"protected meaning changed: {field_name}",
            blocking=True,
        )
        for field_name in compare_meaning_atoms(before, after)
    ]
    if word_limit is not None and len(revised_text.split()) > word_limit:
        findings.append(
            AuditFinding(
                code="word-budget",
                message="faithful revision exceeds the requested word budget",
                blocking=False,
            )
        )
    return tuple(findings)


def corpus_pipeline_audit(manifest: Mapping[str, object]) -> tuple[AuditFinding, ...]:
    """Check core Corpus Pipeline record bindings without touching the filesystem."""

    candidates = manifest.get("candidates", [])
    downloads = manifest.get("downloads", [])
    if not isinstance(candidates, Sequence) or not isinstance(downloads, Sequence):
        return (AuditFinding("manifest-shape", "candidate/download arrays are missing", True),)

    candidate_urls = {
        row.get("url") for row in candidates if isinstance(row, Mapping) and row.get("url")
    }
    download_urls = {
        row.get("url") for row in downloads if isinstance(row, Mapping) and row.get("url")
    }
    findings: list[AuditFinding] = []
    if candidate_urls != download_urls:
        findings.append(
            AuditFinding("candidate-result-mismatch", "candidate and result URL sets differ", True)
        )

    for row in downloads:
        if not isinstance(row, Mapping) or row.get("status") not in {"downloaded", "deduplicated"}:
            continue
        if not row.get("path"):
            findings.append(AuditFinding("missing-path", "successful record lacks path", True))
        if not row.get("sha256"):
            findings.append(AuditFinding("missing-hash", "successful record lacks SHA-256", True))
    return tuple(findings)


def evaluation_harness_compare(
    baseline_scores: Mapping[str, int],
    forward_scores: Mapping[str, int],
) -> dict[str, int]:
    """Return per-case score deltas for the fixed Evaluation Harness."""

    if set(baseline_scores) != set(forward_scores):
        raise ValueError("baseline and forward case identifiers must match")
    return {case_id: forward_scores[case_id] - baseline_scores[case_id] for case_id in baseline_scores}


def license_boundary_allows(source_filename: str, action: str) -> bool:
    """Apply the repository's conservative License Boundary for the restricted source."""

    restricted = source_filename.casefold() == "writing words.pdf"
    metadata_only_actions = {"index-metadata", "store-redacted-context", "link-official-source"}
    return not restricted or action in metadata_only_actions
