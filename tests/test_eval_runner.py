from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "run_evals.py"

SKILL_FILES = [
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
CASES = [
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
DISABLED_FEATURES = [
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
CONFIG_OVERRIDES = [
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
FIXED_EXECUTABLE = (
    r"C:\Users\31933\.vscode\extensions\openai.chatgpt-26.803.61601-win32-x64"
    r"\bin\windows-x86_64\codex.exe"
)
FIXED_EXECUTABLE_LENGTH = 293478192
FIXED_EXECUTABLE_SHA256 = (
    "115518500b45188e410a15d3224c2bbc87df6f2209729bf327aaf7808ca9d5a6"
)


class DeterministicClock:
    def __init__(self) -> None:
        self.wall_calls = 0
        self.monotonic_calls = 0

    def utc_now(self) -> datetime:
        value = datetime(2026, 8, 16, tzinfo=timezone.utc) + timedelta(
            seconds=self.wall_calls
        )
        self.wall_calls += 1
        return value

    def monotonic(self) -> float:
        value = float(self.monotonic_calls)
        self.monotonic_calls += 1
        return value


def load_runner():
    spec = importlib.util.spec_from_file_location("run_evals", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_config(executable: str = FIXED_EXECUTABLE) -> dict:
    return {
        "schema_version": 1,
        "source": {
            "runner_path": "tools/run_evals.py",
            "config_path": "evals/runner-config.json",
            "prompt_wrapper_path": "evals/prompt-wrapper.md",
            "rubric_path": "evals/rubric.md",
            "skill_source_dir": "skills/research-writing",
            "skill_mount_dir": "research-writing",
            "skill_files": list(SKILL_FILES),
            "cases": copy.deepcopy(CASES),
        },
        "codex": {
            "executable": executable,
            "executable_length": FIXED_EXECUTABLE_LENGTH,
            "executable_sha256": FIXED_EXECUTABLE_SHA256,
            "expected_version": "codex-cli 0.147.0-alpha.6.5",
            "model": "gpt-5.6-sol",
            "model_provider": "custom",
            "reasoning_effort": "medium",
            "sandbox": "read-only",
            "approval_policy": "never",
            "case_timeout_seconds": 900,
            "fixed_flags": [
                "--strict-config",
                "--ephemeral",
                "--ignore-rules",
                "--skip-git-repo-check",
                "--json",
                "-o",
                "raw.md",
                "-",
            ],
            "disabled_features": list(DISABLED_FEATURES),
            "config_overrides": list(CONFIG_OVERRIDES),
        },
        "audit": {
            "root_entries": ["research-writing", "case.md", "raw.md"],
            "allowed_event_types": [
                "thread.started",
                "turn.started",
                "item.started",
                "item.updated",
                "item.completed",
                "turn.completed",
            ],
            "allowed_item_types": [
                "reasoning",
                "command_execution",
                "agent_message",
            ],
            "forbidden_item_types": [
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
            ],
        },
    }


def git(repository: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )


def write_file(root: Path, relative: str, data: bytes) -> None:
    target = root.joinpath(*relative.split("/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def make_repository(raw: str, config: dict | None = None) -> tuple[Path, str]:
    repository = Path(raw) / "checkout"
    repository.mkdir()
    config = config or make_config()
    write_file(repository, "tools/run_evals.py", MODULE_PATH.read_bytes())
    write_file(
        repository,
        "evals/runner-config.json",
        (json.dumps(config, indent=2) + "\n").encode("utf-8"),
    )
    write_file(
        repository,
        "evals/prompt-wrapper.md",
        (
            "Evaluate {{CASE_ID}}. Read case.md and relative files under "
            "{{SKILL_MOUNT_DIR}} only.\n"
        ).encode("utf-8"),
    )
    write_file(repository, "evals/rubric.md", b"# Rubric\n")
    for relative in SKILL_FILES:
        write_file(
            repository,
            f"skills/research-writing/{relative}",
            f"skill:{relative}\n".encode("utf-8"),
        )
    for case in CASES:
        write_file(
            repository,
            case["path"],
            f"case:{case['id']}\n".encode("utf-8"),
        )
    manifest = [f"skills/research-writing/{relative}" for relative in SKILL_FILES]
    write_file(
        repository,
        "release-manifest.txt",
        ("\n".join(sorted(manifest)) + "\n").encode("utf-8"),
    )
    git(repository, "init", "-q")
    git(repository, "config", "user.email", "eval@example.invalid")
    git(repository, "config", "user.name", "Eval Test")
    git(repository, "config", "core.autocrlf", "false")
    git(repository, "add", "--", "tools", "evals", "skills", "release-manifest.txt")
    git(repository, "commit", "-q", "-m", "fixture")
    commit = git(repository, "rev-parse", "HEAD").stdout.decode("ascii").strip()
    return repository, commit


def complete_events(message: str = "answer\n", command: str | None = None) -> bytes:
    events = [
        {"type": "thread.started", "thread_id": "thread-1"},
        {"type": "turn.started"},
    ]
    if command is not None:
        events.extend(
            [
                {
                    "type": "item.started",
                    "item": {
                        "id": "command-1",
                        "type": "command_execution",
                        "command": command,
                        "status": "in_progress",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "command-1",
                        "type": "command_execution",
                        "command": command,
                        "aggregated_output": "input\n",
                        "exit_code": 0,
                        "status": "completed",
                    },
                },
            ]
        )
    events.extend(
        [
            {
                "type": "item.completed",
                "item": {
                    "id": "message-1",
                    "type": "agent_message",
                    "text": message,
                },
            },
            {"type": "turn.completed", "usage": {}},
        ]
    )
    return b"".join(
        json.dumps(event, separators=(",", ":")).encode("utf-8") + b"\n"
        for event in events
    )


class FakeCodex:
    def __init__(self, config: dict, mode: str = "ok") -> None:
        self.config = config
        self.mode = mode
        self.calls: list[dict] = []
        self.protected_artifacts: list[Path] = []

    def __call__(self, argv, **kwargs):
        argv = [os.fspath(value) for value in argv]
        self.calls.append({"argv": argv, **kwargs})
        if "--version" in argv:
            return subprocess.CompletedProcess(
                argv,
                0,
                (self.config["codex"]["expected_version"] + "\n").encode(),
                b"",
            )
        if argv[-2:] == ["features", "list"]:
            stdout = "".join(
                f"{name:<36} stable             false\n"
                for name in self.config["codex"]["disabled_features"]
            ).encode()
            return subprocess.CompletedProcess(argv, 0, stdout, b"")
        if argv[-3:] == ["mcp", "list", "--json"]:
            return subprocess.CompletedProcess(argv, 0, b"[]\n", b"")
        if argv[-3:] == ["plugin", "list", "--json"]:
            return subprocess.CompletedProcess(
                argv, 0, b'{"installed":[],"available":[]}\n', b""
            )

        self.assert_exec_call(argv, kwargs)
        model_root = Path(kwargs["cwd"])
        raw = b"answer\n"
        if self.mode == "raw-mismatch":
            raw = b"different\n"
        (model_root / "raw.md").write_bytes(raw)
        if self.mode == "case-mutation":
            (model_root / "case.md").write_text("changed\n", encoding="utf-8")
        if self.mode == "unexpected-file":
            (model_root / "surprise.txt").write_text("x", encoding="utf-8")
        if self.mode == "unexpected-outer-file":
            (model_root.parent / "surprise.txt").write_text("x", encoding="utf-8")

        stdout = complete_events()
        returncode = 0
        if self.mode == "forbidden-item":
            stdout = b"".join(
                json.dumps(event).encode() + b"\n"
                for event in [
                    {"type": "thread.started", "thread_id": "thread-1"},
                    {"type": "turn.started"},
                    {
                        "type": "item.completed",
                        "item": {"id": "x", "type": "file_change"},
                    },
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "message-1",
                            "type": "agent_message",
                            "text": "answer\n",
                        },
                    },
                    {"type": "turn.completed"},
                ]
            )
        elif self.mode == "external-command":
            stdout = complete_events(
                command=r"Get-Content -LiteralPath C:\Windows\win.ini"
            )
        elif self.mode == "turn-failed":
            stdout = b'{"type":"thread.started","thread_id":"t"}\n' + b'{"type":"turn.failed"}\n'
        elif self.mode == "nonzero":
            returncode = 9
        elif self.mode == "failed-executable-replacement":
            stdout = b"".join(
                json.dumps(event).encode() + b"\n"
                for event in [
                    {"type": "thread.started", "thread_id": "thread-1"},
                    {"type": "turn.started"},
                    {
                        "type": "item.completed",
                        "item": {"id": "x", "type": "file_change"},
                    },
                    {"type": "turn.completed"},
                ]
            )
            Path(self.config["codex"]["executable"]).write_bytes(b"replaced\n")
        elif self.mode == "post-snapshot-raw":
            stdout = complete_events("different\n")
        if self.mode in {"artifact-symlinks", "artifact-hardlinks"}:
            for name in ("events.jsonl", "stderr.bin"):
                protected = (
                    Path(self.config["codex"]["executable"]).parent
                    / f"protected-{model_root.parent.name}-{name}"
                )
                protected.write_bytes(b"protected\n")
                target = model_root.parent / name
                if self.mode == "artifact-symlinks":
                    target.symlink_to(protected)
                else:
                    os.link(protected, target)
                self.protected_artifacts.append(protected)
        if self.mode == "model-root-replacement":
            exec_count = sum("exec" in call["argv"] for call in self.calls)
            if exec_count == 1:
                backup = Path(self.config["codex"]["executable"]).parent / "old-root"
                model_root.rename(backup)
                shutil.copytree(backup, model_root)
        if self.mode == "model-root-deletion":
            shutil.rmtree(model_root)
        if self.mode == "model-root-symlink":
            backup = Path(self.config["codex"]["executable"]).parent / "linked-root"
            model_root.rename(backup)
            model_root.symlink_to(backup, target_is_directory=True)
        if self.mode == "executable-replacement":
            exec_count = sum("exec" in call["argv"] for call in self.calls)
            if exec_count == len(CASES):
                Path(self.config["codex"]["executable"]).write_bytes(b"replaced\n")
        return subprocess.CompletedProcess(argv, returncode, stdout, b"fake stderr")

    def assert_exec_call(self, argv: list[str], kwargs: dict) -> None:
        if "exec" not in argv:
            raise AssertionError(argv)
        if kwargs.get("shell") is not False:
            raise AssertionError("runner must pass shell=False")
        if not isinstance(kwargs.get("input"), bytes):
            raise AssertionError("runner prompt must be bytes on stdin")
        model_root = Path(kwargs["cwd"])
        if not (model_root / "raw.md").is_file():
            raise AssertionError("raw.md was not pre-created")
        if (model_root / "raw.md").read_bytes() != b"":
            raise AssertionError("raw.md was not empty before invocation")


class ConfigContractTest(unittest.TestCase):
    def test_executable_digest_and_length_are_pinned(self):
        runner = load_runner()
        config = make_config()
        runner.validate_config_dict(config)
        config["codex"]["executable_sha256"] = "0" * 64
        with self.assertRaises(runner.RunnerError):
            runner.validate_config_dict(config)
        config = make_config()
        config["codex"]["executable_length"] += 1
        with self.assertRaises(runner.RunnerError):
            runner.validate_config_dict(config)

    def test_checked_in_config_is_strict_and_complete(self):
        runner = load_runner()
        config = runner.decode_config((ROOT / "evals" / "runner-config.json").read_bytes())
        runner.validate_config_dict(config)
        self.assertEqual(config, make_config())
        wrapper = (ROOT / "evals" / "prompt-wrapper.md").read_text(encoding="utf-8")
        self.assertIn("Get-Content -LiteralPath", wrapper)
        self.assertIn("cmd /d /c type", wrapper)
        self.assertNotRegex(wrapper, r"(?i)`cat(?:\.exe)?(?:\s|`)")

    def test_config_rejects_unknown_missing_and_duplicate_fields(self):
        runner = load_runner()
        for mutation in ("unknown-top", "missing-source", "unknown-codex"):
            with self.subTest(mutation=mutation):
                config = make_config()
                if mutation == "unknown-top":
                    config["surprise"] = True
                elif mutation == "missing-source":
                    del config["source"]["rubric_path"]
                else:
                    config["codex"]["extra"] = "no"
                with self.assertRaises(runner.RunnerError):
                    runner.validate_config_dict(config)
        with self.assertRaises(runner.RunnerError):
            runner.decode_config(b'{"schema_version":1,"schema_version":1}')
        with self.assertRaises(runner.RunnerError):
            runner.decode_config(b'{"schema_version":NaN}')

    def test_config_rejects_changed_fixed_invariants(self):
        runner = load_runner()
        mutations = {
            "nine-skills": lambda value: value["source"]["skill_files"].pop(),
            "seven-cases": lambda value: value["source"]["cases"].pop(),
            "ordered-cases": lambda value: value["source"]["cases"].reverse(),
            "unique-cases": lambda value: value["source"]["cases"].__setitem__(
                1, copy.deepcopy(value["source"]["cases"][0])
            ),
            "mount": lambda value: value["source"].__setitem__(
                "skill_mount_dir", "other"
            ),
            "model": lambda value: value["codex"].__setitem__("model", "other"),
            "provider": lambda value: value["codex"].__setitem__(
                "model_provider", "other"
            ),
            "reasoning": lambda value: value["codex"].__setitem__(
                "reasoning_effort", "high"
            ),
            "sandbox": lambda value: value["codex"].__setitem__(
                "sandbox", "workspace-write"
            ),
            "approval": lambda value: value["codex"].__setitem__(
                "approval_policy", "on-request"
            ),
            "flags": lambda value: value["codex"]["fixed_flags"].remove(
                "--strict-config"
            ),
            "features": lambda value: value["codex"]["disabled_features"].pop(),
            "overrides": lambda value: value["codex"]["config_overrides"].pop(),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                config = make_config()
                mutate(config)
                with self.assertRaises(runner.RunnerError):
                    runner.validate_config_dict(config)

    def test_config_rejects_non_utf8_and_unsafe_relative_paths(self):
        runner = load_runner()
        with self.assertRaises(runner.RunnerError):
            runner.decode_config(b"\xff")
        config = make_config()
        config["source"]["cases"][0]["path"] = "../outside.md"
        with self.assertRaises(runner.RunnerError):
            runner.validate_config_dict(config)


class GitCaptureTest(unittest.TestCase):
    def test_requires_full_object_id_and_commit(self):
        runner = load_runner()
        for value in ("HEAD", "abc123", "g" * 40, "a" * 39, "a" * 65):
            with self.subTest(value=value), self.assertRaises(runner.RunnerError):
                runner.validate_commit_argument(value)
        self.assertEqual(runner.validate_commit_argument("a" * 40), "a" * 40)
        self.assertEqual(runner.validate_commit_argument("A" * 64), "a" * 64)

    def test_captures_commit_trees_and_blob_identities(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            repository, commit = make_repository(raw)
            frozen = runner.capture_frozen_inputs(repository, commit, MODULE_PATH)
        self.assertEqual(frozen["commit"], commit)
        for key in ("root_tree", "skill_tree", "cases_tree"):
            self.assertRegex(frozen[key], r"^[0-9a-f]{40,64}$")
        expected_paths = {
            "release-manifest.txt",
            "tools/run_evals.py",
            "evals/runner-config.json",
            "evals/prompt-wrapper.md",
            "evals/rubric.md",
            *(f"skills/research-writing/{path}" for path in SKILL_FILES),
            *(case["path"] for case in CASES),
        }
        self.assertEqual(set(frozen["files"]), expected_paths)
        for path, record in frozen["files"].items():
            self.assertEqual(record["path"], path)
            self.assertIn(record["mode"], ("100644", "100755"))
            self.assertRegex(record["blob_id"], r"^[0-9a-f]{40,64}$")
            self.assertEqual(record["length"], len(record["data"]))
            self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")

    def test_rejects_full_blob_id_that_is_not_a_commit(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            repository, commit = make_repository(raw)
            blob_id = (
                git(repository, "rev-parse", f"{commit}:tools/run_evals.py")
                .stdout.decode("ascii")
                .strip()
            )
            with self.assertRaises(runner.RunnerError):
                runner.capture_frozen_inputs(repository, blob_id, MODULE_PATH)

    def test_rejects_runner_self_mismatch_and_non_blob_mode(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            repository, commit = make_repository(raw)
            different = Path(raw) / "different.py"
            different.write_bytes(MODULE_PATH.read_bytes() + b"# changed\n")
            with self.assertRaises(runner.RunnerError):
                runner.capture_frozen_inputs(repository, commit, different)
        for mode in ("120000", "160000", "040000"):
            with self.subTest(mode=mode), self.assertRaises(runner.RunnerError):
                runner.validate_git_blob_mode(mode, "x")


class OutputAndSnapshotTest(unittest.TestCase):
    def test_output_must_be_new_external_and_unlinked(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repository = base / "checkout"
            repository.mkdir()
            external = base / "run"
            self.assertEqual(
                runner.validate_output_path(external, repository), external.absolute()
            )
            existing = base / "existing"
            existing.mkdir()
            for unsafe in (existing, repository / "run"):
                with self.subTest(unsafe=unsafe), self.assertRaises(runner.RunnerError):
                    runner.validate_output_path(unsafe, repository)

            target = base / "target"
            target.mkdir()
            alias = base / "alias"
            try:
                alias.symlink_to(target, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(runner.RunnerError):
                runner.validate_output_path(alias / "run", repository)

    def make_model_root(self, raw: str) -> Path:
        model_root = Path(raw) / "model-root"
        for relative in SKILL_FILES:
            write_file(model_root, f"research-writing/{relative}", b"skill\n")
        write_file(model_root, "case.md", b"case\n")
        write_file(model_root, "raw.md", b"")
        return model_root

    def test_snapshot_enforces_exact_inventory_and_detects_input_mutation(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            model_root = self.make_model_root(raw)
            before = runner.snapshot_model_root(model_root, SKILL_FILES)
            (model_root / "raw.md").write_bytes(b"allowed\n")
            after = runner.snapshot_model_root(model_root, SKILL_FILES)
            runner.assert_unchanged_inputs(before, after)
            (model_root / "case.md").write_bytes(b"changed\n")
            changed = runner.snapshot_model_root(model_root, SKILL_FILES)
            with self.assertRaises(runner.RunnerError):
                runner.assert_unchanged_inputs(after, changed)
        case_record = before["entries"]["case.md"]
        self.assertEqual(case_record["type"], "file")
        self.assertEqual(case_record["length"], 5)
        self.assertRegex(case_record["sha256"], r"^[0-9a-f]{64}$")

    def test_snapshot_rejects_extra_root_skill_and_links(self):
        runner = load_runner()
        scenarios = ("root", "skill", "link")
        for scenario in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as raw:
                model_root = self.make_model_root(raw)
                if scenario == "root":
                    (model_root / "extra.txt").write_text("x", encoding="utf-8")
                elif scenario == "skill":
                    (model_root / "research-writing" / "extra.txt").write_text(
                        "x", encoding="utf-8"
                    )
                else:
                    link = model_root / "research-writing" / "linked.md"
                    try:
                        link.symlink_to(model_root / "case.md")
                    except (NotImplementedError, OSError) as exc:
                        self.skipTest(f"symlink creation unavailable: {exc}")
                with self.assertRaises(runner.RunnerError):
                    runner.snapshot_model_root(model_root, SKILL_FILES)


class TOCTOUMitigationTest(unittest.TestCase):
    def test_stable_read_rejects_parent_replacement_after_open(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw) / "parent"
            parent.mkdir()
            source = parent / "input.bin"
            source.write_bytes(b"payload")
            original_chain = runner._directory_chain_identity
            calls = 0

            def changing_chain(path, context):
                nonlocal calls
                token = original_chain(path, context)
                calls += 1
                if calls >= 2:
                    # Model a concurrent parent replacement without relying
                    # on rename semantics that differ across Windows/POSIX.
                    return token + (("synthetic-race", (0, 0, 0, 0)),)
                return token

            with mock.patch.object(
                runner, "_directory_chain_identity", side_effect=changing_chain
            ):
                with self.assertRaisesRegex(
                    runner.RunnerError, "parent identity changed"
                ):
                    runner._stable_read(source, "race-read")
            self.assertEqual(source.read_bytes(), b"payload")

    def test_safe_write_rejects_parent_replacement_during_replace(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            parent = base / "parent"
            parent.mkdir()
            target = parent / "result.bin"
            backup = base / "parent-before-race"
            original_replace = runner.os.replace

            def raced_replace(source, destination):
                result = original_replace(source, destination)
                parent.rename(backup)
                parent.mkdir()
                return result

            with mock.patch.object(
                runner.os, "replace", side_effect=raced_replace
            ):
                with self.assertRaisesRegex(
                    runner.RunnerError, "parent identity changed"
                ):
                    runner._safe_write_bytes(target, b"payload", "race-write")
            self.assertEqual((backup / "result.bin").read_bytes(), b"payload")
            self.assertFalse((parent / "result.bin").exists())


class ArtifactInventoryTest(unittest.TestCase):
    def make_inventory(self, raw: str) -> Path:
        output = Path(raw) / "output"
        output.mkdir()
        (output / "manifest.json").write_text("{}\n", encoding="utf-8")
        preflight = output / "preflight"
        preflight.mkdir()
        for probe in ("version", "features", "mcp", "plugin"):
            for stream in ("stdout", "stderr"):
                (preflight / f"{probe}.{stream}.bin").write_bytes(b"")
        cases_root = output / "cases"
        cases_root.mkdir()
        for case in CASES:
            case_root = cases_root / case["id"]
            case_root.mkdir()
            for name in ("prompt.bin", "events.jsonl", "stderr.bin", "audit.json"):
                (case_root / name).write_bytes(b"")
            (case_root / "model-root").mkdir()
            (case_root / "model-root" / "raw.md").write_bytes(b"")
        return output

    def test_accepts_exact_run_artifact_inventory(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            output = self.make_inventory(raw)
            runner.validate_run_artifact_inventory(
                output, [case["id"] for case in CASES]
            )

    def test_rejects_noncanonical_case_ids_before_path_join(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            output = self.make_inventory(raw)
            with self.assertRaisesRegex(runner.RunnerError, "case ID"):
                runner.validate_run_artifact_inventory(output, [".."])

    def test_artifact_content_inventory_rejects_tampering_after_capture(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            output = self.make_inventory(raw)
            case_ids = [case["id"] for case in CASES]
            expected = runner.capture_artifact_inventory(output, case_ids)
            (output / "cases" / case_ids[0] / "events.jsonl").write_bytes(
                b"tampered"
            )
            with self.assertRaisesRegex(runner.RunnerError, "artifact content"):
                runner.verify_artifact_inventory(output, case_ids, expected)

    def test_rejects_missing_extra_and_wrong_type_artifacts(self):
        runner = load_runner()
        scenarios = (
            "top-missing",
            "top-extra",
            "preflight-missing",
            "preflight-extra",
            "preflight-wrong-type",
            "cases-missing",
            "cases-extra",
            "cases-wrong-type",
            "case-missing",
            "case-extra",
            "case-wrong-type",
        )
        for scenario in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as raw:
                output = self.make_inventory(raw)
                first_case = output / "cases" / CASES[0]["id"]
                if scenario == "top-missing":
                    (output / "manifest.json").unlink()
                elif scenario == "top-extra":
                    (output / "unexpected.bin").write_bytes(b"")
                elif scenario == "preflight-missing":
                    (output / "preflight" / "version.stdout.bin").unlink()
                elif scenario == "preflight-extra":
                    (output / "preflight" / "unexpected.bin").write_bytes(b"")
                elif scenario == "preflight-wrong-type":
                    path = output / "preflight" / "version.stdout.bin"
                    path.unlink()
                    path.mkdir()
                elif scenario == "cases-missing":
                    shutil.rmtree(first_case)
                elif scenario == "cases-extra":
                    (output / "cases" / "unexpected").mkdir()
                elif scenario == "cases-wrong-type":
                    shutil.rmtree(first_case)
                    first_case.write_bytes(b"")
                elif scenario == "case-missing":
                    (first_case / "audit.json").unlink()
                elif scenario == "case-extra":
                    (first_case / "unexpected.bin").write_bytes(b"")
                else:
                    path = first_case / "model-root"
                    # The inventory fixture includes raw.md so content hashing
                    # can be exercised; remove it before converting the
                    # directory into the deliberately wrong file type.
                    (path / "raw.md").unlink()
                    path.rmdir()
                    path.write_bytes(b"")
                with self.assertRaises(runner.RunnerError):
                    runner.validate_run_artifact_inventory(
                        output, [case["id"] for case in CASES]
                    )

    def test_rejects_casefold_collisions_and_links_without_following(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            output = self.make_inventory(raw)
            (output / "collision-ss").write_bytes(b"")
            (output / "collision-\N{LATIN SMALL LETTER SHARP S}").write_bytes(b"")
            with self.assertRaisesRegex(runner.RunnerError, "case-colliding"):
                runner.validate_run_artifact_inventory(
                    output, [case["id"] for case in CASES]
                )

        with tempfile.TemporaryDirectory() as raw:
            output = self.make_inventory(raw)
            preflight = output / "preflight"
            shutil.rmtree(preflight)
            target = Path(raw) / "preflight-target"
            target.mkdir()
            try:
                preflight.symlink_to(target, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(runner.RunnerError):
                runner.validate_run_artifact_inventory(
                    output, [case["id"] for case in CASES]
                )


class InvocationAndPreflightTest(unittest.TestCase):
    def test_evaluation_provider_uses_an_explicit_custom_alias(self):
        config = make_config()
        self.assertEqual(config["codex"]["model_provider"], "custom")
        self.assertIn('model_provider="custom"', config["codex"]["config_overrides"])

    def test_exec_argv_is_fixed_and_never_ignores_user_config(self):
        runner = load_runner()
        config = make_config()
        argv = runner.build_exec_argv(Path(FIXED_EXECUTABLE), config)
        self.assertEqual(argv[0], FIXED_EXECUTABLE)
        self.assertIn("exec", argv)
        for flag in config["codex"]["fixed_flags"]:
            self.assertIn(flag, argv)
        self.assertEqual(argv[-1], "-")
        self.assertNotIn("--ignore-user-config", argv)
        self.assertEqual(argv.count("--strict-config"), 1)
        self.assertEqual(argv[argv.index("-o") + 1], "raw.md")
        self.assertIn("--ask-for-approval", argv)
        self.assertEqual(argv[argv.index("--ask-for-approval") + 1], "never")
        self.assertLess(
            argv.index("--ask-for-approval"),
            argv.index("exec"),
            "--ask-for-approval is a global CLI option and must precede exec",
        )

    def test_preflight_records_and_validates_all_probes(self):
        runner = load_runner()
        config = make_config()
        fake = FakeCodex(config)
        with tempfile.TemporaryDirectory() as raw:
            preflight = Path(raw) / "preflight"
            result = runner.run_preflight(
                Path(FIXED_EXECUTABLE), config, preflight, process_runner=fake
            )
            names = {path.name for path in preflight.iterdir()}
        self.assertEqual(result["version"], config["codex"]["expected_version"])
        self.assertEqual(
            names,
            {
                f"{probe}.{stream}.bin"
                for probe in ("version", "features", "mcp", "plugin")
                for stream in ("stdout", "stderr")
            },
        )
        self.assertEqual(len(fake.calls), 4)
        self.assertEqual(
            [call["argv"].count("--strict-config") for call in fake.calls],
            [1, 0, 0, 0],
        )
        self.assertEqual(fake.calls[0]["argv"][1], "--strict-config")
        self.assertTrue(result["formal_exec_strict_config"])
        rationale = "pinned CLI subcommand does not support --strict-config"
        for index, probe in enumerate(("version", "features", "mcp", "plugin")):
            record = result["probes"][probe]
            self.assertEqual(record["strict_config_applied"], index == 0)
            if index == 0:
                self.assertNotIn("strict_config_compatibility", record)
            else:
                self.assertEqual(record["strict_config_compatibility"], rationale)
        for call in fake.calls:
            self.assertNotIn("--ignore-user-config", call["argv"])
            for override in CONFIG_OVERRIDES:
                self.assertIn(override, call["argv"])

    def test_preflight_rejects_version_feature_mcp_and_plugin_drift(self):
        runner = load_runner()
        config = make_config()

        class Drift(FakeCodex):
            def __init__(self, config, probe):
                super().__init__(config)
                self.probe = probe

            def __call__(self, argv, **kwargs):
                result = super().__call__(argv, **kwargs)
                args = list(map(os.fspath, argv))
                if self.probe == "version" and "--version" in args:
                    result.stdout = b"codex-cli 0.0.0\n"
                if self.probe == "version-blank" and "--version" in args:
                    result.stdout = (
                        self.config["codex"]["expected_version"] + "\n\n"
                    ).encode()
                if self.probe == "features" and args[-2:] == ["features", "list"]:
                    result.stdout = result.stdout.replace(b"false", b"true", 1)
                if self.probe == "mcp" and args[-3:] == ["mcp", "list", "--json"]:
                    result.stdout = b'[{"name":"x"}]\n'
                if self.probe == "plugin" and args[-3:] == ["plugin", "list", "--json"]:
                    result.stdout = b'{"installed":["x"],"available":[]}\n'
                return result

        for probe in ("version", "version-blank", "features", "mcp", "plugin"):
            with self.subTest(probe=probe), tempfile.TemporaryDirectory() as raw:
                preflight = Path(raw) / "preflight"
                with self.assertRaises(runner.RunnerError):
                    runner.run_preflight(
                        Path(FIXED_EXECUTABLE),
                        config,
                        preflight,
                        process_runner=Drift(config, probe),
                    )
                self.assertTrue(any(preflight.iterdir()))


class EventAuditTest(unittest.TestCase):
    def make_root(self, raw: str) -> Path:
        root = Path(raw) / "model-root"
        write_file(root, "research-writing/SKILL.md", b"skill\n")
        write_file(root, "case.md", b"case\n")
        write_file(root, "raw.md", b"answer\n")
        return root

    def audit(self, runner, root: Path, events: bytes, raw: bytes = b"answer\n"):
        (root / "raw.md").write_bytes(raw)
        return runner.parse_and_audit_events(events, raw, root, make_config())

    def test_accepts_lifecycle_and_simple_relative_read_commands(self):
        runner = load_runner()
        commands = (
            "Get-Content -Raw -LiteralPath research-writing/SKILL.md",
            "cmd /d /c type case.md",
        )
        for command in commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as raw:
                root = self.make_root(raw)
                audit = self.audit(runner, root, complete_events(command=command))
                self.assertEqual(audit["command_count"], 1)
                self.assertEqual(audit["final_message_sha256"], audit["raw_sha256"])

    def test_accepts_only_fixed_windows_shell_wrappers_for_relative_reads(self):
        """The real Windows Codex client reports its shell executable wrapper.

        This is intentionally RED until the auditor normalizes that wrapper to
        the same tiny read grammar as the canonical commands above.  The
        wrapper executable and option order are fixed; the inner command must
        still be one of the existing relative read forms.
        """
        runner = load_runner()
        commands = (
            r'"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" '
            r'-Command "Get-Content -LiteralPath .\case.md"',
            r'"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" '
            r'-NoProfile -Command "Get-Content -Raw -LiteralPath '
            r'research-writing\SKILL.md"',
            (
                r'"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" '
                r"-Command 'cmd /d /c type case.md'"
            ),
        )
        expected_paths = ("case.md", "research-writing/SKILL.md", "case.md")
        for command, expected_path in zip(commands, expected_paths, strict=True):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as raw:
                root = self.make_root(raw)
                audit = self.audit(runner, root, complete_events(command=command))
                self.assertEqual(audit["command_count"], 1)
                self.assertEqual(audit["commands"][0]["path"], expected_path)

    def test_wrapped_reads_still_reject_wrong_executable_injection_and_nonzero_exit(self):
        runner = load_runner()
        fixed = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
        commands = (
            # A relative or different executable must not become trusted merely
            # because its -Command payload looks like a read.
            r'powershell.exe -Command "Get-Content -LiteralPath case.md"',
            r'"C:\Temp\powershell.exe" -Command "Get-Content -LiteralPath case.md"',
            # Metacharacters and encoded/extra commands remain forbidden.
            rf'"{fixed}" -EncodedCommand AAAA',
            rf'"{fixed}" -Command "Get-Content -LiteralPath case.md; whoami"',
            rf'"{fixed}" -Command "Get-Content -LiteralPath ..\outside.md"',
        )
        for command in commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as raw:
                root = self.make_root(raw)
                with self.assertRaises(runner.RunnerError):
                    self.audit(runner, root, complete_events(command=command))

        # Keep the exit-code assertion independent of wrapper support so this
        # test remains a green guard while the acceptance test above is RED.
        failed = complete_events(command="Get-Content -LiteralPath case.md").replace(
            b'"exit_code":0', b'"exit_code":1', 1
        )
        with tempfile.TemporaryDirectory() as raw:
            root = self.make_root(raw)
            with self.assertRaisesRegex(runner.RunnerError, "exited nonzero"):
                self.audit(runner, root, failed)

    def test_rejects_non_utf8_malformed_unknown_and_forbidden_items(self):
        runner = load_runner()
        payloads = {
            "non-utf8": b"\xff\n",
            "malformed": b"{no}\n",
            "unknown-event": complete_events().replace(
                b'"turn.completed"', b'"surprise"'
            ),
            "forbidden-item": complete_events().replace(
                b'"agent_message"', b'"file_change"'
            ),
            "unknown-item": complete_events().replace(
                b'"agent_message"', b'"mystery"'
            ),
        }
        for name, payload in payloads.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as raw:
                root = self.make_root(raw)
                with self.assertRaises(runner.RunnerError):
                    self.audit(runner, root, payload)

    def test_rejects_external_parent_write_combined_and_network_commands(self):
        runner = load_runner()
        commands = (
            r"Get-Content -LiteralPath C:\Windows\win.ini",
            "Get-Content -LiteralPath ../outside.md",
            "cmd /c type case.md",
            "cat case.md",
            "cat -- case.md",
            "CAT -- case.md",
            "cat.exe -- case.md",
            r"C:\Windows\System32\cat.exe case.md",
            "Set-Content -LiteralPath case.md x",
            "Get-Content -LiteralPath case.md | Select-Object -First 1",
            "curl https://example.invalid",
            "python -c print(1)",
        )
        for command in commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as raw:
                root = self.make_root(raw)
                with self.assertRaises(runner.RunnerError):
                    self.audit(runner, root, complete_events(command=command))

    def test_rejects_incomplete_or_inconsistent_item_lifecycles(self):
        runner = load_runner()

        def decoded(payload):
            return [json.loads(line) for line in payload.splitlines()]

        def encoded(events):
            return b"".join(json.dumps(event).encode() + b"\n" for event in events)

        idless = decoded(
            complete_events(command="Get-Content -LiteralPath case.md")
        )
        idless[2]["item"].pop("id")
        idless[3]["item"].pop("id")

        update_before_start = decoded(complete_events())
        update_before_start.insert(
            2,
            {
                "type": "item.updated",
                "item": {"id": "reason-1", "type": "reasoning", "text": "x"},
            },
        )

        incomplete_started_item = decoded(complete_events())
        incomplete_started_item.insert(
            2,
            {
                "type": "item.started",
                "item": {"id": "reason-1", "type": "reasoning", "text": "x"},
            },
        )

        changed_command = decoded(
            complete_events(command="Get-Content -LiteralPath case.md")
        )
        changed_command[3]["item"]["command"] = (
            "Get-Content -LiteralPath research-writing/SKILL.md"
        )

        unknown_field = decoded(complete_events())
        unknown_field[1]["surprise"] = True

        for name, events in {
            "idless-command": idless,
            "update-before-start": update_before_start,
            "incomplete-start": incomplete_started_item,
            "changed-command": changed_command,
            "unknown-event-field": unknown_field,
        }.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as raw:
                root = self.make_root(raw)
                with self.assertRaises(runner.RunnerError):
                    self.audit(runner, root, encoded(events))

    def test_rejects_nonzero_command_failed_turn_and_missing_terminal(self):
        runner = load_runner()
        nonzero_command = complete_events(command="cmd /d /c type case.md").replace(
            b'"exit_code":0', b'"exit_code":7'
        )
        failed_turn = b'{"type":"thread.started","thread_id":"t"}\n' + b'{"type":"turn.failed"}\n'
        missing_terminal = complete_events().replace(
            b'{"type":"turn.completed","usage":{}}\n', b""
        )
        for payload in (nonzero_command, failed_turn, missing_terminal):
            with tempfile.TemporaryDirectory() as raw:
                root = self.make_root(raw)
                with self.assertRaises(runner.RunnerError):
                    self.audit(runner, root, payload)

    def test_final_message_must_match_raw_bytes_including_newline(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            root = self.make_root(raw)
            self.audit(runner, root, complete_events("answer\n"), b"answer\n")
            for events, output in (
                (complete_events("answer"), b"answer\n"),
                (complete_events("answer\n"), b"answer"),
            ):
                with self.assertRaises(runner.RunnerError):
                    self.audit(runner, root, events, output)


class RunnerIntegrationTest(unittest.TestCase):
    def assert_terminal_timing(self, record: dict) -> None:
        for field in ("started_at", "finished_at"):
            value = record[field]
            self.assertRegex(value, r"(?:Z|\+00:00)$")
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            self.assertEqual(parsed.utcoffset(), timedelta(0))
        self.assertIsInstance(record["duration_seconds"], float)
        self.assertGreaterEqual(record["duration_seconds"], 0.0)

    def run_fixture(
        self,
        raw: str,
        mode: str = "ok",
        runner=None,
        **run_kwargs,
    ):
        runner = runner or load_runner()
        fake_executable = Path(raw) / "codex.exe"
        fake_bytes = b"fake executable\n"
        fake_executable.write_bytes(fake_bytes)
        fake_executable.chmod(0o755)
        config = make_config(str(fake_executable.absolute()))
        config["codex"]["executable_length"] = len(fake_bytes)
        config["codex"]["executable_sha256"] = hashlib.sha256(fake_bytes).hexdigest()
        repository, commit = make_repository(raw, config)
        output = Path(raw) / "output"
        fake = FakeCodex(config, mode)
        with mock.patch.object(
            runner,
            "EXPECTED_CODEX_EXECUTABLE",
            str(fake_executable.absolute()),
        ), mock.patch.object(
            runner, "EXPECTED_CODEX_EXECUTABLE_LENGTH", len(fake_bytes)
        ), mock.patch.object(
            runner, "EXPECTED_CODEX_EXECUTABLE_SHA256", config["codex"]["executable_sha256"]
        ):
            result = runner.run_evaluations(
                repository,
                commit,
                output,
                process_runner=fake,
                runner_path=MODULE_PATH,
                **run_kwargs,
            )
        return result, output, fake, runner

    def test_fake_cli_run_preserves_layout_argv_cwd_and_stdin(self):
        with tempfile.TemporaryDirectory() as raw:
            clock = DeterministicClock()
            result, output, fake, runner = self.run_fixture(
                raw,
                utc_now=clock.utc_now,
                monotonic=clock.monotonic,
            )
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "complete")
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(len(manifest["cases"]), 7)
            exec_calls = [call for call in fake.calls if "exec" in call["argv"]]
            self.assertEqual(len(exec_calls), 7)
            for case, call in zip(CASES, exec_calls, strict=True):
                case_root = output / "cases" / case["id"]
                model_root = case_root / "model-root"
                self.assertEqual(Path(call["cwd"]), model_root)
                self.assertTrue(call["input"])
                self.assertEqual(
                    {path.name for path in model_root.iterdir()},
                    {"research-writing", "case.md", "raw.md"},
                )
                for name in ("prompt.bin", "events.jsonl", "stderr.bin", "audit.json"):
                    self.assertTrue((case_root / name).is_file(), name)
                argv = call["argv"]
                self.assertNotIn("--ignore-user-config", argv)
                self.assertEqual(argv[-1], "-")
            self.assertEqual(manifest["audit_scope"], runner.AUDIT_SCOPE)
            self.assertTrue(manifest["user_config_loaded"])
            self.assertFalse(manifest["runtime_file_read_attestation"])
            self.assertEqual(manifest["started_at"], "2026-08-16T00:00:00Z")
            self.assertEqual(manifest["finished_at"], "2026-08-16T00:00:15Z")
            self.assertEqual(manifest["duration_seconds"], 15.0)
            self.assert_terminal_timing(manifest)
            for index, case_manifest in enumerate(manifest["cases"]):
                started = 1 + 2 * index
                finished = started + 1
                self.assertEqual(
                    case_manifest["started_at"],
                    f"2026-08-16T00:00:{started:02d}Z",
                )
                self.assertEqual(
                    case_manifest["finished_at"],
                    f"2026-08-16T00:00:{finished:02d}Z",
                )
                self.assertEqual(case_manifest["duration_seconds"], 1.0)
                self.assert_terminal_timing(case_manifest)

    def test_case_artifact_links_cannot_modify_external_files(self):
        for mode in ("artifact-symlinks", "artifact-hardlinks"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                if mode == "artifact-symlinks":
                    probe_target = Path(raw) / "symlink-target"
                    probe_link = Path(raw) / "symlink-probe"
                    probe_target.write_bytes(b"probe")
                    try:
                        probe_link.symlink_to(probe_target)
                    except (NotImplementedError, OSError) as exc:
                        self.skipTest(f"symlink creation unavailable: {exc}")
                result, output, fake, _runner = self.run_fixture(raw, mode)
                self.assertEqual(result["status"], "complete")
                self.assertTrue(fake.protected_artifacts)
                for protected in fake.protected_artifacts:
                    self.assertEqual(protected.read_bytes(), b"protected\n")
                for case in CASES:
                    for name in ("events.jsonl", "stderr.bin"):
                        target = output / "cases" / case["id"] / name
                        self.assertTrue(target.is_file())
                        self.assertFalse(target.is_symlink())

    def test_case_failure_records_deterministic_terminal_timing(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            clock = DeterministicClock()
            with self.assertRaises(runner.RunnerError):
                self.run_fixture(
                    raw,
                    "forbidden-item",
                    runner,
                    utc_now=clock.utc_now,
                    monotonic=clock.monotonic,
                )
            manifest = json.loads(
                (Path(raw) / "output" / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["started_at"], "2026-08-16T00:00:00Z")
            self.assertEqual(manifest["finished_at"], "2026-08-16T00:00:03Z")
            self.assertEqual(manifest["duration_seconds"], 3.0)
            failed_case = manifest["cases"][0]
            self.assertEqual(failed_case["started_at"], "2026-08-16T00:00:01Z")
            self.assertEqual(failed_case["finished_at"], "2026-08-16T00:00:02Z")
            self.assertEqual(failed_case["duration_seconds"], 1.0)
            self.assert_terminal_timing(manifest)
            self.assert_terminal_timing(failed_case)

    def test_failures_keep_raw_artifacts_and_partial_manifest(self):
        modes = (
            "forbidden-item",
            "external-command",
            "case-mutation",
            "unexpected-file",
            "unexpected-outer-file",
            "raw-mismatch",
            "nonzero",
            "turn-failed",
            "executable-replacement",
            "failed-executable-replacement",
            "model-root-replacement",
            "model-root-deletion",
            "model-root-symlink",
        )
        for mode in modes:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                runner = load_runner()
                with self.assertRaises(runner.RunnerError):
                    self.run_fixture(raw, mode, runner)
                output = Path(raw) / "output"
                manifest = json.loads(
                    (output / "manifest.json").read_text(encoding="utf-8")
                )
                self.assertEqual(manifest["status"], "failed")
                self.assertIn("stage", manifest["diagnostic"])
                self.assert_terminal_timing(manifest)
                for case_manifest in manifest["cases"]:
                    self.assert_terminal_timing(case_manifest)
                case_root = output / "cases" / CASES[0]["id"]
                self.assertTrue((case_root / "events.jsonl").is_file())
                self.assertTrue((case_root / "stderr.bin").is_file())
                if mode == "unexpected-file":
                    audit = json.loads(
                        (case_root / "audit.json").read_text(encoding="utf-8")
                    )
                    self.assertIn("after_snapshot", audit)
                    self.assertIn("surprise.txt", audit["after_snapshot"]["root_entries"])
                if mode == "unexpected-outer-file":
                    self.assertEqual(
                        manifest["diagnostic"]["stage"],
                        "validate-artifact-inventory",
                    )
                    for case in CASES:
                        self.assertTrue(
                            (
                                output
                                / "cases"
                                / case["id"]
                                / "audit.json"
                            ).is_file()
                        )
                if mode == "failed-executable-replacement":
                    self.assertEqual(
                        manifest["executable_integrity"]["status"], "failed"
                    )
                if mode in {"model-root-deletion", "model-root-symlink"}:
                    audit = json.loads(
                        (case_root / "audit.json").read_text(encoding="utf-8")
                    )
                    expected_state = (
                        "missing"
                        if mode == "model-root-deletion"
                        else "link-or-reparse"
                    )
                    self.assertEqual(
                        audit["after_snapshot"]["root_state"], expected_state
                    )
                    self.assertEqual(audit["after_snapshot"]["tree_entries"], [])

    def test_rejects_raw_change_between_after_snapshot_and_audit_read(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            fake_executable = Path(raw) / "codex.exe"
            fake_bytes = b"fake executable\n"
            fake_executable.write_bytes(fake_bytes)
            fake_executable.chmod(0o755)
            config = make_config(str(fake_executable.absolute()))
            config["codex"]["executable_length"] = len(fake_bytes)
            config["codex"]["executable_sha256"] = hashlib.sha256(fake_bytes).hexdigest()
            repository, commit = make_repository(raw, config)
            output = Path(raw) / "output"
            fake = FakeCodex(config, "post-snapshot-raw")
            original_assert = runner.assert_unchanged_inputs
            call_index = 0

            def mutate_after_snapshot(before, after):
                nonlocal call_index
                original_assert(before, after)
                case_id = CASES[call_index]["id"]
                call_index += 1
                (output / "cases" / case_id / "model-root" / "raw.md").write_bytes(
                    b"different\n"
                )

            with mock.patch.object(
                runner, "EXPECTED_CODEX_EXECUTABLE", str(fake_executable.absolute())
            ), mock.patch.object(
                runner, "EXPECTED_CODEX_EXECUTABLE_LENGTH", len(fake_bytes)
            ), mock.patch.object(
                runner,
                "EXPECTED_CODEX_EXECUTABLE_SHA256",
                config["codex"]["executable_sha256"],
            ), mock.patch.object(
                runner, "assert_unchanged_inputs", side_effect=mutate_after_snapshot
            ), self.assertRaises(runner.RunnerError):
                runner.run_evaluations(
                    repository,
                    commit,
                    output,
                    process_runner=fake,
                    runner_path=MODULE_PATH,
                )
            manifest = json.loads(
                (output / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["cases"][0]["status"], "failed")
            self.assertIn("raw.md changed after", manifest["diagnostic"]["message"])

    def test_malformed_event_types_fail_with_runner_error(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "model-root"
            root.mkdir()
            malformed_event = b'{"type":[]}' + b"\n"
            with self.assertRaises(runner.RunnerError):
                runner.parse_and_audit_events(
                    malformed_event, b"answer\n", root, make_config()
                )

    def test_capture_failure_writes_atomic_partial_manifest(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as raw:
            clock = DeterministicClock()
            fake_executable = Path(raw) / "codex.exe"
            fake_executable.write_bytes(b"fake executable\n")
            fake_executable.chmod(0o755)
            config = make_config(str(fake_executable.absolute()))
            repository, commit = make_repository(raw, config)
            mismatched_runner = Path(raw) / "different-runner.py"
            mismatched_runner.write_bytes(MODULE_PATH.read_bytes() + b"# mismatch\n")
            output = Path(raw) / "output"
            with mock.patch.object(
                runner, "EXPECTED_CODEX_EXECUTABLE", str(fake_executable.absolute())
            ), self.assertRaises(runner.RunnerError):
                runner.run_evaluations(
                    repository,
                    commit,
                    output,
                    process_runner=FakeCodex(config),
                    runner_path=mismatched_runner,
                    utc_now=clock.utc_now,
                    monotonic=clock.monotonic,
                )
            manifest = json.loads(
                (output / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["diagnostic"]["stage"], "capture-frozen-inputs")
            self.assertEqual(manifest["started_at"], "2026-08-16T00:00:00Z")
            self.assertEqual(manifest["finished_at"], "2026-08-16T00:00:01Z")
            self.assertEqual(manifest["duration_seconds"], 1.0)
            self.assertEqual(manifest["cases"], [])
            self.assert_terminal_timing(manifest)


if __name__ == "__main__":
    unittest.main()
