from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CODEX_EXECUTABLE = (
    r"C:\Users\31933\.vscode\extensions\openai.chatgpt-26.803.61601-win32-x64"
    r"\bin\windows-x86_64\codex.exe"
)
EXPECTED_CODEX_EXECUTABLE_LENGTH = 293478192
EXPECTED_CODEX_EXECUTABLE_SHA256 = (
    "115518500b45188e410a15d3224c2bbc87df6f2209729bf327aaf7808ca9d5a6"
)
EXPECTED_VERSION = "codex-cli 0.147.0-alpha.6.5"
AUDIT_SCOPE = "model-directed JSONL events and model-root snapshots"
MAX_STABLE_READ_BYTES = 64 * 1024 * 1024
MAX_CAPTURED_STREAM_BYTES = 64 * 1024 * 1024
MAX_GIT_OUTPUT_BYTES = 64 * 1024 * 1024

EXPECTED_SKILL_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "assets/evidence-ledger.csv",
    "assets/writing-brief.md",
    "references/evidence-and-integrity.md",
    "references/revision-and-style.md",
    "references/section-guides.md",
    "references/source-foundations.md",
    "references/writing-workflow.md",
]
EXPECTED_CASES = [
    {"id": "01-outline", "path": "evals/cases/01-outline.md"},
    {"id": "02-revision", "path": "evals/cases/02-revision.md"},
    {"id": "03-integrity", "path": "evals/cases/03-integrity.md"},
    {"id": "04-compression", "path": "evals/cases/04-compression.md"},
    {
        "id": "05-source-foundations",
        "path": "evals/cases/05-source-foundations.md",
    },
    {
        "id": "06-genre-flexibility",
        "path": "evals/cases/06-genre-flexibility.md",
    },
    {
        "id": "07-proportional-edit",
        "path": "evals/cases/07-proportional-edit.md",
    },
]
EXPECTED_FIXED_FLAGS = [
    "--strict-config",
    "--ephemeral",
    "--ignore-rules",
    "--skip-git-repo-check",
    "--json",
    "-o",
    "raw.md",
    "-",
]
EXPECTED_DISABLED_FEATURES = [
    "apps",
    "enable_mcp_apps",
    "auth_elicitation",
    "tool_call_mcp_elicitation",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "in_app_browser",
    "computer_use",
    "hooks",
    "image_generation",
    "multi_agent",
    "multi_agent_v2",
    "plugins",
    "remote_plugin",
    "recommended_plugins",
    "plugin_sharing",
    "skill_search",
    "skill_mcp_dependency_install",
    "workspace_dependencies",
    "standalone_web_search",
]
EXPECTED_CONFIG_OVERRIDES = [
    'model_provider="custom"',
    'model_reasoning_effort="medium"',
    'web_search="disabled"',
    "tools.web_search=false",
    "mcp_servers={}",
    "plugins={}",
    "apps._default.enabled=false",
    "project_doc_max_bytes=0",
    'shell_environment_policy.inherit="none"',
]
EXPECTED_ROOT_ENTRIES = ["research-writing", "case.md", "raw.md"]
EXPECTED_ALLOWED_EVENTS = [
    "thread.started",
    "turn.started",
    "item.started",
    "item.updated",
    "item.completed",
    "turn.completed",
]
EXPECTED_ALLOWED_ITEMS = ["reasoning", "command_execution", "agent_message"]
EXPECTED_FORBIDDEN_ITEMS = [
    "file_change",
    "mcp_tool_call",
    "web_search",
    "plan",
    "tool_suggestion",
    "browser",
    "browser_use",
    "computer",
    "computer_use",
    "image",
    "image_generation",
    "collaboration",
    "subagent",
    "agent_tool_call",
]

TOP_LEVEL_FIELDS = {"schema_version", "source", "codex", "audit"}
SOURCE_FIELDS = {
    "runner_path",
    "config_path",
    "prompt_wrapper_path",
    "rubric_path",
    "skill_source_dir",
    "skill_mount_dir",
    "skill_files",
    "cases",
}
CASE_FIELDS = {"id", "path"}
CODEX_FIELDS = {
    "executable",
    "executable_length",
    "executable_sha256",
    "expected_version",
    "model",
    "model_provider",
    "reasoning_effort",
    "sandbox",
    "approval_policy",
    "case_timeout_seconds",
    "fixed_flags",
    "disabled_features",
    "config_overrides",
}
AUDIT_FIELDS = {
    "root_entries",
    "allowed_event_types",
    "allowed_item_types",
    "forbidden_item_types",
}
FULL_OBJECT_ID_RE = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\Z")
OBJECT_ID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
CASE_ID_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\Z")
FEATURE_LINE_RE = re.compile(r"^(\S+)\s+.+?\s+(true|false)$")
WINDOWS_INVALID_CHARS = frozenset('<>"|?*')
WINDOWS_POWERSHELL_EXECUTABLE = (
    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
)


class RunnerError(Exception):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RunnerError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise RunnerError(f"non-standard JSON constant is forbidden: {value}")


def _validate_json_value(value: Any, context: str) -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise RunnerError(f"{context} contains an invalid Unicode scalar") from exc
    elif isinstance(value, float) and not math.isfinite(value):
        raise RunnerError(f"{context} contains a non-finite number")
    elif isinstance(value, list):
        for item in value:
            _validate_json_value(item, context)
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_json_value(key, context)
            _validate_json_value(item, context)


def _decode_json(data: bytes, context: str) -> Any:
    if len(data) > MAX_CAPTURED_STREAM_BYTES:
        raise RunnerError(
            f"{context} exceeds the {MAX_CAPTURED_STREAM_BYTES} byte limit"
        )
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RunnerError(f"{context} is not strict UTF-8: {exc}") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except RunnerError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise RunnerError(f"{context} is not valid JSON: {exc}") from exc
    try:
        _validate_json_value(value, context)
    except RecursionError as exc:
        raise RunnerError(f"{context} is too deeply nested") from exc
    return value


def decode_config(data: bytes) -> dict[str, Any]:
    value = _decode_json(data, "runner config")
    if not isinstance(value, dict):
        raise RunnerError("runner config must be a JSON object")
    return value


def _expect_keys(value: Any, expected: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunnerError(f"{context} must be an object")
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise RunnerError(
            f"{context} fields mismatch; missing={missing!r}, unknown={unknown!r}"
        )
    return value


def _expect_string_list(value: Any, context: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RunnerError(f"{context} must be an array of strings")
    if len(value) != len(set(value)):
        raise RunnerError(f"{context} must not contain duplicates")
    return value


def validate_relative_path(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise RunnerError(f"{context} must be a non-empty relative path")
    if "\\" in value:
        raise RunnerError(f"{context} must use forward slashes")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive or windows.root:
        raise RunnerError(f"{context} must not be absolute: {value!r}")
    if posix.as_posix() != value or any(part in ("", ".", "..") for part in posix.parts):
        raise RunnerError(f"{context} is not a canonical relative path: {value!r}")
    for part in posix.parts:
        if part != part.rstrip(" .") or ":" in part:
            raise RunnerError(f"{context} has an unsafe path component: {part!r}")
        if any(character in WINDOWS_INVALID_CHARS for character in part):
            raise RunnerError(f"{context} has an unsafe path component: {part!r}")
        if PureWindowsPath(part).is_reserved():
            raise RunnerError(f"{context} has a reserved path component: {part!r}")
    return value


def validate_config_dict(config: dict[str, Any]) -> None:
    config = _expect_keys(config, TOP_LEVEL_FIELDS, "config")
    if config["schema_version"] != 1 or isinstance(config["schema_version"], bool):
        raise RunnerError("schema_version must be exactly 1")

    source = _expect_keys(config["source"], SOURCE_FIELDS, "source")
    expected_paths = {
        "runner_path": "tools/run_evals.py",
        "config_path": "evals/runner-config.json",
        "prompt_wrapper_path": "evals/prompt-wrapper.md",
        "rubric_path": "evals/rubric.md",
        "skill_source_dir": "skills/research-writing",
        "skill_mount_dir": "research-writing",
    }
    for field, expected in expected_paths.items():
        actual = validate_relative_path(source[field], f"source.{field}")
        if actual != expected:
            raise RunnerError(f"source.{field} must be exactly {expected!r}")
    skill_files = _expect_string_list(source["skill_files"], "source.skill_files")
    for index, path in enumerate(skill_files):
        validate_relative_path(path, f"source.skill_files[{index}]")
    if skill_files != EXPECTED_SKILL_FILES:
        raise RunnerError("schema v1 requires the fixed nine Skill files in order")

    cases = source["cases"]
    if not isinstance(cases, list):
        raise RunnerError("source.cases must be an array")
    normalized_cases: list[dict[str, str]] = []
    for index, case in enumerate(cases):
        case = _expect_keys(case, CASE_FIELDS, f"source.cases[{index}]")
        case_id = case["id"]
        if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
            raise RunnerError(f"source.cases[{index}].id is invalid")
        path = validate_relative_path(case["path"], f"source.cases[{index}].path")
        normalized_cases.append({"id": case_id, "path": path})
    if normalized_cases != EXPECTED_CASES:
        raise RunnerError("schema v1 requires the fixed seven unique cases in order")

    codex = _expect_keys(config["codex"], CODEX_FIELDS, "codex")
    exact_codex = {
        "executable": EXPECTED_CODEX_EXECUTABLE,
        "executable_length": EXPECTED_CODEX_EXECUTABLE_LENGTH,
        "executable_sha256": EXPECTED_CODEX_EXECUTABLE_SHA256,
        "expected_version": EXPECTED_VERSION,
        "model": "gpt-5.6-sol",
        "model_provider": "custom",
        "reasoning_effort": "medium",
        "sandbox": "read-only",
        "approval_policy": "never",
    }
    for field, expected in exact_codex.items():
        if codex[field] != expected:
            raise RunnerError(f"codex.{field} must be exactly {expected!r}")
    executable_length = codex["executable_length"]
    if (
        isinstance(executable_length, bool)
        or not isinstance(executable_length, int)
        or executable_length <= 0
    ):
        raise RunnerError("codex.executable_length must be a positive integer")
    executable_sha256 = codex["executable_sha256"]
    if (
        not isinstance(executable_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", executable_sha256) is None
    ):
        raise RunnerError("codex.executable_sha256 must be a lowercase SHA-256 digest")
    timeout = codex["case_timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 7200:
        raise RunnerError("codex.case_timeout_seconds must be an integer from 1 to 7200")
    fixed_flags = _expect_string_list(codex["fixed_flags"], "codex.fixed_flags")
    disabled = _expect_string_list(
        codex["disabled_features"], "codex.disabled_features"
    )
    overrides = _expect_string_list(codex["config_overrides"], "codex.config_overrides")
    if fixed_flags != EXPECTED_FIXED_FLAGS:
        raise RunnerError("codex.fixed_flags do not match the schema v1 invocation")
    if "--ignore-user-config" in fixed_flags:
        raise RunnerError("--ignore-user-config is forbidden")
    if disabled != EXPECTED_DISABLED_FEATURES:
        raise RunnerError("codex.disabled_features do not match schema v1")
    if overrides != EXPECTED_CONFIG_OVERRIDES:
        raise RunnerError("codex.config_overrides do not match schema v1")

    audit = _expect_keys(config["audit"], AUDIT_FIELDS, "audit")
    exact_audit = {
        "root_entries": EXPECTED_ROOT_ENTRIES,
        "allowed_event_types": EXPECTED_ALLOWED_EVENTS,
        "allowed_item_types": EXPECTED_ALLOWED_ITEMS,
        "forbidden_item_types": EXPECTED_FORBIDDEN_ITEMS,
    }
    for field, expected in exact_audit.items():
        actual = _expect_string_list(audit[field], f"audit.{field}")
        if actual != expected:
            raise RunnerError(f"audit.{field} does not match schema v1")


def validate_commit_argument(value: str) -> str:
    if not isinstance(value, str) or FULL_OBJECT_ID_RE.fullmatch(value) is None:
        raise RunnerError("--commit must be a full 40- or 64-hex object ID")
    return value.lower()


def validate_git_blob_mode(mode: str, path: str) -> None:
    if mode not in {"100644", "100755"}:
        raise RunnerError(f"frozen input is not an ordinary Git blob: {path} ({mode})")


def _git(repository: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", os.fspath(repository), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise RunnerError(f"Git command timed out ({' '.join(args)})") from exc
    if len(result.stdout) > MAX_GIT_OUTPUT_BYTES or len(result.stderr) > MAX_GIT_OUTPUT_BYTES:
        raise RunnerError(
            f"Git command output exceeds the {MAX_GIT_OUTPUT_BYTES} byte limit"
        )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="backslashreplace").strip()
        raise RunnerError(f"Git command failed ({' '.join(args)}): {detail}")
    return result.stdout


def _git_object_id(repository: Path, expression: str, expected_type: str) -> str:
    raw = _git(repository, "rev-parse", "--verify", "--end-of-options", expression)
    lines = raw.decode("ascii", errors="strict").splitlines()
    if len(lines) != 1 or OBJECT_ID_RE.fullmatch(lines[0]) is None:
        raise RunnerError(f"Git returned an invalid object ID for {expression!r}")
    object_id = lines[0]
    actual_type = _git(repository, "cat-file", "-t", object_id).decode("ascii").strip()
    if actual_type != expected_type:
        raise RunnerError(
            f"Git object {expression!r} is {actual_type!r}, expected {expected_type!r}"
        )
    return object_id


def _parse_ls_tree(data: bytes, context: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for raw_entry in data.split(b"\x00"):
        if not raw_entry:
            continue
        try:
            header, raw_path = raw_entry.split(b"\t", 1)
            mode, object_type, object_id = header.decode("ascii").split(" ")
            path = raw_path.decode("utf-8", errors="strict")
        except (ValueError, UnicodeDecodeError) as exc:
            raise RunnerError(f"malformed git ls-tree output for {context}") from exc
        if OBJECT_ID_RE.fullmatch(object_id) is None:
            raise RunnerError(f"invalid Git object ID for {path}")
        entries.append(
            {"mode": mode, "type": object_type, "object_id": object_id, "path": path}
        )
    return entries


def _git_blob_record(repository: Path, commit: str, path: str) -> dict[str, Any]:
    validate_relative_path(path, f"frozen path {path!r}")
    entries = _parse_ls_tree(
        _git(repository, "ls-tree", "-z", "--full-tree", commit, "--", path), path
    )
    exact = [entry for entry in entries if entry["path"] == path]
    if len(exact) != 1:
        raise RunnerError(f"frozen input is missing or ambiguous in commit: {path}")
    entry = exact[0]
    validate_git_blob_mode(entry["mode"], path)
    if entry["type"] != "blob":
        raise RunnerError(f"frozen input is not a blob: {path} ({entry['type']})")
    data = _git(repository, "cat-file", "blob", entry["object_id"])
    return {
        "path": path,
        "mode": entry["mode"],
        "blob_id": entry["object_id"],
        "length": len(data),
        "sha256": _sha256(data),
        "data": data,
    }


def _tree_file_paths(repository: Path, commit: str, prefix: str) -> set[str]:
    entries = _parse_ls_tree(
        _git(
            repository,
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            commit,
            "--",
            prefix,
        ),
        prefix,
    )
    paths: set[str] = set()
    for entry in entries:
        validate_git_blob_mode(entry["mode"], entry["path"])
        if entry["type"] != "blob":
            raise RunnerError(f"non-blob entry below {prefix}: {entry['path']}")
        validate_relative_path(entry["path"], "Git tree path")
        folded = entry["path"].casefold()
        if any(existing.casefold() == folded for existing in paths):
            raise RunnerError(f"case-colliding Git tree paths below {prefix}")
        paths.add(entry["path"])
    return paths


def _is_linklike(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        junction = getattr(path, "is_junction", None)
        if junction is not None and junction():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except FileNotFoundError:
        return False
    except OSError:
        return True
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(flag and attributes & flag)


def _stable_read(
    path: Path, context: str, max_bytes: int = MAX_STABLE_READ_BYTES
) -> bytes:
    path = _absolute(path)
    parent = path.parent
    parent_before = _directory_chain_identity(parent, f"{context} parent")
    _reject_linklike_components(path, context)
    if _is_linklike(path):
        raise RunnerError(f"{context} must not be a link or reparse point: {path}")
    try:
        before = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise RunnerError(f"cannot stat {context}: {path}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise RunnerError(f"{context} is not an ordinary file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        try:
            chunks: list[bytes] = []
            total = 0
            opened_before = os.fstat(descriptor)
            _assert_directory_chain_unchanged(
                parent, parent_before, f"{context} parent"
            )
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    raise RunnerError(
                        f"{context} exceeds the {max_bytes} byte read limit: {path}"
                    )
            opened_after = os.fstat(descriptor)
            _assert_directory_chain_unchanged(
                parent, parent_before, f"{context} parent"
            )
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise RunnerError(f"cannot read {context}: {path}: {exc}") from exc
    signature = lambda value: (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_nlink,
    )
    if signature(opened_before) != signature(opened_after):
        raise RunnerError(f"{context} changed while being read: {path}")
    try:
        after = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise RunnerError(f"cannot re-stat {context}: {path}: {exc}") from exc
    if signature(before) != signature(after) or _is_linklike(path):
        raise RunnerError(f"{context} identity changed while being read: {path}")
    _assert_directory_chain_unchanged(parent, parent_before, f"{context} parent")
    return b"".join(chunks)


def capture_frozen_inputs(
    repository: Path, commit_argument: str, runner_path: Path | None = None
) -> dict[str, Any]:
    repository = Path(os.path.abspath(os.fspath(repository)))
    commit_argument = validate_commit_argument(commit_argument)
    commit = _git_object_id(repository, f"{commit_argument}^{{commit}}", "commit")
    root_tree = _git_object_id(repository, f"{commit}^{{tree}}", "tree")

    config_record = _git_blob_record(repository, commit, "evals/runner-config.json")
    config = decode_config(config_record["data"])
    validate_config_dict(config)
    source = config["source"]
    skill_tree = _git_object_id(repository, f"{commit}:{source['skill_source_dir']}", "tree")
    cases_tree = _git_object_id(repository, f"{commit}:evals/cases", "tree")

    expected_skill_paths = {
        f"{source['skill_source_dir']}/{relative}" for relative in source["skill_files"]
    }
    actual_skill_paths = _tree_file_paths(repository, commit, source["skill_source_dir"])
    if actual_skill_paths != expected_skill_paths:
        raise RunnerError(
            "Skill tree does not contain exactly the nine configured files; "
            f"missing={sorted(expected_skill_paths - actual_skill_paths)!r}, "
            f"extra={sorted(actual_skill_paths - expected_skill_paths)!r}"
        )
    expected_case_paths = {case["path"] for case in source["cases"]}
    actual_case_paths = _tree_file_paths(repository, commit, "evals/cases")
    if actual_case_paths != expected_case_paths:
        raise RunnerError(
            "case tree does not contain exactly the seven configured cases; "
            f"missing={sorted(expected_case_paths - actual_case_paths)!r}, "
            f"extra={sorted(actual_case_paths - expected_case_paths)!r}"
        )

    manifest_record = _git_blob_record(repository, commit, "release-manifest.txt")
    try:
        manifest_text = manifest_record["data"].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RunnerError("release-manifest.txt is not strict UTF-8") from exc
    manifest_entries = [
        line.strip()
        for line in manifest_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(manifest_entries) != len(set(manifest_entries)):
        raise RunnerError("release-manifest.txt has duplicate entries")
    manifest_skill_paths = [
        path for path in manifest_entries if path.startswith("skills/research-writing/")
    ]
    if manifest_skill_paths != sorted(expected_skill_paths):
        raise RunnerError("release-manifest.txt does not specify the fixed nine Skill files")

    frozen_paths = [
        "release-manifest.txt",
        source["runner_path"],
        source["config_path"],
        source["prompt_wrapper_path"],
        source["rubric_path"],
        *sorted(expected_skill_paths),
        *(case["path"] for case in source["cases"]),
    ]
    if len(frozen_paths) != len(set(frozen_paths)):
        raise RunnerError("frozen paths conflict")
    folded: set[str] = set()
    for path in frozen_paths:
        validate_relative_path(path, "frozen path")
        if path.casefold() in folded:
            raise RunnerError(f"case-colliding frozen path: {path}")
        folded.add(path.casefold())

    records: dict[str, dict[str, Any]] = {}
    for path in frozen_paths:
        if path == source["config_path"]:
            record = config_record
        elif path == "release-manifest.txt":
            record = manifest_record
        else:
            record = _git_blob_record(repository, commit, path)
        records[path] = record

    actual_runner_path = Path(runner_path) if runner_path is not None else Path(__file__)
    current_runner = _stable_read(actual_runner_path, "running evaluation runner")
    if current_runner != records[source["runner_path"]]["data"]:
        raise RunnerError("running tools/run_evals.py does not match the pinned Git blob")
    return {
        "commit_argument": commit_argument,
        "commit": commit,
        "root_tree": root_tree,
        "skill_tree": skill_tree,
        "cases_tree": cases_tree,
        "config": config,
        "files": records,
    }


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _contains(parent: Path, child: Path) -> bool:
    try:
        common = os.path.commonpath(
            [os.path.normcase(os.fspath(parent)), os.path.normcase(os.fspath(child))]
        )
    except ValueError:
        return False
    return common == os.path.normcase(os.fspath(parent))


def _existing_components(path: Path):
    path = _absolute(path)
    parts = path.parts
    if not parts:
        return
    current = Path(parts[0])
    if os.path.lexists(current):
        yield current
    for part in parts[1:]:
        current = current / part
        if not os.path.lexists(current):
            break
        yield current


def _reject_linklike_components(path: Path, context: str) -> None:
    try:
        components = list(_existing_components(path))
    except OSError as exc:
        raise RunnerError(f"cannot inspect {context}: {path}: {exc}") from exc
    for component in components:
        if _is_linklike(component):
            raise RunnerError(
                f"{context} has a symlink, junction, or reparse-point component: {component}"
            )


def _directory_identity_token(status: os.stat_result) -> tuple[int, int, int, int]:
    """Return identity-only fields for a directory.

    Directory size and timestamps legitimately change when files are created,
    so they are deliberately excluded. Device/inode (or their Windows
    equivalents exposed by os.stat), the file-type bits, and reparse
    attributes are stable enough to detect a parent replacement without
    turning ordinary child writes into false positives.
    """

    return (
        int(getattr(status, "st_dev", 0)),
        int(getattr(status, "st_ino", 0)),
        int(stat.S_IFMT(status.st_mode)),
        int(getattr(status, "st_file_attributes", 0)),
    )


def _directory_chain_identity(
    path: Path, context: str
) -> tuple[tuple[str, tuple[int, int, int, int]], ...]:
    """Snapshot every existing directory component of path.

    This is a portable (including Windows) substitute for directory handles.
    Callers compare the returned token before and after a pathname operation.
    It cannot close the final race window, but it detects a parent being
    replaced while the operation is in progress and fails closed on uncertain
    filesystem errors.
    """

    path = _absolute(path)
    try:
        components = list(_existing_components(path))
    except OSError as exc:
        raise RunnerError(f"cannot inspect {context}: {path}: {exc}") from exc
    if not components:
        raise RunnerError(f"{context} has no existing directory components: {path}")
    normalized_path = os.path.normcase(os.path.normpath(os.fspath(path)))
    normalized_last = os.path.normcase(
        os.path.normpath(os.fspath(components[-1]))
    )
    if normalized_last != normalized_path:
        raise RunnerError(f"{context} directory does not exist: {path}")

    snapshot: list[tuple[str, tuple[int, int, int, int]]] = []
    for component in components:
        if _is_linklike(component):
            raise RunnerError(
                f"{context} has a symlink, junction, or reparse-point component: {component}"
            )
        try:
            status = component.stat(follow_symlinks=False)
        except OSError as exc:
            raise RunnerError(f"cannot stat {context}: {component}: {exc}") from exc
        if not stat.S_ISDIR(status.st_mode):
            raise RunnerError(
                f"{context} component is not an ordinary directory: {component}"
            )
        snapshot.append(
            (
                os.path.normcase(os.path.normpath(os.fspath(component))),
                _directory_identity_token(status),
            )
        )
    return tuple(snapshot)


def _assert_directory_chain_unchanged(
    path: Path,
    before: tuple[tuple[str, tuple[int, int, int, int]], ...],
    context: str,
) -> None:
    after = _directory_chain_identity(path, context)
    if after != before:
        raise RunnerError(f"{context} identity changed during the operation: {path}")


def _require_directory(path: Path, context: str) -> None:
    """Require an existing ordinary, non-link directory."""

    path = _absolute(path)
    if _is_linklike(path):
        raise RunnerError(f"{context} must not be a link or reparse point: {path}")
    try:
        status = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise RunnerError(f"cannot stat {context}: {path}: {exc}") from exc
    if not stat.S_ISDIR(status.st_mode):
        raise RunnerError(f"{context} is not an ordinary directory: {path}")


def _ensure_directory_tree(
    path: Path, context: str
) -> tuple[tuple[str, tuple[int, int, int, int]], ...]:
    """Create missing ancestors one component at a time with revalidation.

    Recursive Path.mkdir can follow a concurrently substituted
    symlink/junction ancestor. Creating one component at a time lets us
    snapshot and revalidate the already-existing parent around each mkdir.
    """

    path = _absolute(path)
    parts = path.parts
    if not parts:
        raise RunnerError(f"{context} has an empty path")
    current = Path(parts[0])
    _require_directory(current, context)
    for part in parts[1:]:
        child = current / part
        try:
            exists = os.path.lexists(child)
        except OSError as exc:
            raise RunnerError(f"cannot inspect {context}: {child}: {exc}") from exc
        if exists:
            _require_directory(child, context)
            current = child
            continue

        parent_before = _directory_chain_identity(current, f"{context} parent")
        try:
            # parents=False is intentional: every ancestor is checked
            # independently before this call.
            child.mkdir(parents=False, exist_ok=False)
        except FileExistsError:
            # A concurrent creator is acceptable only if it produced an
            # ordinary directory, never a link/reparse point.
            _require_directory(child, context)
        except OSError as exc:
            raise RunnerError(f"cannot create {context}: {child}: {exc}") from exc
        _require_directory(child, context)
        _assert_directory_chain_unchanged(
            current, parent_before, f"{context} parent"
        )
        current = child
    return _directory_chain_identity(path, context)


def _mkdir_safe(path: Path, context: str) -> Path:
    """Create one new directory and revalidate its parent identity."""

    path = _absolute(path)
    try:
        if os.path.lexists(path):
            raise RunnerError(f"{context} must name a new, nonexistent directory: {path}")
    except OSError as exc:
        raise RunnerError(f"cannot inspect {context}: {path}: {exc}") from exc
    parent = path.parent
    parent_before = _directory_chain_identity(parent, f"{context} parent")
    try:
        path.mkdir(parents=False, exist_ok=False)
    except OSError as exc:
        raise RunnerError(f"cannot create {context}: {path}: {exc}") from exc
    try:
        _require_directory(path, context)
        _assert_directory_chain_unchanged(parent, parent_before, f"{context} parent")
    except BaseException:
        # The new entry belongs to this operation; remove it only when the
        # parent is still the snapshotted directory.
        try:
            _assert_directory_chain_unchanged(parent, parent_before, f"{context} parent")
            path.rmdir()
        except Exception:
            pass
        raise
    return path


def validate_output_path(output: Path, repository: Path) -> Path:
    output = _absolute(Path(output))
    repository = _absolute(Path(repository))
    if os.path.lexists(output):
        raise RunnerError("--output must name a new, nonexistent directory")
    if not repository.is_dir():
        raise RunnerError(f"repository root is not a directory: {repository}")
    parent = output.parent
    if not parent.is_dir():
        raise RunnerError("--output parent directory must already exist")
    _reject_linklike_components(output, "--output")
    repository_resolved = repository.resolve(strict=True)
    output_resolved = output.resolve(strict=False)
    if _contains(repository, output) or _contains(repository_resolved, output_resolved):
        raise RunnerError("--output must be outside the checkout")
    return output


def resolve_executable(
    configured: str, *, expected_length: int, expected_sha256: str
) -> tuple[Path, dict[str, Any]]:
    located = shutil.which(configured)
    candidate = Path(located) if located is not None else Path(configured)
    if not candidate.is_absolute():
        raise RunnerError("configured Codex executable did not resolve to an absolute path")
    candidate = _absolute(candidate)
    _reject_linklike_components(candidate, "Codex executable")
    data = _stable_read(
        candidate,
        "Codex executable",
        max_bytes=max(expected_length, MAX_STABLE_READ_BYTES),
    )
    observed_length = len(data)
    observed_sha256 = _sha256(data)
    if observed_length != expected_length or observed_sha256 != expected_sha256:
        raise RunnerError(
            "Codex executable does not match the pinned length or SHA-256 digest"
        )
    resolved = candidate.resolve(strict=True)
    identity = {
        "configured_path": configured,
        "resolved_path": os.fspath(resolved),
        "length": observed_length,
        "sha256": observed_sha256,
    }
    return resolved, identity


def verify_executable_identity(
    executable: Path, config: dict[str, Any], expected: dict[str, Any]
) -> dict[str, Any]:
    codex = config["codex"]
    resolved, observed = resolve_executable(
        codex["executable"],
        expected_length=codex["executable_length"],
        expected_sha256=codex["executable_sha256"],
    )
    if resolved != executable or observed != expected:
        raise RunnerError("Codex executable path or bytes changed after pinning")
    return observed


def _config_arguments(config: dict[str, Any]) -> list[str]:
    codex = config["codex"]
    result: list[str] = []
    for override in codex["config_overrides"]:
        result.extend(["-c", override])
    for feature in codex["disabled_features"]:
        result.extend(["--disable", feature])
    return result


def build_exec_argv(executable: Path, config: dict[str, Any]) -> list[str]:
    validate_config_dict(config)
    codex = config["codex"]
    # ``--ask-for-approval`` is a top-level option in the pinned CLI.  It is
    # accepted before ``exec`` but is rejected by the ``exec`` subcommand when
    # placed after it (the latter yields ``unexpected argument``).  Keep the
    # safety policy explicit while respecting the CLI's option scope.
    argv = [
        os.fspath(executable),
        "--strict-config",
        *_config_arguments(config),
        "--ask-for-approval",
        codex["approval_policy"],
        "exec",
    ]
    argv.extend(
        [
            "--ephemeral",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--json",
            "-o",
            "raw.md",
            "--model",
            codex["model"],
            "--sandbox",
            codex["sandbox"],
            "-",
        ]
    )
    if "--ignore-user-config" in argv:
        raise RunnerError("--ignore-user-config is forbidden")
    return argv


def _process_bytes(value: Any, context: str) -> bytes:
    if value is None:
        return b""
    if not isinstance(value, bytes):
        raise RunnerError(f"{context} was not captured as bytes")
    if len(value) > MAX_CAPTURED_STREAM_BYTES:
        raise RunnerError(
            f"{context} exceeds the {MAX_CAPTURED_STREAM_BYTES} byte limit"
        )
    return value


def _run_process(
    process_runner: Callable[..., Any],
    argv: list[str],
    *,
    cwd: Path,
    timeout: int,
    input_bytes: bytes | None = None,
) -> Any:
    kwargs: dict[str, Any] = {
        "cwd": os.fspath(cwd),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": False,
        "check": False,
        "timeout": timeout,
    }
    if input_bytes is not None:
        kwargs["input"] = input_bytes
    return process_runner(argv, **kwargs)


def _artifact_record(data: bytes) -> dict[str, Any]:
    return {"length": len(data), "sha256": _sha256(data)}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_timestamp(value: datetime) -> str:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise RunnerError("UTC clock must return a timezone-aware datetime")
    rendered = value.astimezone(timezone.utc).isoformat()
    if rendered.endswith("+00:00"):
        return rendered[:-6] + "Z"
    raise RunnerError("UTC clock did not format with a zero offset")


def _start_timing(
    record: dict[str, Any],
    *,
    utc_now: Callable[[], datetime],
    monotonic: Callable[[], float],
) -> float:
    record["started_at"] = _utc_timestamp(utc_now())
    return monotonic()


def _finish_timing(
    record: dict[str, Any],
    started_monotonic: float,
    *,
    utc_now: Callable[[], datetime],
    monotonic: Callable[[], float],
) -> None:
    record["finished_at"] = _utc_timestamp(utc_now())
    try:
        duration = float(monotonic() - started_monotonic)
    except (TypeError, ValueError) as exc:
        raise RunnerError("monotonic clock returned a non-numeric value") from exc
    if not math.isfinite(duration) or duration < 0:
        raise RunnerError("monotonic clock returned an invalid duration")
    record["duration_seconds"] = duration


def _validate_feature_output(data: bytes, disabled_features: list[str]) -> None:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RunnerError("features list stdout is not strict UTF-8") from exc
    states: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = FEATURE_LINE_RE.fullmatch(line)
        if match is None:
            raise RunnerError(f"malformed features list line {line_number}: {line!r}")
        name, state = match.groups()
        if name in states:
            raise RunnerError(f"duplicate feature in features list: {name}")
        states[name] = state
    missing = [name for name in disabled_features if name not in states]
    enabled = [name for name in disabled_features if states.get(name) != "false"]
    if missing or enabled:
        raise RunnerError(
            f"disabled feature preflight failed; missing={missing!r}, enabled={enabled!r}"
        )


def run_preflight(
    executable: Path,
    config: dict[str, Any],
    output: Path,
    *,
    process_runner: Callable[..., Any] = subprocess.run,
    expected_executable_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_config_dict(config)
    _mkdir_safe(output, "preflight output")
    common = [os.fspath(executable), *_config_arguments(config)]
    probes = [
        ("version", [common[0], "--strict-config", *common[1:], "--version"]),
        ("features", [*common, "features", "list"]),
        ("mcp", [*common, "mcp", "list", "--json"]),
        ("plugin", [*common, "plugin", "list", "--json"]),
    ]
    captured: dict[str, dict[str, Any]] = {}
    raw_outputs: dict[str, bytes] = {}
    for name, argv in probes:
        if "--ignore-user-config" in argv:
            raise RunnerError("--ignore-user-config is forbidden")
        if expected_executable_identity is not None:
            executable_before = verify_executable_identity(
                executable, config, expected_executable_identity
            )
        else:
            executable_before = None
        process_error: Exception | None = None
        result: Any = None
        stdout = b""
        stderr = b""
        try:
            result = _run_process(process_runner, argv, cwd=output.parent, timeout=120)
            stdout = _process_bytes(result.stdout, f"{name} stdout")
            stderr = _process_bytes(result.stderr, f"{name} stderr")
        except Exception as exc:
            process_error = exc
            stdout = _process_bytes(getattr(exc, "stdout", None), f"{name} stdout")
            stderr = _process_bytes(getattr(exc, "stderr", None), f"{name} stderr")
        finally:
            _safe_write_bytes(
                output / f"{name}.stdout.bin", stdout, f"{name} stdout artifact"
            )
            _safe_write_bytes(
                output / f"{name}.stderr.bin", stderr, f"{name} stderr artifact"
            )
            if expected_executable_identity is not None:
                executable_after = verify_executable_identity(
                    executable, config, expected_executable_identity
                )
            else:
                executable_after = None
        if process_error is not None:
            if isinstance(process_error, subprocess.TimeoutExpired):
                raise RunnerError(f"Codex {name} preflight timed out") from process_error
            raise RunnerError(f"Codex {name} preflight launch failed: {process_error}") from process_error
        captured[name] = {
            "argv": argv,
            "returncode": result.returncode,
            "stdout": _artifact_record(stdout),
            "stderr": _artifact_record(stderr),
            "executable_before": executable_before,
            "executable_after": executable_after,
            "strict_config_applied": name == "version",
        }
        if name != "version":
            captured[name]["strict_config_compatibility"] = (
                "pinned CLI subcommand does not support --strict-config"
            )
        raw_outputs[name] = stdout
        if result.returncode != 0:
            raise RunnerError(f"Codex {name} preflight exited {result.returncode}")

    expected_version = config["codex"]["expected_version"]
    expected_bytes = expected_version.encode("utf-8")
    if raw_outputs["version"] not in {
        expected_bytes,
        expected_bytes + b"\n",
        expected_bytes + b"\r\n",
    }:
        raise RunnerError(
            f"Codex version mismatch: expected exactly {expected_version!r} with at "
            "most one platform line ending"
        )
    version = expected_version
    _validate_feature_output(
        raw_outputs["features"], config["codex"]["disabled_features"]
    )
    mcp = _decode_json(raw_outputs["mcp"], "mcp list stdout")
    if mcp != []:
        raise RunnerError("mcp list must be exactly an empty array")
    plugins = _decode_json(raw_outputs["plugin"], "plugin list stdout")
    plugins = _expect_keys(plugins, {"installed", "available"}, "plugin list")
    if plugins["installed"] != [] or plugins["available"] != []:
        raise RunnerError("plugin installed and available lists must both be empty")
    formal_exec_argv = build_exec_argv(executable, config)
    formal_exec_strict_config = (
        formal_exec_argv.count("--strict-config") == 1
        and formal_exec_argv[1] == "--strict-config"
    )
    if not formal_exec_strict_config:
        raise RunnerError("formal Codex exec argv is not globally strict")
    return {
        "version": version,
        "probes": captured,
        "formal_exec_strict_config": formal_exec_strict_config,
    }


def _mode_string(status: os.stat_result) -> str:
    return f"0o{stat.S_IMODE(status.st_mode):03o}"


def _snapshot_file(path: Path, relative: str) -> dict[str, Any]:
    data = _stable_read(path, f"model-root file {relative}")
    status = path.stat(follow_symlinks=False)
    return {
        "path": relative,
        "type": "file",
        "mode": _mode_string(status),
        "length": len(data),
        "sha256": _sha256(data),
    }


def _scan_skill_tree(skill_root: Path) -> tuple[set[str], set[str]]:
    files: set[str] = set()
    directories: set[str] = set()

    def visit(directory: Path, prefix: str) -> None:
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise RunnerError(f"cannot scan model-root Skill directory: {exc}") from exc
        folded: set[str] = set()
        for entry in entries:
            if entry.name.casefold() in folded:
                raise RunnerError(f"case-colliding model-root entry: {entry.name}")
            folded.add(entry.name.casefold())
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            path = Path(entry.path)
            if _is_linklike(path):
                raise RunnerError(f"linked model-root Skill entry: {relative}")
            try:
                status = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise RunnerError(f"cannot stat model-root Skill entry {relative}: {exc}") from exc
            if stat.S_ISDIR(status.st_mode):
                directories.add(relative)
                visit(path, relative)
            elif stat.S_ISREG(status.st_mode):
                files.add(relative)
            else:
                raise RunnerError(f"non-ordinary model-root Skill entry: {relative}")

    visit(skill_root, "")
    return files, directories


def snapshot_model_root(model_root: Path, skill_files: list[str]) -> dict[str, Any]:
    model_root = _absolute(Path(model_root))
    if _is_linklike(model_root) or not model_root.is_dir():
        raise RunnerError("model-root must be an ordinary directory")
    for index, relative in enumerate(skill_files):
        validate_relative_path(relative, f"skill_files[{index}]")
    if len(skill_files) != len(set(path.casefold() for path in skill_files)):
        raise RunnerError("Skill file paths collide")

    try:
        root_items = list(os.scandir(model_root))
    except OSError as exc:
        raise RunnerError(f"cannot scan model-root: {exc}") from exc
    root_names = [entry.name for entry in root_items]
    if len(root_names) != len(set(name.casefold() for name in root_names)):
        raise RunnerError("case-colliding model-root entries")
    if set(root_names) != set(EXPECTED_ROOT_ENTRIES):
        raise RunnerError(
            f"model-root inventory mismatch: expected={EXPECTED_ROOT_ENTRIES!r}, "
            f"actual={sorted(root_names)!r}"
        )
    for entry in root_items:
        if _is_linklike(Path(entry.path)):
            raise RunnerError(f"linked model-root entry: {entry.name}")

    skill_root = model_root / "research-writing"
    if not skill_root.is_dir():
        raise RunnerError("research-writing must be an ordinary directory")
    actual_files, actual_directories = _scan_skill_tree(skill_root)
    expected_files = set(skill_files)
    expected_directories: set[str] = set()
    for relative in skill_files:
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    if actual_files != expected_files or actual_directories != expected_directories:
        raise RunnerError(
            "model-root Skill inventory mismatch; "
            f"missing={sorted(expected_files - actual_files)!r}, "
            f"extra={sorted(actual_files - expected_files)!r}, "
            f"directory_extra={sorted(actual_directories - expected_directories)!r}"
        )

    entries: dict[str, dict[str, Any]] = {}
    for relative in skill_files:
        mounted = f"research-writing/{relative}"
        entries[mounted] = _snapshot_file(
            skill_root.joinpath(*PurePosixPath(relative).parts), mounted
        )
    for name in ("case.md", "raw.md"):
        path = model_root / name
        if _is_linklike(path) or not path.is_file():
            raise RunnerError(f"{name} must be an ordinary model-root file")
        entries[name] = _snapshot_file(path, name)
    return {
        "root_entries": sorted(root_names),
        "skill_directories": sorted(actual_directories),
        "entries": entries,
    }


def diagnostic_model_root_snapshot(model_root: Path) -> dict[str, Any]:
    model_root = _absolute(model_root)
    result: dict[str, Any] = {
        "root_entries": [],
        "tree_entries": [],
        "diagnostic_only": True,
    }
    if not os.path.lexists(model_root):
        result["root_state"] = "missing"
        return result
    linked_components = [
        os.fspath(component)
        for component in _existing_components(model_root)
        if _is_linklike(component)
    ]
    if linked_components:
        result["root_state"] = "link-or-reparse"
        result["linked_components"] = linked_components
        return result
    try:
        root_status = model_root.stat(follow_symlinks=False)
    except OSError as exc:
        result["root_state"] = "unreadable"
        result["diagnostic_error"] = f"{type(exc).__name__}: {exc}"
        return result
    if not stat.S_ISDIR(root_status.st_mode):
        result["root_state"] = "non-directory"
        result["root_mode"] = _mode_string(root_status)
        return result
    result["root_state"] = "directory"

    def visit(directory: Path, prefix: str, recurse: bool) -> None:
        for entry in sorted(os.scandir(directory), key=lambda value: value.name.casefold()):
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            if not prefix:
                result["root_entries"].append(entry.name)
            path = Path(entry.path)
            try:
                status = entry.stat(follow_symlinks=False)
                record: dict[str, Any] = {
                    "path": relative,
                    "mode": _mode_string(status),
                }
                if _is_linklike(path):
                    record["type"] = "link-or-reparse"
                elif stat.S_ISDIR(status.st_mode):
                    record["type"] = "directory"
                    if recurse or relative == "research-writing":
                        visit(path, relative, True)
                elif stat.S_ISREG(status.st_mode):
                    record["type"] = "file"
                    data = _stable_read(path, f"diagnostic model-root file {relative}")
                    record["length"] = len(data)
                    record["sha256"] = _sha256(data)
                else:
                    record["type"] = "special"
                result["tree_entries"].append(record)
            except Exception as exc:
                result["tree_entries"].append(
                    {
                        "path": relative,
                        "type": "unreadable",
                        "diagnostic": f"{type(exc).__name__}: {exc}",
                    }
                )

    visit(model_root, "", False)
    result["root_entries"].sort(key=str.casefold)
    result["tree_entries"].sort(key=lambda value: value["path"].casefold())
    return result


def directory_identity(path: Path, context: str) -> dict[str, Any]:
    path = _absolute(path)
    _reject_linklike_components(path, context)
    try:
        status = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise RunnerError(f"cannot stat {context}: {path}: {exc}") from exc
    if not stat.S_ISDIR(status.st_mode):
        raise RunnerError(f"{context} is not an ordinary directory: {path}")
    return {
        "resolved_path": os.fspath(path.resolve(strict=True)),
        "device": status.st_dev,
        "inode": status.st_ino,
        "mode": status.st_mode,
    }


def assert_unchanged_inputs(before: dict[str, Any], after: dict[str, Any]) -> None:
    before_entries = {
        key: value for key, value in before["entries"].items() if key != "raw.md"
    }
    after_entries = {
        key: value for key, value in after["entries"].items() if key != "raw.md"
    }
    if (
        before["root_entries"] != after["root_entries"]
        or before["skill_directories"] != after["skill_directories"]
        or before_entries != after_entries
    ):
        raise RunnerError("model-root Skill inputs or case.md changed during execution")


def _tokenize_command(command: str) -> list[str]:
    if not command or command != command.strip():
        raise RunnerError("command_execution command is empty or not canonical")
    if any(character in command for character in "\r\n|&;<>`$%*?(){}"):
        raise RunnerError("command_execution uses expansion, operators, or metacharacters")
    tokens: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for character in command:
        if quote is not None:
            if character == quote:
                quote = None
            else:
                current.append(character)
        elif character in ("'", '"'):
            quote = character
        elif character.isspace():
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(character)
    if quote is not None:
        raise RunnerError("command_execution has an unterminated quote")
    if current:
        tokens.append("".join(current))
    if not tokens:
        raise RunnerError("command_execution command is empty")
    return tokens


def _command_path(tokens: list[str], _wrapper_depth: int = 0) -> str:
    if not tokens:
        raise RunnerError("command_execution command is empty")
    lowered = [token.casefold() for token in tokens]
    # The Windows Codex client may report the read command through a fixed
    # PowerShell wrapper.  Normalize only this exact executable and the two
    # option layouts observed in the audit stream; every other shell form
    # remains outside the intentionally tiny read-only grammar.  The payload
    # is tokenized again so operators, expansion, and extra commands cannot be
    # hidden inside the wrapper's quoted argument.
    if lowered[0] == WINDOWS_POWERSHELL_EXECUTABLE.casefold():
        if _wrapper_depth:
            raise RunnerError("nested PowerShell command wrappers are not allowed")
        if len(tokens) == 3 and lowered[1] == "-command":
            payload = tokens[2]
        elif (
            len(tokens) == 4
            and lowered[1] == "-noprofile"
            and lowered[2] == "-command"
        ):
            payload = tokens[3]
        else:
            raise RunnerError("PowerShell wrapper options are not allowed")
        return _command_path(_tokenize_command(payload), _wrapper_depth + 1)
    if lowered[0] == "get-content":
        path: str | None = None
        index = 1
        while index < len(tokens):
            option = lowered[index]
            if option == "-raw":
                index += 1
            elif option == "-literalpath":
                if path is not None or index + 1 >= len(tokens):
                    raise RunnerError("Get-Content requires one -LiteralPath")
                path = tokens[index + 1]
                index += 2
            elif option in ("-encoding", "-totalcount", "-readcount"):
                if index + 1 >= len(tokens):
                    raise RunnerError(f"Get-Content option {tokens[index]} needs a value")
                value = tokens[index + 1]
                if option == "-encoding" and value.casefold() not in {
                    "utf8",
                    "utf8bom",
                    "utf8nobom",
                }:
                    raise RunnerError("Get-Content encoding is not allowed")
                if option != "-encoding" and not value.isdecimal():
                    raise RunnerError("Get-Content count must be decimal")
                index += 2
            else:
                raise RunnerError(f"Get-Content option is not allowed: {tokens[index]}")
        if path is None:
            raise RunnerError("Get-Content requires exactly one -LiteralPath")
        return path
    if lowered[:4] == ["cmd", "/d", "/c", "type"] and len(tokens) == 5:
        return tokens[4]
    raise RunnerError("command_execution is not in the small read-only command grammar")


def audit_read_command(command: str, model_root: Path) -> str:
    if not isinstance(command, str):
        raise RunnerError("command_execution.command must be a string")
    command.encode("utf-8", errors="strict")
    raw_path = _command_path(_tokenize_command(command))
    windows = PureWindowsPath(raw_path)
    posix = PurePosixPath(raw_path.replace("\\", "/"))
    if windows.is_absolute() or windows.drive or windows.root or posix.is_absolute():
        raise RunnerError("command_execution path must be relative")
    normalized = posix.as_posix()
    validate_relative_path(normalized, "command_execution path")
    if normalized != "case.md" and not normalized.startswith("research-writing/"):
        raise RunnerError("command_execution may read only case.md or research-writing/**")
    model_root = _absolute(model_root)
    target = model_root.joinpath(*posix.parts)
    _reject_linklike_components(target, "command_execution path")
    try:
        resolved = target.resolve(strict=True)
    except OSError as exc:
        raise RunnerError(f"command_execution target does not exist: {normalized}") from exc
    if not _contains(model_root.resolve(strict=True), resolved):
        raise RunnerError("command_execution target escapes model-root")
    if not resolved.is_file():
        raise RunnerError("command_execution target must be one ordinary file")
    return normalized


def parse_and_audit_events(
    data: bytes, raw_bytes: bytes, model_root: Path, config: dict[str, Any]
) -> dict[str, Any]:
    validate_config_dict(config)
    try:
        text = data.decode("utf-8", errors="strict")
        raw_text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RunnerError("events.jsonl and raw.md must be strict UTF-8") from exc
    if not text:
        raise RunnerError("events.jsonl is empty")
    lines = text.splitlines()
    if not lines or any(not line for line in lines):
        raise RunnerError("events.jsonl contains an empty line")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        event = _decode_json(line.encode("utf-8"), f"events.jsonl line {line_number}")
        if not isinstance(event, dict):
            raise RunnerError(f"events.jsonl line {line_number} is not an object")
        events.append(event)

    allowed_events = set(config["audit"]["allowed_event_types"])
    allowed_items = set(config["audit"]["allowed_item_types"])
    forbidden_items = set(config["audit"]["forbidden_item_types"])
    thread_started = 0
    turn_started = 0
    turn_completed = 0
    item_states: dict[str, dict[str, Any]] = {}
    completed_messages: list[str] = []
    command_records: list[dict[str, Any]] = []

    for index, event in enumerate(events):
        event_type = event.get("type")
        # JSON permits any scalar/container here, but lifecycle dispatch must
        # fail closed with a domain error instead of attempting set membership
        # on an unhashable list/dict (which would leak a bare TypeError).
        if not isinstance(event_type, str):
            raise RunnerError(
                f"events.jsonl event type must be a string (line {index + 1})"
            )
        if event_type in {"error", "turn.failed"}:
            raise RunnerError(f"failure event is forbidden: {event_type}")
        if event_type not in allowed_events:
            raise RunnerError(f"unknown or forbidden lifecycle event: {event_type!r}")
        event_fields = (
            {"type", "thread_id"}
            if event_type == "thread.started"
            else {"type", "usage"}
            if event_type == "turn.completed"
            else {"type"}
            if event_type == "turn.started"
            else {"type", "item"}
        )
        unknown_event_fields = set(event) - event_fields
        if unknown_event_fields:
            raise RunnerError(
                f"unknown fields on {event_type}: {sorted(unknown_event_fields)!r}"
            )
        if event_type == "thread.started":
            thread_started += 1
            if index != 0 or thread_started != 1:
                raise RunnerError("thread.started must occur exactly once at the start")
            thread_id = event.get("thread_id")
            if not isinstance(thread_id, str) or not thread_id:
                raise RunnerError("thread.started requires a non-empty thread_id")
            continue
        if event_type == "turn.started":
            turn_started += 1
            if thread_started != 1 or turn_started != 1 or turn_completed:
                raise RunnerError("turn.started is missing, duplicated, or out of order")
            continue
        if event_type == "turn.completed":
            turn_completed += 1
            if turn_started != 1 or turn_completed != 1 or index != len(events) - 1:
                raise RunnerError("turn.completed must be the unique terminal event")
            if "usage" in event and not isinstance(event["usage"], dict):
                raise RunnerError("turn.completed usage must be an object when present")
            continue
        if thread_started != 1 or turn_started != 1 or turn_completed:
            raise RunnerError("item lifecycle event is out of order")

        item = event.get("item")
        if not isinstance(item, dict):
            raise RunnerError(f"{event_type} requires an item object")
        item_type = item.get("type")
        if not isinstance(item_type, str):
            raise RunnerError(
                f"{event_type}.item.type must be a string when present"
            )
        if item_type in forbidden_items:
            raise RunnerError(f"forbidden item type: {item_type}")
        if item_type not in allowed_items:
            raise RunnerError(f"unknown item type: {item_type!r}")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise RunnerError("every allowed item requires a non-empty string id")
        allowed_item_fields = (
            {"id", "type", "text"}
            if item_type in {"reasoning", "agent_message"}
            else {
                "id",
                "type",
                "command",
                "aggregated_output",
                "exit_code",
                "status",
            }
        )
        unknown_item_fields = set(item) - allowed_item_fields
        if unknown_item_fields:
            raise RunnerError(
                f"unknown fields on {item_type}: {sorted(unknown_item_fields)!r}"
            )
        if item_type in {"reasoning", "agent_message"} and "text" in item:
            if not isinstance(item["text"], str):
                raise RunnerError(f"{item_type}.text must be a string when present")

        command = item.get("command") if item_type == "command_execution" else None
        if item_type == "command_execution":
            audit_read_command(command, model_root)
        state = item_states.get(item_id)
        if event_type == "item.started":
            if state is not None:
                raise RunnerError(f"duplicate item start or reused item id: {item_id}")
            item_states[item_id] = {
                "type": item_type,
                "command": command,
                "active": True,
            }
        elif event_type == "item.updated":
            if state is None or not state["active"]:
                raise RunnerError(f"item.updated has no active start: {item_id}")
            if state["type"] != item_type or state["command"] != command:
                raise RunnerError(f"item identity changed during update: {item_id}")
        else:
            if state is None:
                if item_type == "command_execution":
                    raise RunnerError(
                        "command_execution completion requires a matching started item"
                    )
                item_states[item_id] = {
                    "type": item_type,
                    "command": command,
                    "active": False,
                }
            else:
                if not state["active"]:
                    raise RunnerError(f"duplicate item terminal: {item_id}")
                if state["type"] != item_type or state["command"] != command:
                    raise RunnerError(f"item identity changed before completion: {item_id}")
                state["active"] = False

        if item_type == "command_execution":
            normalized_path = audit_read_command(command, model_root)
            if event_type == "item.completed":
                if item.get("status") != "completed":
                    raise RunnerError("completed command_execution status must be completed")
                exit_code = item.get("exit_code")
                if isinstance(exit_code, bool) or not isinstance(exit_code, int):
                    raise RunnerError("completed command_execution exit_code must be an integer")
                if exit_code != 0:
                    raise RunnerError(f"command_execution exited nonzero: {exit_code}")
                output = item.get("aggregated_output")
                if not isinstance(output, str):
                    raise RunnerError(
                        "completed command_execution aggregated_output must be a string"
                    )
                output_bytes = output.encode("utf-8", errors="strict")
                command_records.append(
                    {
                        "command": command,
                        "path": normalized_path,
                        "exit_code": exit_code,
                        "output_length": len(output_bytes),
                        "output_sha256": _sha256(output_bytes),
                    }
                )
        elif item_type == "agent_message" and event_type == "item.completed":
            message = item.get("text")
            if not isinstance(message, str):
                raise RunnerError("completed agent_message.text must be a string")
            message.encode("utf-8", errors="strict")
            completed_messages.append(message)

    if thread_started != 1 or turn_started != 1 or turn_completed != 1:
        raise RunnerError("events.jsonl is missing a unique successful terminal sequence")
    active_items = sorted(
        item_id for item_id, state in item_states.items() if state["active"]
    )
    if active_items:
        raise RunnerError(f"started items are missing terminal events: {active_items!r}")
    if not completed_messages:
        raise RunnerError("events.jsonl has no completed agent_message")
    final_bytes = completed_messages[-1].encode("utf-8", errors="strict")
    if final_bytes != raw_bytes or completed_messages[-1] != raw_text:
        raise RunnerError(
            "last completed agent_message does not match raw.md bytes exactly"
        )
    return {
        "audit_scope": AUDIT_SCOPE,
        "user_config_loaded": True,
        "runtime_file_read_attestation": False,
        "event_count": len(events),
        "command_count": len(command_records),
        "commands": command_records,
        "final_message_length": len(final_bytes),
        "final_message_sha256": _sha256(final_bytes),
        "raw_length": len(raw_bytes),
        "raw_sha256": _sha256(raw_bytes),
    }


def _temporary_identity(path: Path, context: str) -> tuple[int, int, int, int, int]:
    """Return identity fields for a temporary regular file."""

    if _is_linklike(path):
        raise RunnerError(f"{context} must not be a link or reparse point: {path}")
    try:
        status = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise RunnerError(f"cannot stat {context}: {path}: {exc}") from exc
    if not stat.S_ISREG(status.st_mode):
        raise RunnerError(f"{context} is not an ordinary file: {path}")
    return (
        int(getattr(status, "st_dev", 0)),
        int(getattr(status, "st_ino", 0)),
        int(stat.S_IFMT(status.st_mode)),
        int(status.st_size),
        int(getattr(status, "st_nlink", 1)),
    )


def _set_temporary_mode(path: Path, mode: int, context: str) -> None:
    """Set mode on our private temporary pathname before replacement.

    Platforms exposing no-follow chmod use it directly. Windows Python does
    not expose a no-follow chmod primitive, so the fallback verifies the
    freshly-created temporary entry immediately before and after chmod. This
    leaves only the unavoidable pathname race on platforms without that API.
    """

    if isinstance(mode, bool) or not isinstance(mode, int):
        raise RunnerError(f"{context} mode must be an integer")
    before = _temporary_identity(path, context)
    try:
        os.chmod(path, mode, follow_symlinks=False)
    except (NotImplementedError, TypeError):
        # Windows and a few Python/platform combinations do not implement
        # follow_symlinks for chmod. The target is still our private mkstemp
        # entry, and identity checks prevent silently continuing after a
        # concurrent replacement.
        try:
            os.chmod(path, mode)
        except OSError as exc:
            raise RunnerError(f"cannot set {context} mode: {path}: {exc}") from exc
    except OSError as exc:
        raise RunnerError(f"cannot set {context} mode: {path}: {exc}") from exc
    after = _temporary_identity(path, context)
    if before != after:
        raise RunnerError(f"{context} identity changed while setting mode: {path}")


def _safe_write_bytes(
    path: Path, payload: bytes, context: str, *, mode: int | None = None
) -> None:
    path = _absolute(path)
    parent = path.parent
    # Build missing ancestors one component at a time. In particular, avoid
    # recursive Path.mkdir: it can follow a substituted link ancestor.
    parent_before = _ensure_directory_tree(parent, f"{context} parent")
    _assert_directory_chain_unchanged(parent, parent_before, f"{context} parent")

    # Existing files (including symlinks and hard links) are replaced by the
    # fully-written temporary file below. os.replace operates on the directory
    # entry, so it does not write through a link or mutate another hard-link
    # name. Refuse an existing directory, for which replacement is
    # platform-dependent and could leave an unexpected tree behind.
    try:
        target_exists = os.path.lexists(path)
    except OSError as exc:
        raise RunnerError(f"cannot inspect {context} target: {path}: {exc}") from exc
    if target_exists:
        try:
            target_status = path.stat(follow_symlinks=False)
        except OSError as exc:
            raise RunnerError(f"cannot inspect {context} target: {path}: {exc}") from exc
        if stat.S_ISDIR(target_status.st_mode):
            raise RunnerError(f"{context} target must not be a directory: {path}")

    try:
        descriptor, raw_temporary = tempfile.mkstemp(
            dir=parent, prefix=f".{path.name}.", suffix=".tmp"
        )
    except OSError as exc:
        raise RunnerError(f"cannot create temporary {context}: {exc}") from exc
    temporary = Path(raw_temporary)
    try:
        # Revalidate immediately after mkstemp: a parent swap can otherwise
        # make the temporary pathname refer to a different tree.
        _assert_directory_chain_unchanged(parent, parent_before, f"{context} parent")
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            _set_temporary_mode(temporary, mode, f"temporary {context}")
        temporary_identity = _temporary_identity(temporary, f"temporary {context}")
        if temporary_identity[-1] != 1:
            raise RunnerError(
                f"temporary {context} has multiple hard links: {temporary}"
            )
        _assert_directory_chain_unchanged(parent, parent_before, f"{context} parent")
        os.replace(temporary, path)
        # Detect replacement of an ancestor during os.replace. If this check
        # fails, the operation is reported as failed even though the old tree
        # may already contain the completed replacement.
        _assert_directory_chain_unchanged(parent, parent_before, f"{context} parent")
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        # Do not unlink through a potentially swapped parent. Leaving a private
        # temporary behind is safer than deleting an attacker-controlled path.
        try:
            _assert_directory_chain_unchanged(parent, parent_before, f"{context} parent")
            temporary.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _write_json_atomic(path: Path, value: Any) -> None:
    payload = (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _safe_write_bytes(path, payload, "JSON artifact")


def _validate_exact_directory(
    directory: Path,
    *,
    expected_files: set[str],
    expected_directories: set[str],
    context: str,
) -> None:
    expected_names = expected_files | expected_directories
    if expected_files & expected_directories:
        raise RunnerError(f"{context} expected inventory has conflicting types")
    if len(expected_names) != len({name.casefold() for name in expected_names}):
        raise RunnerError(f"{context} expected inventory has case-colliding names")

    identity_before = directory_identity(directory, context)
    try:
        entries = list(os.scandir(directory))
    except OSError as exc:
        raise RunnerError(f"cannot scan {context}: {exc}") from exc
    names = [entry.name for entry in entries]
    if len(names) != len({name.casefold() for name in names}):
        raise RunnerError(f"case-colliding entries in {context}")
    actual_names = set(names)
    if actual_names != expected_names:
        raise RunnerError(
            f"{context} inventory mismatch: "
            f"missing={sorted(expected_names - actual_names)!r}, "
            f"extra={sorted(actual_names - expected_names)!r}"
        )

    for entry in entries:
        path = Path(entry.path)
        if _is_linklike(path):
            raise RunnerError(f"linked entry in {context}: {entry.name}")
        try:
            status = entry.stat(follow_symlinks=False)
        except OSError as exc:
            raise RunnerError(
                f"cannot stat {context} entry {entry.name}: {exc}"
            ) from exc
        if entry.name in expected_files and not stat.S_ISREG(status.st_mode):
            raise RunnerError(
                f"{context} entry must be an ordinary file: {entry.name}"
            )
        if entry.name in expected_directories and not stat.S_ISDIR(status.st_mode):
            raise RunnerError(
                f"{context} entry must be an ordinary directory: {entry.name}"
            )
    if directory_identity(directory, context) != identity_before:
        raise RunnerError(f"{context} identity changed while validating inventory")


def validate_run_artifact_inventory(output: Path, case_ids: list[str]) -> None:
    for index, case_id in enumerate(case_ids):
        if not isinstance(case_id, str) or CASE_ID_RE.fullmatch(case_id) is None:
            raise RunnerError(
                f"run artifact case ID at index {index} is not canonical: {case_id!r}"
            )
    if len(case_ids) != len(set(case_ids)):
        raise RunnerError("run artifact case IDs are not unique")
    _validate_exact_directory(
        output,
        expected_files={"manifest.json"},
        expected_directories={"preflight", "cases"},
        context="run output",
    )
    preflight_files = {
        f"{probe}.{stream}.bin"
        for probe in ("version", "features", "mcp", "plugin")
        for stream in ("stdout", "stderr")
    }
    _validate_exact_directory(
        output / "preflight",
        expected_files=preflight_files,
        expected_directories=set(),
        context="preflight artifacts",
    )
    _validate_exact_directory(
        output / "cases",
        expected_files=set(),
        expected_directories=set(case_ids),
        context="case artifacts",
    )
    for case_id in case_ids:
        _validate_exact_directory(
            output / "cases" / case_id,
            expected_files={"prompt.bin", "events.jsonl", "stderr.bin", "audit.json"},
            expected_directories={"model-root"},
            context=f"case {case_id} artifacts",
        )


def _artifact_inventory_paths(output: Path, case_ids: list[str]) -> list[Path]:
    paths: list[Path] = []
    for probe in ("version", "features", "mcp", "plugin"):
        for stream in ("stdout", "stderr"):
            paths.append(output / "preflight" / f"{probe}.{stream}.bin")
    for case_id in case_ids:
        case_root = output / "cases" / case_id
        paths.extend(
            [
                case_root / "prompt.bin",
                case_root / "events.jsonl",
                case_root / "stderr.bin",
                case_root / "audit.json",
                case_root / "model-root" / "raw.md",
            ]
        )
    return paths


def capture_artifact_inventory(output: Path, case_ids: list[str]) -> dict[str, dict[str, Any]]:
    validate_run_artifact_inventory(output, case_ids)
    inventory: dict[str, dict[str, Any]] = {}
    root = _absolute(output)
    for path in _artifact_inventory_paths(root, case_ids):
        relative = path.relative_to(root).as_posix()
        data = _stable_read(path, f"artifact {relative}")
        status = path.stat(follow_symlinks=False)
        if status.st_nlink > 1:
            raise RunnerError(f"artifact {relative} has multiple hard links")
        inventory[relative] = _artifact_record(data)
    return inventory


def verify_artifact_inventory(
    output: Path, case_ids: list[str], expected: dict[str, dict[str, Any]]
) -> None:
    actual = capture_artifact_inventory(output, case_ids)
    if actual != expected:
        raise RunnerError("artifact content changed after capture")


def _public_frozen(frozen: dict[str, Any]) -> dict[str, Any]:
    return {
        "commit_argument": frozen["commit_argument"],
        "commit": frozen["commit"],
        "root_tree": frozen["root_tree"],
        "skill_tree": frozen["skill_tree"],
        "cases_tree": frozen["cases_tree"],
        "files": [
            {key: value for key, value in record.items() if key != "data"}
            for record in frozen["files"].values()
        ],
    }


def _materialized_mode(git_mode: str) -> int:
    validate_git_blob_mode(git_mode, "materialized input")
    return 0o755 if git_mode == "100755" else 0o644


def _write_model_input(root: Path, relative: str, record: dict[str, Any]) -> None:
    validate_relative_path(relative, "materialized path")
    target = root.joinpath(*PurePosixPath(relative).parts)
    if not _contains(root, _absolute(target)):
        raise RunnerError(f"materialized path escapes model-root: {relative}")
    if os.path.lexists(target):
        raise RunnerError(f"materialized path already exists: {relative}")
    _safe_write_bytes(
        target,
        record["data"],
        f"materialized input {relative}",
        mode=_materialized_mode(record["mode"]),
    )


def materialize_model_root(
    model_root: Path,
    frozen: dict[str, Any],
    case: dict[str, str],
) -> None:
    config = frozen["config"]
    source = config["source"]
    _mkdir_safe(model_root, "model-root")
    mount = source["skill_mount_dir"]
    planned = [
        f"{mount}/{relative}" for relative in source["skill_files"]
    ] + ["case.md", "raw.md"]
    if len(planned) != len(set(path.casefold() for path in planned)):
        raise RunnerError("materialized paths have a case-insensitive conflict")
    for relative in source["skill_files"]:
        source_path = f"{source['skill_source_dir']}/{relative}"
        _write_model_input(
            model_root,
            f"{mount}/{relative}",
            frozen["files"][source_path],
        )
    _write_model_input(model_root, "case.md", frozen["files"][case["path"]])
    raw = model_root / "raw.md"
    _safe_write_bytes(raw, b"", "raw.md", mode=0o644)


def render_prompt(wrapper_bytes: bytes, case_id: str, skill_mount_dir: str) -> bytes:
    try:
        wrapper = wrapper_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RunnerError("prompt wrapper is not strict UTF-8") from exc
    replacements = {
        "{{CASE_ID}}": case_id,
        "{{SKILL_MOUNT_DIR}}": skill_mount_dir,
        "{{CASE_FILE}}": "case.md",
    }
    for marker in ("{{CASE_ID}}", "{{SKILL_MOUNT_DIR}}"):
        if wrapper.count(marker) != 1:
            raise RunnerError(f"prompt wrapper must contain {marker} exactly once")
    rendered = wrapper
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    if "{{" in rendered or "}}" in rendered:
        raise RunnerError("prompt wrapper contains an unknown template marker")
    return rendered.encode("utf-8", errors="strict")


def _case_failure_audit(
    case_id: str,
    stage: str,
    exc: BaseException,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "failed",
        "case_id": case_id,
        "audit_scope": AUDIT_SCOPE,
        "user_config_loaded": True,
        "runtime_file_read_attestation": False,
        "diagnostic": {
            "stage": stage,
            "error_type": type(exc).__name__,
            "message": str(exc),
        },
    }
    if before is not None:
        result["before_snapshot"] = before
    if after is not None:
        result["after_snapshot"] = after
    return result


def run_evaluations(
    repository: Path,
    commit_argument: str,
    output: Path,
    *,
    process_runner: Callable[..., Any] = subprocess.run,
    runner_path: Path | None = None,
    utc_now: Callable[[], datetime] = _utc_now,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    repository = _absolute(Path(repository))
    commit_argument = validate_commit_argument(commit_argument)
    output = validate_output_path(Path(output), repository)
    _mkdir_safe(output, "created --output")
    _reject_linklike_components(output, "created --output")
    if _is_linklike(output) or not output.is_dir():
        raise RunnerError("created output is not an ordinary directory")
    if _contains(repository.resolve(strict=True), output.resolve(strict=True)):
        raise RunnerError("created output resolved inside the checkout")

    run_started_monotonic = monotonic()
    stage = "initialize"
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "stage": stage,
        "audit_scope": AUDIT_SCOPE,
        "user_config_loaded": True,
        "runtime_file_read_attestation": False,
        "cases": [],
    }
    manifest["started_at"] = _utc_timestamp(utc_now())
    manifest_path = output / "manifest.json"

    try:
        _write_json_atomic(manifest_path, manifest)
        stage = "capture-frozen-inputs"
        manifest["stage"] = stage
        _write_json_atomic(manifest_path, manifest)
        frozen = capture_frozen_inputs(repository, commit_argument, runner_path)
        config = frozen["config"]
        manifest["source"] = _public_frozen(frozen)
        manifest["configuration"] = config
        _write_json_atomic(manifest_path, manifest)

        stage = "resolve-executable-before"
        manifest["stage"] = stage
        executable, executable_before = resolve_executable(
            config["codex"]["executable"],
            expected_length=config["codex"]["executable_length"],
            expected_sha256=config["codex"]["executable_sha256"],
        )
        manifest["codex_executable_before"] = executable_before
        _write_json_atomic(manifest_path, manifest)

        stage = "preflight"
        manifest["stage"] = stage
        preflight = run_preflight(
            executable,
            config,
            output / "preflight",
            process_runner=process_runner,
            expected_executable_identity=executable_before,
        )
        manifest["preflight"] = preflight
        _write_json_atomic(manifest_path, manifest)

        cases_root = output / "cases"
        _mkdir_safe(cases_root, "cases output")
        wrapper = frozen["files"][config["source"]["prompt_wrapper_path"]]["data"]
        argv = build_exec_argv(executable, config)
        for case in config["source"]["cases"]:
            case_id = case["id"]
            case_root = cases_root / case_id
            model_root = case_root / "model-root"
            before: dict[str, Any] | None = None
            after: dict[str, Any] | None = None
            case_manifest: dict[str, Any] = {
                "id": case_id,
                "source_path": case["path"],
                "status": "running",
            }
            case_started_monotonic = _start_timing(
                case_manifest, utc_now=utc_now, monotonic=monotonic
            )
            manifest["cases"].append(case_manifest)
            stage = f"case:{case_id}:materialize"
            manifest["stage"] = stage
            try:
                _mkdir_safe(case_root, f"case {case_id} output")
                _write_json_atomic(manifest_path, manifest)
                materialize_model_root(model_root, frozen, case)
                prompt = render_prompt(
                    wrapper, case_id, config["source"]["skill_mount_dir"]
                )
                _safe_write_bytes(case_root / "prompt.bin", prompt, "prompt artifact")
                before = snapshot_model_root(
                    model_root, config["source"]["skill_files"]
                )
                model_root_before = directory_identity(model_root, "model-root")

                stage = f"case:{case_id}:verify-before"
                manifest["stage"] = stage
                _write_json_atomic(manifest_path, manifest)
                launch_executable_before = verify_executable_identity(
                    executable, config, executable_before
                )
                if directory_identity(model_root, "model-root") != model_root_before:
                    raise RunnerError("model-root identity changed before Codex launch")
                stage = f"case:{case_id}:execute"
                manifest["stage"] = stage
                timed_out: subprocess.TimeoutExpired | None = None
                result: Any = None
                events = b""
                stderr = b""
                try:
                    result = _run_process(
                        process_runner,
                        argv,
                        cwd=model_root,
                        timeout=config["codex"]["case_timeout_seconds"],
                        input_bytes=prompt,
                    )
                    events = _process_bytes(result.stdout, "Codex events stdout")
                    stderr = _process_bytes(result.stderr, "Codex case stderr")
                except subprocess.TimeoutExpired as exc:
                    timed_out = exc
                    events = _process_bytes(
                        getattr(exc, "stdout", None), "timed-out Codex events stdout"
                    )
                    stderr = _process_bytes(
                        getattr(exc, "stderr", None), "timed-out Codex stderr"
                    )
                finally:
                    _safe_write_bytes(
                        case_root / "events.jsonl", events, "events artifact"
                    )
                    _safe_write_bytes(
                        case_root / "stderr.bin", stderr, "stderr artifact"
                    )
                    stage = f"case:{case_id}:verify-after"
                    launch_executable_after = verify_executable_identity(
                        executable, config, executable_before
                    )
                    model_root_after = directory_identity(model_root, "model-root")
                    if model_root_after != model_root_before:
                        raise RunnerError("model-root identity changed across Codex launch")

                stage = f"case:{case_id}:snapshot-after"
                after = snapshot_model_root(
                    model_root, config["source"]["skill_files"]
                )
                assert_unchanged_inputs(before, after)
                if timed_out is not None:
                    raise RunnerError(
                        f"Codex case timed out after "
                        f"{config['codex']['case_timeout_seconds']} seconds"
                    ) from timed_out

                stage = f"case:{case_id}:audit-events"
                raw_bytes = _stable_read(model_root / "raw.md", "raw.md")
                raw_record = _artifact_record(raw_bytes)
                raw_snapshot = after["entries"]["raw.md"]
                if (
                    raw_record["length"] != raw_snapshot["length"]
                    or raw_record["sha256"] != raw_snapshot["sha256"]
                ):
                    raise RunnerError("raw.md changed after the audited after-snapshot")
                event_audit = parse_and_audit_events(
                    events, raw_bytes, model_root, config
                )
                if result.returncode != 0:
                    raise RunnerError(f"Codex case exited nonzero: {result.returncode}")
                audit = {
                    "status": "passed",
                    "case_id": case_id,
                    **event_audit,
                    "returncode": result.returncode,
                    "argv": argv,
                    "cwd": os.fspath(model_root),
                    "prompt": _artifact_record(prompt),
                    "events": _artifact_record(events),
                    "stderr": _artifact_record(stderr),
                    "before_snapshot": before,
                    "after_snapshot": after,
                    "model_root_identity_before": model_root_before,
                    "model_root_identity_after": model_root_after,
                    "executable_identity_before_launch": launch_executable_before,
                    "executable_identity_after_launch": launch_executable_after,
                }
                _write_json_atomic(case_root / "audit.json", audit)
                case_manifest.update(
                    {
                        "status": "passed",
                        "prompt": _artifact_record(prompt),
                        "events": _artifact_record(events),
                        "stderr": _artifact_record(stderr),
                        "raw": _artifact_record(raw_bytes),
                    }
                )
                _finish_timing(
                    case_manifest,
                    case_started_monotonic,
                    utc_now=utc_now,
                    monotonic=monotonic,
                )
                _write_json_atomic(manifest_path, manifest)
            except Exception as exc:
                if after is None:
                    try:
                        after = diagnostic_model_root_snapshot(model_root)
                    except Exception as diagnostic_exc:
                        after = {
                            "diagnostic_only": True,
                            "diagnostic_error": (
                                f"{type(diagnostic_exc).__name__}: {diagnostic_exc}"
                            ),
                        }
                case_manifest["status"] = "failed"
                case_manifest["diagnostic"] = {
                    "stage": stage,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
                _finish_timing(
                    case_manifest,
                    case_started_monotonic,
                    utc_now=utc_now,
                    monotonic=monotonic,
                )
                _write_json_atomic(
                    case_root / "audit.json",
                    _case_failure_audit(case_id, stage, exc, before, after),
                )
                raise

        stage = "resolve-executable-after"
        manifest["stage"] = stage
        executable_after_path, executable_after = resolve_executable(
            config["codex"]["executable"],
            expected_length=config["codex"]["executable_length"],
            expected_sha256=config["codex"]["executable_sha256"],
        )
        manifest["codex_executable_after"] = executable_after
        if executable_after_path != executable or executable_after != executable_before:
            raise RunnerError("Codex executable identity changed during the run")

        stage = "validate-artifact-inventory"
        manifest["stage"] = stage
        validate_run_artifact_inventory(
            output, [case["id"] for case in config["source"]["cases"]]
        )
        case_ids = [case["id"] for case in config["source"]["cases"]]
        artifact_inventory = capture_artifact_inventory(output, case_ids)
        manifest["artifact_inventory"] = artifact_inventory
        _write_json_atomic(manifest_path, manifest)
        verify_artifact_inventory(output, case_ids, artifact_inventory)

        manifest["status"] = "complete"
        manifest["stage"] = "complete"
        _finish_timing(
            manifest,
            run_started_monotonic,
            utc_now=utc_now,
            monotonic=monotonic,
        )
        _write_json_atomic(manifest_path, manifest)
        return manifest
    except Exception as exc:
        executable_integrity: dict[str, Any] | None = None
        if "config" in locals() and "executable_before" in locals():
            try:
                failure_path, failure_identity = resolve_executable(
                    config["codex"]["executable"],
                    expected_length=config["codex"]["executable_length"],
                    expected_sha256=config["codex"]["executable_sha256"],
                )
                matches = (
                    failure_path == executable and failure_identity == executable_before
                )
                executable_integrity = {
                    "status": "passed" if matches else "failed",
                    "observed": failure_identity,
                }
            except Exception as identity_exc:
                executable_integrity = {
                    "status": "failed",
                    "diagnostic": (
                        f"{type(identity_exc).__name__}: {identity_exc}"
                    ),
                }
        if executable_integrity is not None:
            manifest["executable_integrity"] = executable_integrity
        manifest["status"] = "failed"
        manifest["stage"] = stage
        manifest["diagnostic"] = {
            "stage": stage,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
        _finish_timing(
            manifest,
            run_started_monotonic,
            utc_now=utc_now,
            monotonic=monotonic,
        )
        _write_json_atomic(manifest_path, manifest)
        if isinstance(exc, RunnerError):
            raise
        raise RunnerError(f"evaluation run failed during {stage}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the pinned seven-case Codex research-writing evaluation."
    )
    parser.add_argument(
        "--commit",
        required=True,
        help="Full 40- or 64-hex Git object ID that resolves to a commit.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="New, nonexistent output directory outside the checkout.",
    )
    args = parser.parse_args(argv)
    try:
        manifest = run_evaluations(ROOT, args.commit, args.output)
    except (OSError, RunnerError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(args.output / "manifest.json")
    if manifest["status"] != "complete":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
