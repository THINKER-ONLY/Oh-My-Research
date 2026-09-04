from __future__ import annotations

import csv
import os
import re
import stat
import sys
import unicodedata
from datetime import date
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Callable
from urllib.parse import unquote, urlsplit

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode
from yaml.resolver import BaseResolver


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "research-writing"
MANIFEST = ROOT / "release-manifest.txt"

ALLOWED_ROOT_RELEASE_FILES = {"LICENSE", "THIRD_PARTY_NOTICES.md"}
FORBIDDEN_RELEASE_PREFIXES = ("doc/", "ara/", "evals/", "tests/")
TEXT_EXTENSIONS = {".md", ".csv", ".yaml", ".yml", ".txt"}
FORBIDDEN_SUFFIXES = {".pdf", ".pyc", ".pyo"}
WINDOWS_INVALID_CHARACTERS = frozenset('<>"|?*')
ALLOWED_EXTERNAL_SCHEMES = {"http", "https", "mailto"}
CANONICAL_LICENSE_SHA256 = (
    "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
)
EXPECTED_LEDGER_HEADER = [
    "claim_id",
    "section",
    "claim_text",
    "claim_type",
    "polarity",
    "scope",
    "conditions",
    "qualifiers",
    "numeric_value",
    "unit",
    "denominator",
    "comparison_or_baseline",
    "evidence_id",
    "evidence_location",
    "evidence_summary",
    "support_status",
    "citation_status",
    "limitation_or_gap",
    "action",
]
EXPECTED_SOURCE_HEADER = [
    "Principle",
    "Source type and authority",
    "Supplied PDF and page",
    "Verified extension document and location",
    "Skill rule",
    "Applicability or conflict",
    "Canonical URL",
    "Access date",
]
SOURCE_FOUNDATION_EXTENSION_MARKERS = (
    "Simon Peyton Jones",
    "George M. Whitesides",
    "Mike Ashby",
    "George D. Gopen",
    "Donald E. Knuth",
    "Helsinki",
    "Bates",
    "NASA SP-7084",
    "Machine Learning Reproducibility Checklist",
    "On Being a Scientist",
)
SOURCE_FOUNDATION_OUTSIDE_MARKERS = (
    "https://www.phrasebank.manchester.ac.uk/",
    "Restricted-source boundary",
)
EXPECTED_SOURCE_PAIRS = (
    ("Write while the research is forming", "Simon Peyton Jones"),
    ("Write while the research is forming", "George M. Whitesides"),
    ("Write while the research is forming", "Mike Ashby"),
    ("Make the central idea and claims explicit", "Simon Peyton Jones"),
    (
        "Make the central idea and claims explicit",
        "Machine Learning Reproducibility Checklist",
    ),
    ("Design for the reader's current state", "Simon Peyton Jones"),
    ("Design for the reader's current state", "Mike Ashby"),
    ("Design for the reader's current state", "Donald E. Knuth"),
    ("Give each section a rhetorical job", "George M. Whitesides"),
    ("Give each section a rhetorical job", "Mike Ashby"),
    ("Give each section a rhetorical job", "Helsinki"),
    ("Give each section a rhetorical job", "Bates"),
    ("Use information structure deliberately", "George D. Gopen"),
    (
        "Keep stylistic prescriptions conditional",
        "Technical Writing (updated).pdf",
    ),
    ("Keep stylistic prescriptions conditional", "Helsinki"),
    ("Keep stylistic prescriptions conditional", "Bates"),
    ("Keep stylistic prescriptions conditional", "George D. Gopen"),
    ("Separate observation from interpretation", "Helsinki"),
    ("Separate observation from interpretation", "Bates"),
    (
        "Make figures and statistical support carry explicit messages",
        "Bates",
    ),
    ("Do not make the record stronger than the data", "On Being a Scientist"),
    (
        "Verify source identity and local claim support separately",
        "On Being a Scientist",
    ),
    (
        "Report enough method detail to evaluate and reproduce",
        "On Being a Scientist",
    ),
    (
        "Report enough method detail to evaluate and reproduce",
        "Machine Learning Reproducibility Checklist",
    ),
    (
        "Disclose questionable exclusions and divide papers by contribution",
        "On Being a Scientist",
    ),
    ("Compress without deleting meaning", "NASA SP-7084"),
    ("Compress without deleting meaning", "George D. Gopen"),
    (
        "Define notation and expose assumptions before relying on them",
        "Donald E. Knuth",
    ),
    (
        "Define notation and expose assumptions before relying on them",
        "Technical Writing (updated).pdf",
    ),
    (
        "Define notation and expose assumptions before relying on them",
        "Mike Ashby",
    ),
)
EXPECTED_SOURCE_LOCATORS = {
    ("Write while the research is forming", "Simon Peyton Jones"): "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20",
    ("Write while the research is forming", "George M. Whitesides"): "George M. Whitesides, *Writing a Paper*, PDF pp.1-3",
    ("Write while the research is forming", "Mike Ashby"): "Mike Ashby, *How to Write a Paper*, PDF pp.4-6",
    ("Make the central idea and claims explicit", "Simon Peyton Jones"): "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.12-13 and 21-24",
    ("Make the central idea and claims explicit", "Machine Learning Reproducibility Checklist"): "Machine Learning Reproducibility Checklist, PDF p.1",
    ("Design for the reader's current state", "Simon Peyton Jones"): "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.36-45",
    ("Design for the reader's current state", "Mike Ashby"): "Mike Ashby, *How to Write a Paper*, PDF pp.4-8",
    ("Design for the reader's current state", "Donald E. Knuth"): "Donald E. Knuth, Tracy Larrabee, and Paul M. Roberts, *Mathematical Writing*, PDF pp.4-7",
    ("Give each section a rhetorical job", "George M. Whitesides"): "George M. Whitesides, *Writing a Paper*, PDF pp.1-3",
    ("Give each section a rhetorical job", "Mike Ashby"): "Mike Ashby, *How to Write a Paper*, PDF pp.4-14",
    ("Give each section a rhetorical job", "Helsinki"): "Helsinki *Scientific Writing Guide*, PDF pp.2 and 6-14",
    ("Give each section a rhetorical job", "Bates"): "Bates *How to Write Guide*, PDF pp.5, 9-16, and 29-30",
    ("Use information structure deliberately", "George D. Gopen"): "George D. Gopen and Judith A. Swan, *The Science of Scientific Writing*, PDF pp.4-12",
    ("Keep stylistic prescriptions conditional", "Technical Writing (updated).pdf"): "`Technical Writing (updated).pdf`, PDF p.1",
    ("Keep stylistic prescriptions conditional", "Helsinki"): "Helsinki *Scientific Writing Guide*, PDF p.2",
    ("Keep stylistic prescriptions conditional", "Bates"): "Bates *How to Write Guide*, PDF pp.5 and 59",
    ("Keep stylistic prescriptions conditional", "George D. Gopen"): "George D. Gopen and Judith A. Swan, *The Science of Scientific Writing*, PDF pp.6 and 12",
    ("Separate observation from interpretation", "Helsinki"): "Helsinki *Scientific Writing Guide*, PDF pp.11-13",
    ("Separate observation from interpretation", "Bates"): "Bates *How to Write Guide*, PDF pp.29-30",
    ("Make figures and statistical support carry explicit messages", "Bates"): "Bates *How to Write Guide*, PDF pp.9-16, 29-30, and 59",
    ("Do not make the record stronger than the data", "On Being a Scientist"): "*On Being a Scientist*, PDF pp.10 and 27-31",
    ("Verify source identity and local claim support separately", "On Being a Scientist"): "*On Being a Scientist*, PDF pp.48-49",
    ("Report enough method detail to evaluate and reproduce", "On Being a Scientist"): "*On Being a Scientist*, PDF pp.28-31",
    ("Report enough method detail to evaluate and reproduce", "Machine Learning Reproducibility Checklist"): "Machine Learning Reproducibility Checklist, PDF p.1",
    ("Disclose questionable exclusions and divide papers by contribution", "On Being a Scientist"): "*On Being a Scientist*, PDF pp.70 and 73",
    ("Compress without deleting meaning", "NASA SP-7084"): "NASA SP-7084, PDF pp.19 and 36-52",
    ("Compress without deleting meaning", "George D. Gopen"): "George D. Gopen and Judith A. Swan, *The Science of Scientific Writing*, PDF p.6",
    ("Define notation and expose assumptions before relying on them", "Donald E. Knuth"): "Donald E. Knuth, Tracy Larrabee, and Paul M. Roberts, *Mathematical Writing*, PDF pp.4-7 and 114",
    ("Define notation and expose assumptions before relying on them", "Technical Writing (updated).pdf"): "`Technical Writing (updated).pdf`, PDF pp.6-8",
    ("Define notation and expose assumptions before relying on them", "Mike Ashby"): "Mike Ashby, *How to Write a Paper*, PDF p.14",
}
TECHNICAL_WRITING_MARKER = "Technical Writing (updated).pdf"
UPSTREAM_SOURCE_GAP = (
    "not verified: introducing/indexing supplied PDF and page are not recorded"
)
DIRECT_EXTENSION_MARKER = "not applicable: direct supplied-PDF evidence"
UNAVAILABLE_URL_MARKER = "not verified: canonical public URL unavailable"
DIRECT_URL_MARKER = "not applicable: canonical URL not verified"
UNAVAILABLE_DATE_MARKER = "not applicable: access date unavailable"
ALLOWED_SOURCE_TYPES = {
    "Integrity basis",
    "Workflow guidance",
    "Style heuristic",
    "Field guidance",
    "Workflow guidance plus integrity basis",
}
EXPECTED_SOURCE_URLS = {
    "Simon Peyton Jones": "https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/",
    "George M. Whitesides": "https://doi.org/10.1002/adma.200400767",
    "Mike Ashby": "https://www-mdp.eng.cam.ac.uk/web/library/enginfo/reports/How_to_write_a_paper_2005.pdf",
    "George D. Gopen": "https://www.gatsby.ucl.ac.uk/~pel/misc/gopen_swan.pdf",
    "Donald E. Knuth": "https://jmlr.csail.mit.edu/reviewing-papers/knuth_mathematical_writing.pdf",
    "Helsinki": "https://www.cs.helsinki.fi/group/ese/ScientificWritingGuide.pdf",
    "Bates": "https://www.bates.edu/biology/files/2010/06/How-to-Write-Guide-v10-2014.pdf",
    "NASA SP-7084": "https://ntrs.nasa.gov/citations/19900017394",
    "Machine Learning Reproducibility Checklist": "https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf",
    "On Being a Scientist": "https://doi.org/10.17226/12192",
    TECHNICAL_WRITING_MARKER: DIRECT_URL_MARKER,
}
DIRECT_SUPPLIED_LOCATORS = {
    "`Technical Writing (updated).pdf`, PDF p.1",
    "`Technical Writing (updated).pdf`, PDF pp.6-8",
}
EXTENSION_LOCATOR_RE = re.compile(
    r"^\S(?:.*\S)?,\s*(?:PDF pp?\.\d+(?:-\d+)?"
    r"(?:, \d+(?:-\d+)?)*(?:,? and \d+(?:-\d+)?)?|section \S(?:.*\S)?)$"
)
HTTPS_URL_RE = re.compile(r"https://[^\s;|]+")
ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
REQUIRED_INSTRUCTIONAL_LEDGER_FIELDS = {
    "claim_id": "TEMPLATE-01",
    "claim_text": "Replace this instructional row before using the ledger.",
    "claim_type": "proposal",
    "polarity": "neutral",
    "support_status": "not-applicable",
    "citation_status": "not-required",
}

WINDOWS_DRIVE_PATH_RE = re.compile(r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]")
WINDOWS_DRIVE_RELATIVE_RE = re.compile(
    r"(?<![A-Za-z0-9+.-])[A-Za-z]:(?![\\/])(?=[^\s])"
)
UNC_PATH_RE = re.compile(r"(?<!\\)\\\\[^\\/\s]+[\\/][^\\/\s]+")
NETWORK_PATH_RE = re.compile(r"(?<![:/])//(?=[^/\s]+/)")
POSIX_ROOTED_PATH_RE = re.compile(r"(?<![A-Za-z0-9:/\\])/(?=[^/\s])")
WINDOWS_ROOTED_PATH_RE = re.compile(r"(?<![A-Za-z0-9\\])\\(?!\\)(?=[^\s])")
TILDE_PATH_RE = re.compile(r"(?<![A-Za-z0-9])~[\\/](?=[^\s])")
FILE_URI_RE = re.compile(r"(?i)(?<![A-Za-z0-9+.-])file:")
UNSUPPORTED_SCHEME_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9+.-])[A-Za-z][A-Za-z0-9+.-]*://"
)
ALLOWED_URI_START_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9+.-])(?:https?://|mailto:)"
)
URI_BOUNDARY_CHARACTERS = frozenset('<>"\'`{}')
INLINE_LINK_RE = re.compile(r"!?\[[^\]\r\n]*\]\(([^)\r\n]+)\)")
REFERENCE_LINK_RE = re.compile(
    r"^[ \t]{0,3}\[[^\]\r\n]+\]:[ \t]*(<[^>\r\n]+>|[^\s]+)", re.MULTILINE
)
FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(?P<header>.*?)(?:\r?\n)---[ \t]*(?:\r?\n|\Z)",
    re.DOTALL,
)


@dataclass(frozen=True)
class ManifestRecord:
    line_number: int
    value: str


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_strict_mapping(
    loader: StrictSafeLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    if not isinstance(node, MappingNode):
        raise ConstructorError(
            None,
            None,
            "expected a mapping node",
            node.start_mark,
        )

    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "merge keys are not allowed",
                key_node.start_mark,
            )
        key = loader.construct_object(key_node, deep=deep)
        try:
            hash(key)
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key {key!r} is not allowed",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_strict_mapping,
)


def _strict_yaml_load(text: str) -> Any:
    return yaml.load(text, Loader=StrictSafeLoader)


def manifest_records(root: Path = ROOT) -> list[ManifestRecord]:
    manifest = Path(root) / "release-manifest.txt"
    return _manifest_records_from_text(manifest.read_text(encoding="utf-8"))


def _manifest_records_from_text(text: str) -> list[ManifestRecord]:
    records: list[ManifestRecord] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip() and not line.lstrip().startswith("#"):
            records.append(ManifestRecord(line_number, line))
    return records


def manifest_entries(root: Path = ROOT) -> list[str]:
    return [record.value for record in manifest_records(root)]


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if match is None:
        raise ValueError("SKILL.md must begin with YAML frontmatter")

    try:
        metadata = _strict_yaml_load(match.group("header"))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("YAML frontmatter must be a mapping")
    return metadata, text[match.end() :]


def _is_link(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        if sys.version_info >= (3, 12) and path.is_junction():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except FileNotFoundError:
        # A missing path is not a link. Callers still report it as missing.
        return False
    except OSError:
        # Failure to inspect a path must not be treated as proof that it is
        # safe. The validator is deliberately fail-closed for permission,
        # I/O, and other lstat errors.
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _relative_label(root: Path, path: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return os.fspath(path)
    return relative.as_posix() or "."


def _containment_errors(root: Path, target: Path, label: str) -> list[str]:
    errors: list[str] = []
    root_absolute = _lexical_absolute(root)
    target_absolute = _lexical_absolute(target)
    try:
        relative = target_absolute.relative_to(root_absolute)
    except ValueError:
        return [f"{label} is lexically outside the repository root"]

    current = root_absolute
    components = [current]
    for part in relative.parts:
        current = current / part
        components.append(current)
    for component in components:
        if _is_link(component):
            errors.append(
                f"{label} has a symlink, junction, or reparse-point ancestor: "
                f"{_relative_label(root_absolute, component)}"
            )
            break

    try:
        resolved_root = root_absolute.resolve(strict=True)
        resolved_target = target_absolute.resolve(strict=False)
    except OSError as exc:
        errors.append(f"cannot resolve {label}: {exc}")
    else:
        if not resolved_target.is_relative_to(resolved_root):
            errors.append(f"{label} resolves outside the repository root")
    return errors


def _ordinary_file_errors(root: Path, path: Path, label: str) -> list[str]:
    errors = _containment_errors(root, path, label)
    if not path.is_file() or _is_link(path):
        errors.append(f"{label} must be an ordinary non-linked file")
    return errors


def _fixed_file_guard(root: Path, path: Path, label: str) -> list[str]:
    """Return security errors before reading a repository fixed file.

    The tree walk also rejects links, but the specialized readers below run
    independently of that result. Guarding each fixed path here prevents a
    linked file (or a linked parent) from being followed by a reader. Missing
    and ordinary-file diagnostics remain the responsibility of the
    specialized reader so their existing messages stay useful.
    """

    errors = _containment_errors(root, path, label)
    link_ancestor = any(
        "symlink, junction, or reparse-point ancestor" in error for error in errors
    )
    if _is_link(path) or link_ancestor:
        errors.append(f"{label} must be an ordinary non-linked file")
    return errors


def _manifest_path_errors(entry: str) -> list[str]:
    errors: list[str] = []
    relative = PurePosixPath(entry)
    windows_relative = PureWindowsPath(entry)

    if "\\" in entry:
        errors.append("uses a backslash")
    if windows_relative.drive:
        errors.append("has a Windows drive or UNC root")
    if relative.is_absolute():
        errors.append("is an absolute POSIX path")
    if ".." in relative.parts:
        errors.append("contains a parent traversal")
    if relative.as_posix() != entry:
        errors.append("is not a canonical POSIX path")

    for part in windows_relative.parts:
        if part != part.rstrip(" ."):
            errors.append(f"component {ascii(part)} has a trailing dot or space")
        if ":" in part:
            errors.append(f"component {ascii(part)} contains a colon")
        if PureWindowsPath(part).is_reserved():
            errors.append(f"component {ascii(part)} is a reserved Windows name")
        for character in part:
            if character in WINDOWS_INVALID_CHARACTERS:
                errors.append(
                    f"component {ascii(part)} contains Windows-invalid character "
                    f"{ascii(character)}"
                )
            if ord(character) < 32 or ord(character) == 127:
                errors.append(
                    f"component {ascii(part)} contains ASCII control character "
                    f"U+{ord(character):04X}"
                )

    folded_parts = {part.casefold() for part in relative.parts}
    if "__pycache__" in folded_parts:
        errors.append("contains a __pycache__ directory")
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        errors.append(f"has forbidden suffix {relative.suffix!r}")
    if entry.casefold().startswith(FORBIDDEN_RELEASE_PREFIXES):
        errors.append("uses a forbidden release prefix")

    is_allowed_root_file = len(relative.parts) == 1 and entry in ALLOWED_ROOT_RELEASE_FILES
    is_skill_file = entry.startswith("skills/research-writing/")
    if not (is_allowed_root_file or is_skill_file):
        errors.append("is outside the release allowlist boundary")
    return errors


def safe_release_source_records(
    root: Path = ROOT,
) -> tuple[bytes, tuple[tuple[ManifestRecord, Path], ...]]:
    root = Path(root)
    manifest_path = root / "release-manifest.txt"
    errors = _ordinary_file_errors(root, manifest_path, "release-manifest.txt")
    if errors:
        raise ValueError("; ".join(errors))

    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest_text = manifest_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read release-manifest.txt safely: {exc}") from exc

    records = _manifest_records_from_text(manifest_text)
    sources: list[tuple[ManifestRecord, Path]] = []
    for record in records:
        path_errors = _manifest_path_errors(record.value)
        if path_errors:
            errors.extend(
                f"invalid manifest entry at line {record.line_number} "
                f"{ascii(record.value)}: {message}"
                for message in path_errors
            )
            continue
        relative = PurePosixPath(record.value)
        target = root.joinpath(*relative.parts)
        errors.extend(
            _ordinary_file_errors(
                root,
                target,
                f"manifest target at line {record.line_number} {ascii(record.value)}",
            )
        )
        sources.append((record, target))

    errors.extend(_ordinary_file_errors(root, manifest_path, "release-manifest.txt"))
    try:
        manifest_changed = manifest_path.read_bytes() != manifest_bytes
    except OSError as exc:
        errors.append(f"cannot re-read release-manifest.txt safely: {exc}")
        manifest_changed = True
    if manifest_changed:
        errors.append("release-manifest.txt changed while capturing release inputs")
    if errors:
        raise ValueError("; ".join(errors))
    return manifest_bytes, tuple(sources)


def _archive_name(entry: str) -> str:
    prefix = "skills/research-writing/"
    if entry.startswith(prefix):
        return "research-writing/" + entry[len(prefix) :]
    return entry


def _collision_errors(
    records: list[ManifestRecord], label: str
) -> tuple[list[str], bool]:
    errors: list[str] = []
    collided = False
    transformations: tuple[tuple[str, Callable[[str], str]], ...] = (
        ("exact", lambda value: value),
        ("casefold", str.casefold),
        ("NFC", lambda value: unicodedata.normalize("NFC", value)),
        ("NFD", lambda value: unicodedata.normalize("NFD", value)),
        (
            "NFC+casefold",
            lambda value: unicodedata.normalize("NFC", value).casefold(),
        ),
        (
            "NFD+casefold",
            lambda value: unicodedata.normalize("NFD", value).casefold(),
        ),
    )
    for kind, transform in transformations:
        seen: dict[str, ManifestRecord] = {}
        for record in records:
            key = transform(record.value)
            previous = seen.get(key)
            if previous is None:
                seen[key] = record
                continue
            if kind != "exact" and previous.value == record.value:
                continue
            collided = True
            errors.append(
                f"{label} {kind} collision between line {previous.line_number} "
                f"{ascii(previous.value)} and line {record.line_number} "
                f"{ascii(record.value)}"
            )
    return errors, collided


def _markdown_destination(raw: str) -> str:
    destination = raw.strip()
    if destination.startswith("<"):
        closing = destination.find(">", 1)
        return destination[1:closing] if closing != -1 else destination
    return destination.split(maxsplit=1)[0] if destination else ""


def _markdown_targets(text: str) -> list[str]:
    targets = [_markdown_destination(match.group(1)) for match in INLINE_LINK_RE.finditer(text)]
    targets.extend(
        _markdown_destination(match.group(1)) for match in REFERENCE_LINK_RE.finditer(text)
    )
    return targets


def _validate_skill_markdown(skill_dir: Path, root: Path, errors: list[str]) -> bool:
    invalid = False
    skill_file = skill_dir / "SKILL.md"
    fixed_file_errors = _fixed_file_guard(
        root, skill_file, "skills/research-writing/SKILL.md"
    )
    if fixed_file_errors:
        errors.extend(fixed_file_errors)
        return True
    if not skill_file.is_file():
        errors.append("skills/research-writing/SKILL.md is missing")
        return True

    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read skills/research-writing/SKILL.md: {exc}")
        return True

    try:
        metadata, _ = split_frontmatter(text)
    except ValueError as exc:
        errors.append(str(exc))
        invalid = True
    else:
        if set(metadata) != {"name", "description"}:
            errors.append("SKILL.md frontmatter keys must be exactly name and description")
            invalid = True
        if metadata.get("name") != "research-writing":
            errors.append("SKILL.md frontmatter name must be research-writing")
            invalid = True
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append("SKILL.md frontmatter description must be a non-empty string")
            invalid = True
        else:
            if not description.startswith("Use when "):
                errors.append("SKILL.md description must start with 'Use when '")
                invalid = True
            if len(description) > 1024:
                errors.append("SKILL.md description must be at most 1024 characters")
                invalid = True

    skill_root = skill_dir.resolve(strict=True)
    for raw_target in _markdown_targets(text):
        decoded_target = unquote(raw_target)
        if not decoded_target or decoded_target.startswith("#"):
            continue

        parsed = urlsplit(decoded_target)
        scheme = parsed.scheme.casefold()
        if scheme:
            if scheme in ALLOWED_EXTERNAL_SCHEMES:
                if scheme in {"http", "https"} and not parsed.netloc:
                    errors.append(f"SKILL.md has a malformed external link: {ascii(raw_target)}")
                    invalid = True
                continue
            errors.append(
                f"SKILL.md uses unsupported URI scheme {ascii(scheme)}: "
                f"{ascii(raw_target)}"
            )
            invalid = True
            continue
        if decoded_target.startswith("//"):
            errors.append(f"SKILL.md uses a scheme-relative external link: {ascii(raw_target)}")
            invalid = True
            continue

        target = decoded_target.split("#", 1)[0]
        if not target:
            continue
        if "\\" in target:
            errors.append(f"SKILL.md link uses a backslash: {ascii(raw_target)}")
            invalid = True
            continue
        relative = PurePosixPath(target)
        candidate = skill_dir.joinpath(*relative.parts)
        containment = _containment_errors(root, candidate, f"SKILL.md link {ascii(raw_target)}")
        if relative.is_absolute() or ".." in relative.parts or containment:
            errors.append(f"SKILL.md link escapes the Skill directory: {ascii(raw_target)}")
            errors.extend(containment)
            invalid = True
            continue
        try:
            inside_skill = candidate.resolve(strict=False).is_relative_to(skill_root)
        except OSError:
            inside_skill = False
        if not inside_skill:
            errors.append(f"SKILL.md link escapes the Skill directory: {ascii(raw_target)}")
            invalid = True
        elif not candidate.is_file() or _is_link(candidate):
            errors.append(f"SKILL.md link target is not an ordinary file: {ascii(raw_target)}")
            invalid = True
    return invalid


def _allowed_uri_span_end(text: str, start: int) -> int:
    parentheses = 0
    brackets = 0
    index = start
    while index < len(text):
        character = text[index]
        if character.isspace() or character in URI_BOUNDARY_CHARACTERS:
            break
        if character == "(":
            parentheses += 1
        elif character == ")":
            if parentheses == 0:
                break
            parentheses -= 1
        elif character == "[":
            brackets += 1
        elif character == "]":
            if brackets == 0:
                break
            brackets -= 1
        index += 1
    return index


def _is_maskable_allowed_uri(candidate: str) -> bool:
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return False
    scheme = parsed.scheme.casefold()
    if scheme not in ALLOWED_EXTERNAL_SCHEMES:
        return False
    return scheme not in {"http", "https"} or bool(parsed.netloc)


def _masked_for_local_path_scan(text: str) -> str:
    masked = list(text)
    search_from = 0
    while match := ALLOWED_URI_START_RE.search(text, search_from):
        start = match.start()
        end = _allowed_uri_span_end(text, start)
        candidate = text[start:end]
        if _is_maskable_allowed_uri(candidate):
            masked[start:end] = " " * (end - start)
        search_from = max(end, match.end())
    return "".join(masked)


def _local_path_errors(text: str, label: str) -> list[str]:
    scan_text = _masked_for_local_path_scan(text)
    checks = (
        (FILE_URI_RE, "local file URI"),
        (WINDOWS_DRIVE_PATH_RE, "local Windows drive path"),
        (WINDOWS_DRIVE_RELATIVE_RE, "local Windows drive-relative path"),
        (UNC_PATH_RE, "local UNC path"),
        (NETWORK_PATH_RE, "local network path"),
        (WINDOWS_ROOTED_PATH_RE, "local Windows rooted path"),
        (POSIX_ROOTED_PATH_RE, "local POSIX rooted path"),
        (TILDE_PATH_RE, "local tilde path"),
        (UNSUPPORTED_SCHEME_RE, "unsupported URI scheme"),
    )
    return [f"{description} found in {label}" for pattern, description in checks if pattern.search(scan_text)]


def _validate_skill_tree(
    skill_dir: Path, root: Path, errors: list[str]
) -> tuple[set[str], bool]:
    skill_files: set[str] = set()
    invalid = False
    for path in sorted(skill_dir.rglob("*"), key=lambda item: item.as_posix()):
        relative_to_root = path.relative_to(root).as_posix()
        containment = _containment_errors(root, path, relative_to_root)
        if containment:
            errors.extend(containment)
            invalid = True
            continue
        if _is_link(path):
            errors.append(f"Skill contains a symlink, junction, or reparse point: {relative_to_root}")
            invalid = True
            continue
        if any(part.casefold() == "__pycache__" for part in path.parts):
            errors.append(f"Skill contains a cache path: {relative_to_root}")
            invalid = True
        if not path.is_file():
            continue

        skill_files.add(relative_to_root)
        suffix = path.suffix.casefold()
        if suffix in FORBIDDEN_SUFFIXES:
            errors.append(f"Skill contains a forbidden file type: {relative_to_root}")
            invalid = True
            continue
        if suffix not in TEXT_EXTENSIONS:
            errors.append(f"unsupported Skill file type: {relative_to_root}")
            invalid = True
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {relative_to_root} as UTF-8 text: {exc}")
            invalid = True
            continue

        local_errors = _local_path_errors(text, relative_to_root)
        if local_errors:
            errors.extend(local_errors)
            invalid = True
    return skill_files, invalid


def _validate_agent_metadata(skill_dir: Path, errors: list[str]) -> bool:
    invalid = False
    agent_file = skill_dir / "agents" / "openai.yaml"
    fixed_file_errors = _fixed_file_guard(
        skill_dir.parent.parent, agent_file, "skills/research-writing/agents/openai.yaml"
    )
    if fixed_file_errors:
        errors.extend(fixed_file_errors)
        return True
    if not agent_file.is_file():
        errors.append("skills/research-writing/agents/openai.yaml is missing")
        return True
    try:
        document = _strict_yaml_load(agent_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"cannot parse agents/openai.yaml: {exc}")
        return True
    if not isinstance(document, dict):
        errors.append("agents/openai.yaml document must be a mapping")
        return True
    if set(document) != {"interface"}:
        errors.append("agents/openai.yaml top-level keys must be exactly interface")
        invalid = True
    interface = document.get("interface")
    if not isinstance(interface, dict):
        errors.append("agents/openai.yaml interface must be a mapping")
        return True

    expected_keys = {"display_name", "short_description", "default_prompt"}
    if set(interface) != expected_keys:
        errors.append(
            "agents/openai.yaml interface keys must be exactly display_name, "
            "short_description, and default_prompt"
        )
        invalid = True
    for key in expected_keys:
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"agents/openai.yaml {key} must be a non-empty string")
            invalid = True

    short_description = interface.get("short_description")
    if isinstance(short_description, str) and not 25 <= len(short_description) <= 64:
        errors.append("agents/openai.yaml short_description must be 25-64 characters")
        invalid = True
    default_prompt = interface.get("default_prompt")
    if isinstance(default_prompt, str) and "$research-writing" not in default_prompt:
        errors.append("agents/openai.yaml default_prompt must contain $research-writing")
        invalid = True
    return invalid


def _validate_evidence_ledger(skill_dir: Path, errors: list[str]) -> None:
    ledger_path = skill_dir / "assets" / "evidence-ledger.csv"
    fixed_file_errors = _fixed_file_guard(
        skill_dir.parent.parent,
        ledger_path,
        "skills/research-writing/assets/evidence-ledger.csv",
    )
    if fixed_file_errors:
        errors.extend(fixed_file_errors)
        return
    try:
        with ledger_path.open(encoding="utf-8", newline="") as stream:
            ledger_rows = list(csv.reader(stream))
    except FileNotFoundError:
        errors.append("missing assets/evidence-ledger.csv")
        return
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot parse assets/evidence-ledger.csv: {exc}")
        return

    if not ledger_rows or ledger_rows[0] != EXPECTED_LEDGER_HEADER:
        errors.append("evidence ledger header does not match canonical schema")
    elif (
        len(ledger_rows) != 2
        or len(ledger_rows[1]) != len(EXPECTED_LEDGER_HEADER)
        or any(
            ledger_rows[1][EXPECTED_LEDGER_HEADER.index(field)].strip() != expected
            for field, expected in REQUIRED_INSTRUCTIONAL_LEDGER_FIELDS.items()
        )
        or not ledger_rows[1][EXPECTED_LEDGER_HEADER.index("action")].strip()
    ):
        errors.append("evidence ledger must contain one complete instructional row")


def _source_matrix_lines(text: str) -> list[str]:
    lines = text.splitlines()
    heading = "## Principle-to-source matrix"
    try:
        heading_index = lines.index(heading)
    except ValueError:
        return []

    table_lines: list[str] = []
    table_started = False
    for line in lines[heading_index + 1 :]:
        if not table_started and not line.strip():
            continue
        if line.startswith("|"):
            table_started = True
            table_lines.append(line)
        else:
            break
    return table_lines


def _source_matrix_cells(line: str) -> list[str] | None:
    """Split one pipe-table row while honoring escaped pipe characters."""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None

    raw_cells: list[str] = []
    current: list[str] = []
    backslashes = 0
    for character in stripped:
        if character == "\\":
            current.append(character)
            backslashes += 1
            continue
        if character == "|" and backslashes % 2 == 0:
            raw_cells.append("".join(current))
            current = []
        else:
            if character == "|" and current:
                current.pop()
            current.append(character)
        backslashes = 0

    if current or not raw_cells or raw_cells[0] != "":
        return None
    return [cell.strip() for cell in raw_cells[1:]]


def _validate_source_foundations(skill_dir: Path, errors: list[str]) -> None:
    source_path = skill_dir / "references" / "source-foundations.md"
    fixed_file_errors = _fixed_file_guard(
        skill_dir.parent.parent,
        source_path,
        "skills/research-writing/references/source-foundations.md",
    )
    if fixed_file_errors:
        errors.extend(fixed_file_errors)
        return
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append("missing references/source-foundations.md")
        return
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read references/source-foundations.md: {exc}")
        return

    table_lines = _source_matrix_lines(source_text)
    if not table_lines:
        errors.append("source foundations table header is not canonical")
        return

    header = _source_matrix_cells(table_lines[0])
    if header != EXPECTED_SOURCE_HEADER:
        errors.append("source foundations table header is not canonical")
        return
    if len(table_lines) < 2:
        errors.append("source foundations table separator is missing")
        return

    separator = _source_matrix_cells(table_lines[1])
    if (
        separator is None
        or len(separator) != len(EXPECTED_SOURCE_HEADER)
        or any(re.fullmatch(r":?-{3,}:?", cell) is None for cell in separator)
    ):
        errors.append("source foundations table separator is not canonical")

    raw_data_lines = table_lines[2:]
    if len(raw_data_lines) != 30:
        errors.append(
            "source foundations must contain exactly thirty atomic provenance rows"
        )

    parsed_rows: list[tuple[int, list[str]]] = []
    for line_number, line in enumerate(raw_data_lines, start=3):
        cells = _source_matrix_cells(line)
        if cells is None:
            errors.append(f"source foundations table row {line_number} is not a valid pipe row")
            continue
        if len(cells) != len(EXPECTED_SOURCE_HEADER):
            errors.append(
                f"source foundations data row {line_number} must contain exactly eight cells"
            )
            continue
        parsed_rows.append((line_number, cells))

    actual_pairs: list[tuple[str, str]] = []
    for line_number, row in parsed_rows:
        (
            principle,
            source_type,
            supplied,
            extension,
            skill_rule,
            applicability,
            canonical_url,
            access_date,
        ) = row
        for column_name, cell in zip(EXPECTED_SOURCE_HEADER, row):
            if not cell:
                errors.append(
                    f"source foundations data row {line_number} has empty {column_name}"
                )

        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(
                f"source foundations data row {line_number} has invalid source type and authority"
            )
        if len(skill_rule) < 40:
            errors.append(
                f"source foundations data row {line_number} has incomplete Skill rule"
            )
        if len(applicability) < 30:
            errors.append(
                f"source foundations data row {line_number} has incomplete applicability or conflict"
            )

        if ";" in supplied or ";" in extension:
            errors.append(
                f"source foundations data row {line_number} must contain one source contribution without semicolons"
            )

        source_marker: str | None = None
        if supplied == UPSTREAM_SOURCE_GAP:
            if EXTENSION_LOCATOR_RE.fullmatch(extension) is None:
                errors.append(
                    f"source foundations data row {line_number} has invalid extension locator"
                )
            extension_matches = [
                marker
                for marker in SOURCE_FOUNDATION_EXTENSION_MARKERS
                if marker in extension
            ]
            if len(extension_matches) == 1:
                source_marker = extension_matches[0]
            else:
                errors.append(
                    f"source foundations data row {line_number} must identify one approved extension source"
                )
        elif supplied in DIRECT_SUPPLIED_LOCATORS:
            source_marker = TECHNICAL_WRITING_MARKER
            if extension != DIRECT_EXTENSION_MARKER:
                errors.append(
                    f"source foundations data row {line_number} has invalid direct-evidence extension marker"
                )
        else:
            errors.append(
                f"source foundations data row {line_number} has invalid supplied PDF locator"
            )

        if source_marker is not None:
            locator = (
                supplied
                if source_marker == TECHNICAL_WRITING_MARKER
                else extension
            )
            if EXPECTED_SOURCE_LOCATORS.get((principle, source_marker)) != locator:
                errors.append(
                    f"source foundations data row {line_number} locator does not match source contribution"
                )

        https_matches = HTTPS_URL_RE.findall(canonical_url)
        if canonical_url.startswith("https://"):
            if len(https_matches) != 1 or HTTPS_URL_RE.fullmatch(canonical_url) is None:
                errors.append(
                    f"source foundations data row {line_number} must contain exactly one HTTPS URL"
                )
        elif canonical_url not in {UNAVAILABLE_URL_MARKER, DIRECT_URL_MARKER}:
            errors.append(
                f"source foundations data row {line_number} must contain exactly one HTTPS URL or an exact unavailable marker"
            )

        valid_access_date = access_date == UNAVAILABLE_DATE_MARKER
        if ISO_DATE_RE.fullmatch(access_date):
            try:
                date.fromisoformat(access_date)
            except ValueError:
                pass
            else:
                valid_access_date = True
        if not valid_access_date:
            errors.append(
                f"source foundations data row {line_number} has invalid access date"
            )
        if canonical_url.startswith("https://") and access_date != "2026-08-07":
            errors.append(
                f"source foundations data row {line_number} HTTPS access date must be 2026-08-07"
            )

        if supplied in DIRECT_SUPPLIED_LOCATORS:
            if canonical_url != DIRECT_URL_MARKER:
                errors.append(
                    f"source foundations data row {line_number} has invalid direct-evidence canonical URL marker"
                )
            if access_date != UNAVAILABLE_DATE_MARKER:
                errors.append(
                    f"source foundations data row {line_number} has invalid direct-evidence access date"
                )
        elif canonical_url == DIRECT_URL_MARKER:
            errors.append(
                f"source foundations data row {line_number} misplaces the direct-evidence canonical URL marker"
            )

        if (
            source_marker is not None
            and canonical_url != EXPECTED_SOURCE_URLS[source_marker]
        ):
            errors.append(
                f"source foundations data row {line_number} canonical URL does not match source contribution"
            )

        if source_marker is not None:
            actual_pairs.append((principle, source_marker))

    matrix_text = "\n".join(raw_data_lines)
    supplied_text = "\n".join(row[2] for _, row in parsed_rows)
    extension_text = "\n".join(row[3] for _, row in parsed_rows)
    for marker in SOURCE_FOUNDATION_EXTENSION_MARKERS:
        if marker not in extension_text:
            errors.append(f"source foundation missing extension marker: {marker}")
    if TECHNICAL_WRITING_MARKER not in supplied_text:
        errors.append(
            f"source foundation missing supplied-PDF marker: {TECHNICAL_WRITING_MARKER}"
        )
    if sorted(actual_pairs) != sorted(EXPECTED_SOURCE_PAIRS):
        errors.append(
            "source foundations principle-source pairs do not match the canonical thirty contributions"
        )
    for marker in SOURCE_FOUNDATION_OUTSIDE_MARKERS:
        if marker not in source_text:
            errors.append(f"source foundation missing outside-matrix marker: {marker}")
        if marker in matrix_text:
            errors.append(f"source foundation outside-matrix marker appears in matrix: {marker}")


def validate_repository(root: Path = ROOT) -> list[str]:
    root = Path(root)
    skill_dir = root / "skills" / "research-writing"
    legacy_skill_dir = root / "research-writing"
    manifest_path = root / "release-manifest.txt"
    errors: list[str] = []

    if sys.version_info < (3, 12):
        errors.append(
            "Python 3.12 or newer is required for junction and reparse-point validation"
        )

    manifest_control_errors = _ordinary_file_errors(
        root, manifest_path, "release-manifest.txt"
    )
    errors.extend(manifest_control_errors)
    if manifest_control_errors:
        records: list[ManifestRecord] = []
    else:
        try:
            records = manifest_records(root)
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read release-manifest.txt: {exc}")
            records = []

    if legacy_skill_dir.exists() or _is_link(legacy_skill_dir):
        errors.append("legacy research-writing directory must not exist at repository root")

    skill_invalid = False
    skill_containment = _containment_errors(root, skill_dir, "skills/research-writing")
    if not skill_dir.is_dir():
        errors.append("Skill must be located at skills/research-writing")
        skill_files: set[str] = set()
        skill_invalid = True
    elif skill_containment:
        errors.extend(skill_containment)
        skill_files = set()
        skill_invalid = True
    else:
        if (skill_dir / "evals").exists() or _is_link(skill_dir / "evals"):
            errors.append("Skill must not contain evals")
            skill_invalid = True
        corpus_script = skill_dir / "scripts" / "corpus.py"
        if corpus_script.exists() or _is_link(corpus_script):
            errors.append("Skill must not contain scripts/corpus.py")
            skill_invalid = True
        skill_files, tree_invalid = _validate_skill_tree(skill_dir, root, errors)
        markdown_invalid = _validate_skill_markdown(skill_dir, root, errors)
        agent_invalid = _validate_agent_metadata(skill_dir, errors)
        skill_invalid = skill_invalid or tree_invalid or markdown_invalid or agent_invalid

    values = [record.value for record in records]
    manifest_invalid = bool(manifest_control_errors)
    if values != sorted(values):
        errors.append("release-manifest.txt entries must be sorted lexically")
        manifest_invalid = True

    manifest_collision_errors, manifest_collided = _collision_errors(
        records, "manifest entry"
    )
    errors.extend(manifest_collision_errors)
    manifest_invalid = manifest_invalid or manifest_collided

    archive_records = [
        ManifestRecord(record.line_number, _archive_name(record.value)) for record in records
    ]
    archive_collision_errors, archive_collided = _collision_errors(
        archive_records, "archive name"
    )
    errors.extend(archive_collision_errors)
    manifest_invalid = manifest_invalid or archive_collided

    for legal_name in sorted(ALLOWED_ROOT_RELEASE_FILES):
        count = values.count(legal_name)
        if count != 1:
            errors.append(
                f"{legal_name} must appear exactly once in release-manifest.txt; found {count}"
            )
            manifest_invalid = True
        legal_errors = _ordinary_file_errors(root, root / legal_name, legal_name)
        if legal_errors:
            errors.extend(legal_errors)
            manifest_invalid = True
            continue
        try:
            legal_bytes = (root / legal_name).read_bytes()
            legal_text = legal_bytes.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {legal_name} as UTF-8 release text: {exc}")
            manifest_invalid = True
            continue
        if legal_name == "LICENSE":
            digest = sha256(legal_bytes).hexdigest()
            if digest != CANONICAL_LICENSE_SHA256:
                errors.append(
                    "LICENSE must be the canonical Apache License 2.0 text; "
                    f"found SHA-256 {digest}"
                )
                manifest_invalid = True
        local_errors = _local_path_errors(legal_text, legal_name)
        if local_errors:
            errors.extend(local_errors)
            manifest_invalid = True

    manifest_skill_files: set[str] = set()
    for record in records:
        entry = record.value
        path_errors = _manifest_path_errors(entry)
        if path_errors:
            manifest_invalid = True
            errors.extend(
                f"invalid manifest entry at line {record.line_number} {ascii(entry)}: {message}"
                for message in path_errors
            )
            continue

        relative = PurePosixPath(entry)
        target = root.joinpath(*relative.parts)
        target_errors = _ordinary_file_errors(
            root, target, f"manifest target at line {record.line_number} {ascii(entry)}"
        )
        if target_errors:
            errors.extend(target_errors)
            manifest_invalid = True
            continue
        if entry.startswith("skills/research-writing/"):
            manifest_skill_files.add(entry)

    if not manifest_invalid and not skill_invalid and skill_files != manifest_skill_files:
        missing = sorted(skill_files - manifest_skill_files)
        extra = sorted(manifest_skill_files - skill_files)
        if missing:
            errors.append("Skill files missing from manifest: " + ", ".join(missing))
        if extra:
            errors.append("manifest lists non-physical Skill files: " + ", ".join(extra))

    if skill_dir.is_dir() and not skill_containment:
        _validate_evidence_ledger(skill_dir, errors)
        _validate_source_foundations(skill_dir, errors)
    return errors


def _console_safe(text: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, errors="backslashreplace").decode(encoding)


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            for line in str(error).splitlines() or [""]:
                print(f"ERROR: {_console_safe(line)}")
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
