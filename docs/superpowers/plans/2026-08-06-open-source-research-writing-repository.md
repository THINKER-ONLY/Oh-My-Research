# Open-Source Research Writing Skill Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current research-writing workspace into a testable open-source repository with one minimal publishable Skill package, source-grounded writing rules, deterministic releases, and an unchanged `doc/` corpus.

**Architecture:** Move the runtime Skill to `skills/research-writing/`; move corpus maintenance and evaluations to repository-level `tools/` and `evals/`, with immutable dated run artifacts. Add repository validation and an allowlisted cross-platform deterministic release builder. Refactor the Skill only after static and behavioral RED tests expose the current source-traceability, schema, and genre-flexibility gaps.

**Tech Stack:** Python 3.12, `unittest`, PyMuPDF, requests, PyYAML, Markdown, YAML, CSV, GitHub Actions

**Execution prerequisite:** Run this plan on a dedicated feature branch created from `main` in the current checkout. Do not execute implementation tasks directly on `main`; the full ignored `doc/` corpus must remain available in this checkout, so a normal linked worktree is not sufficient for the final baseline comparison.

---

## File Map

### Move

- `research-writing/` -> `skills/research-writing/`: installable runtime Skill.
- `skills/research-writing/scripts/corpus.py` -> `tools/corpus.py`: repository-local corpus inventory/download tool.
- `skills/research-writing/evals/` -> `evals/`: development evaluation evidence.

### Create

- `README.md`: user-facing repository overview, installation, release boundary, validation, and evaluation limits.
- `LICENSE`: canonical Apache License 2.0 text for original project material.
- `CONTRIBUTING.md`: contribution workflow and source/copyright constraints.
- `SECURITY.md`: private vulnerability and sensitive-material reporting instructions.
- `THIRD_PARTY_NOTICES.md`: explicit exclusion of third-party PDFs and `doc/` from the project license.
- `requirements.txt`: bounded development dependencies.
- `release-manifest.txt`: exact release allowlist.
- `.gitattributes`: export exclusions as a second defense around the allowlisted release builder.
- `.github/workflows/ci.yml`: Windows/Linux validation.
- `tools/validate_repository.py`: deterministic structure, source, schema, and release-boundary validator.
- `tools/build_release.py`: deterministic ZIP builder driven only by `release-manifest.txt`.
- `tests/test_repository.py`: repository, Skill package, source matrix, and release tests.
- `skills/research-writing/references/source-foundations.md`: page-level writing-philosophy provenance matrix.
- `docs/skill-design-review.md`: critical design assessment and resolutions.
- `evals/cases/05-source-foundations.md`: source-rationale retrieval case.
- `evals/cases/06-genre-flexibility.md`: genre-sensitive structure case.
- `evals/cases/07-proportional-edit.md`: one-sentence proportionality regression case.
- `evals/run-metadata.md`: provenance and limitations for old and new evaluation runs.
- `docs/superpowers/specs/2026-08-06-doc-baseline.tsv`: pre-implementation per-file path, size, UTC timestamp, and content SHA-256 control recorded without modifying `doc/`.

### Modify

- `.gitignore`: ignore `dist/` and release ZIPs without changing any `doc/` rule.
- `tests/test_corpus.py`: load `tools/corpus.py` from its new path.
- `skills/research-writing/SKILL.md`: canonical evidence schema, genre-aware structure selection, source-foundation routing, and reduced duplication.
- `skills/research-writing/references/writing-workflow.md`: canonical status fields and genre-aware structure phase.
- `skills/research-writing/references/section-guides.md`: make section patterns conditional on genre and venue.
- `skills/research-writing/references/evidence-and-integrity.md`: separate claim type, support status, and citation status.
- `skills/research-writing/references/revision-and-style.md`: preserve existing semantic and compression safeguards while making stylistic guidance explicitly conditional.
- `skills/research-writing/assets/evidence-ledger.csv`: smaller canonical schema.
- `skills/research-writing/agents/openai.yaml`: verify or regenerate after the final Skill text.
- `evals/comparison.md`: append bounded results for Cases 05-07 without rewriting the original four-case scores.

## Task 1: Freeze the `doc/` Baseline and Write the Repository-Layout RED Test

**Files:**

- Read: `docs/superpowers/specs/2026-08-06-doc-baseline.tsv`
- Create: `tests/test_repository.py`

- [ ] **Step 1: Verify the immutable `doc/` baseline**

Run this read-only PowerShell command from the repository root:

```powershell
$branch = git branch --show-current
if ($branch -in @('main', 'master', '')) { throw 'Run implementation on a named feature branch, not main/master' }
$startRevision = git merge-base HEAD main
$headRevision = git rev-parse HEAD
if ($startRevision -ne $headRevision) { throw 'Feature branch must begin Task 1 at its main branch point' }

$root = (Resolve-Path 'doc').Path
$baselinePath = (Resolve-Path 'docs/superpowers/specs/2026-08-06-doc-baseline.tsv').Path
$baseline = [IO.File]::ReadAllLines($baselinePath, [Text.Encoding]::UTF8) |
  Select-Object -Skip 2 |
  ConvertFrom-Csv -Delimiter "`t"
$items = Get-ChildItem -LiteralPath $root -Recurse -File | Sort-Object FullName
$current = foreach ($item in $items) {
  $relativeNative = $item.FullName.Substring($root.Length).TrimStart('\')
  [PSCustomObject]@{
    relative_path = $relativeNative.Replace('\','/')
    bytes = "$($item.Length)"
    mtime_utc_ticks = "$($item.LastWriteTimeUtc.Ticks)"
    sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}
$differences = @(Compare-Object -ReferenceObject $baseline -DifferenceObject $current -Property relative_path,bytes,mtime_utc_ticks,sha256 -PassThru)
if ($differences.Count -gt 0) {
  $differences | Format-Table relative_path,bytes,mtime_utc_ticks,sha256,SideIndicator -AutoSize
  throw 'doc baseline differs'
}

$metadataRecords = foreach ($item in $items) {
  $relativeNative = $item.FullName.Substring($root.Length).TrimStart('\')
  "$relativeNative`t$($item.Length)`t$($item.LastWriteTimeUtc.Ticks)"
}
$contentRecords = $current | ForEach-Object {
  "$($_.relative_path)`t$($_.bytes)`t$($_.mtime_utc_ticks)`t$($_.sha256)"
}
$metadataPayload = [Text.Encoding]::UTF8.GetBytes(($metadataRecords -join "`n"))
$metadataSha = [Security.Cryptography.SHA256]::Create()
$metadataDigest = [BitConverter]::ToString($metadataSha.ComputeHash($metadataPayload)).Replace('-','').ToLowerInvariant()
$contentPayload = [Text.Encoding]::UTF8.GetBytes(($contentRecords -join "`n"))
$contentSha = [Security.Cryptography.SHA256]::Create()
$contentDigest = [BitConverter]::ToString($contentSha.ComputeHash($contentPayload)).Replace('-','').ToLowerInvariant()
"files=$($items.Count) bytes=$((($items | Measure-Object Length -Sum).Sum)) metadata_sha256=$metadataDigest content_metadata_sha256=$contentDigest"
```

Expected:

```text
files=83 bytes=222559046 metadata_sha256=7698527d65a098ecf449ddc34340b0c02cf5bc6d47931d93ef8b83407c59d7b9 content_metadata_sha256=5045a0e383ded4e474ee6976b21f246e766f6f22a8ff62be55cc2744e119ef59
```

Record the exact `$startRevision` value in the task report. Task 10 recomputes the same merge base; do not substitute a remembered or abbreviated value.

- [ ] **Step 2: Create the failing layout test**

Create `tests/test_repository.py` with this initial content:

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "research-writing"


class RepositoryLayoutTest(unittest.TestCase):
    def test_runtime_skill_is_isolated_from_development_artifacts(self):
        self.assertTrue(SKILL_DIR.is_dir())
        self.assertTrue((SKILL_DIR / "SKILL.md").is_file())
        self.assertFalse((ROOT / "research-writing").exists())
        self.assertTrue((ROOT / "tools" / "corpus.py").is_file())
        self.assertTrue((ROOT / "evals" / "rubric.md").is_file())
        self.assertFalse((SKILL_DIR / "evals").exists())
        self.assertFalse((SKILL_DIR / "scripts" / "corpus.py").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the layout test and verify RED**

Run:

```powershell
python -B -m unittest tests.test_repository -v
```

Expected: FAIL at `self.assertTrue(SKILL_DIR.is_dir())` because `skills/research-writing/` does not exist.

- [ ] **Step 4: Commit the failing structural specification**

```powershell
git add -- tests/test_repository.py
git commit -m "test: specify publishable skill layout"
```

## Task 2: Move Runtime and Development Files to Their Approved Boundaries

**Files:**

- Move: `research-writing/` -> `skills/research-writing/`
- Move: `skills/research-writing/scripts/corpus.py` -> `tools/corpus.py`
- Move: `skills/research-writing/evals/` -> `evals/`
- Modify: `tests/test_corpus.py:6`

- [ ] **Step 1: Resolve and verify every move target**

Run:

```powershell
$workspace = (Resolve-Path '.').Path
$source = (Resolve-Path 'research-writing').Path
$skillsParent = Join-Path $workspace 'skills'
$skillTarget = Join-Path $skillsParent 'research-writing'
$toolsTarget = Join-Path $workspace 'tools'
$evalTarget = Join-Path $workspace 'evals'

if (-not $source.StartsWith($workspace, [StringComparison]::OrdinalIgnoreCase)) { throw 'Source escaped workspace' }
foreach ($target in @($skillTarget, $toolsTarget, $evalTarget)) {
  if (-not $target.StartsWith($workspace, [StringComparison]::OrdinalIgnoreCase)) { throw "Target escaped workspace: $target" }
}
if (Test-Path -LiteralPath $skillTarget) { throw 'Skill target already exists' }
if (Test-Path -LiteralPath $evalTarget) { throw 'Eval target already exists' }

$ignored = @(git ls-files --others --ignored --exclude-standard -- research-writing)
$unexpectedIgnored = @($ignored | Where-Object {
  $_ -notmatch '^research-writing/scripts/__pycache__/[^/]+\.pyc$'
})
if ($unexpectedIgnored.Count -gt 0) {
  throw "Unexpected ignored files under runtime source: $($unexpectedIgnored -join ', ')"
}
```

Expected: exit 0 with no output.

- [ ] **Step 2: Perform the version-preserving moves**

Run:

```powershell
$cacheDir = Join-Path $source 'scripts\__pycache__'
if (Test-Path -LiteralPath $cacheDir) {
  $resolvedCache = (Resolve-Path -LiteralPath $cacheDir).Path
  if (-not $resolvedCache.StartsWith($source, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Cache path escaped runtime source'
  }
  $cacheEntries = @(Get-ChildItem -LiteralPath $resolvedCache -Recurse -Force)
  $unexpectedCache = @($cacheEntries | Where-Object {
    $_.PSIsContainer -or $_.Extension -ne '.pyc'
  })
  if ($unexpectedCache.Count -gt 0) { throw 'Runtime cache contains non-pyc content' }
  Remove-Item -LiteralPath $resolvedCache -Recurse
}

New-Item -ItemType Directory -Path 'skills' -Force | Out-Null
New-Item -ItemType Directory -Path 'tools' -Force | Out-Null
git mv -- research-writing skills/research-writing
git mv -- skills/research-writing/evals evals
git mv -- skills/research-writing/scripts/corpus.py tools/corpus.py
$emptyScripts = Join-Path $skillTarget 'scripts'
if ((Test-Path -LiteralPath $emptyScripts) -and -not (Get-ChildItem -LiteralPath $emptyScripts -Force)) {
  Remove-Item -LiteralPath $emptyScripts
}
```

Only the validated generated `__pycache__` directory is removed. Do not run any command against `doc/`.

- [ ] **Step 3: Update the corpus test module path**

Change the constant in `tests/test_corpus.py` to:

```python
MODULE_PATH = Path(__file__).parents[1] / "tools" / "corpus.py"
```

- [ ] **Step 4: Run layout and corpus tests and verify GREEN**

Run:

```powershell
python -B -m unittest tests.test_repository tests.test_corpus -v
```

Expected: 18 tests pass: 1 repository-layout test plus the existing 17 corpus tests.

- [ ] **Step 5: Run the official Skill validator at the new path**

Run:

```powershell
$codexRoots = @()
if ($env:CODEX_HOME) { $codexRoots += $env:CODEX_HOME }
$codexRoots += Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'
$skillValidator = $codexRoots |
  ForEach-Object { Join-Path $_ 'skills/.system/skill-creator/scripts/quick_validate.py' } |
  Where-Object { Test-Path -LiteralPath $_ } |
  Select-Object -First 1
if (-not $skillValidator) { throw 'Codex skill-creator quick_validate.py was not found' }
python $skillValidator skills/research-writing
```

Expected:

```text
Skill is valid!
```

- [ ] **Step 6: Commit the boundary migration**

```powershell
git add -- skills tools evals tests/test_corpus.py
git commit -m "refactor: isolate runtime skill package"
```

## Task 3: Write Failing Release-Boundary Tests

**Files:**

- Modify: `tests/test_repository.py`

- [ ] **Step 1: Replace `tests/test_repository.py` with the expanded release specification**

Use this complete content:

```python
import subprocess
import sys
import tempfile
import unittest
import zipfile
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "research-writing"
TOOLS_DIR = ROOT / "tools"
MANIFEST = ROOT / "release-manifest.txt"


class RepositoryLayoutTest(unittest.TestCase):
    def test_runtime_skill_is_isolated_from_development_artifacts(self):
        self.assertTrue(SKILL_DIR.is_dir())
        self.assertTrue((SKILL_DIR / "SKILL.md").is_file())
        self.assertFalse((ROOT / "research-writing").exists())
        self.assertTrue((TOOLS_DIR / "corpus.py").is_file())
        self.assertTrue((ROOT / "evals" / "rubric.md").is_file())
        self.assertFalse((SKILL_DIR / "evals").exists())
        self.assertFalse((SKILL_DIR / "scripts" / "corpus.py").exists())

    def test_release_manifest_is_an_explicit_allowlist(self):
        entries = [
            line.strip()
            for line in MANIFEST.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(entries, sorted(entries))
        self.assertEqual(len(entries), len(set(entries)))
        for entry in entries:
            path = Path(entry)
            self.assertFalse(path.is_absolute())
            self.assertTrue((ROOT / path).is_file(), entry)
            self.assertFalse(entry.startswith(("doc/", "ara/", "evals/", "tests/")))
            self.assertNotEqual(path.suffix.lower(), ".pdf")

        package_files = {
            path.relative_to(ROOT).as_posix()
            for path in SKILL_DIR.rglob("*")
            if path.is_file()
        }
        manifest_package_files = {
            entry for entry in entries if entry.startswith("skills/research-writing/")
        }
        self.assertEqual(package_files, manifest_package_files)

    def test_repository_validator_accepts_the_repository(self):
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "validate_repository.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_license_is_the_canonical_apache_2_text(self):
        digest = sha256((ROOT / "LICENSE").read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
        )

    def test_release_builder_is_deterministic_and_allowlisted(self):
        with tempfile.TemporaryDirectory() as raw:
            first = Path(raw) / "first.zip"
            second = Path(raw) / "second.zip"
            for output in (first, second):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(TOOLS_DIR / "build_release.py"),
                        "--output",
                        str(output),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                infos = archive.infolist()

        self.assertIn("research-writing/SKILL.md", names)
        self.assertIn("LICENSE", names)
        self.assertIn("THIRD_PARTY_NOTICES.md", names)
        self.assertFalse(any(name.startswith(("doc/", "ara/", "evals/", "tests/")) for name in names))
        self.assertFalse(any(name.lower().endswith(".pdf") for name in names))
        self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in infos))
        self.assertTrue(all(info.create_system == 3 for info in infos))
        self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED for info in infos))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the expanded test and verify RED**

Run:

```powershell
python -B -m unittest tests.test_repository -v
```

Expected failures:

- `release-manifest.txt` does not exist;
- `tools/validate_repository.py` does not exist;
- `tools/build_release.py` does not exist;
- `LICENSE` does not exist.

- [ ] **Step 3: Commit the failing release specification**

```powershell
git add -- tests/test_repository.py
git commit -m "test: specify deterministic release boundary"
```

## Task 4: Implement the Deterministic Validator and Release Builder

**Files:**

- Create: `tools/validate_repository.py`
- Create: `tools/build_release.py`
- Create: `release-manifest.txt`
- Create: `LICENSE`
- Create: `THIRD_PARTY_NOTICES.md`
- Create: `requirements.txt`
- Create: `.gitattributes`
- Modify: `.gitignore`

- [ ] **Step 1: Add bounded dependencies**

Create `requirements.txt` with:

```text
PyMuPDF>=1.27,<2
PyYAML>=6,<7
requests>=2.32,<3
```

- [ ] **Step 2: Add the exact release allowlist**

Create `release-manifest.txt` with sorted entries:

```text
LICENSE
THIRD_PARTY_NOTICES.md
skills/research-writing/SKILL.md
skills/research-writing/agents/openai.yaml
skills/research-writing/assets/evidence-ledger.csv
skills/research-writing/assets/writing-brief.md
skills/research-writing/references/evidence-and-integrity.md
skills/research-writing/references/revision-and-style.md
skills/research-writing/references/section-guides.md
skills/research-writing/references/writing-workflow.md
```

Task 8 adds `source-foundations.md` to both the package and this manifest in the same GREEN change.

- [ ] **Step 3: Create `tools/validate_repository.py`**

Use this implementation:

```python
from __future__ import annotations

import re
import sys
from pathlib import Path, PurePosixPath

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "research-writing"
MANIFEST = ROOT / "release-manifest.txt"
ALLOWED_ROOT_RELEASE_FILES = {"LICENSE", "THIRD_PARTY_NOTICES.md"}
FORBIDDEN_PREFIXES = ("doc/", "ara/", "evals/", "tests/")
FORBIDDEN_PACKAGE_PARTS = {"__pycache__"}
LOCAL_ABSOLUTE_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]"),
    re.compile(r"\\\\[^\\\s]+\\"),
    re.compile(r"(?<!:)(?:/Users/|/home/|/tmp/|/mnt/[A-Za-z]/)"),
)


def manifest_entries(root: Path = ROOT) -> list[str]:
    path = root / "release-manifest.txt"
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must contain YAML frontmatter")
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError("SKILL.md frontmatter must be a mapping")
    return metadata, match.group(2)


def validate_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    skill_dir = root / "skills" / "research-writing"
    skill_path = skill_dir / "SKILL.md"

    if not skill_path.is_file():
        return ["missing skills/research-writing/SKILL.md"]
    if (root / "research-writing").exists():
        errors.append("legacy research-writing/ path still exists")
    if (skill_dir / "evals").exists():
        errors.append("evals must not be bundled in the Skill")
    if (skill_dir / "scripts" / "corpus.py").exists():
        errors.append("corpus.py must not be bundled in the Skill")

    skill_text = skill_path.read_text(encoding="utf-8")
    try:
        metadata, body = split_frontmatter(skill_text)
    except (ValueError, yaml.YAMLError) as exc:
        errors.append(str(exc))
        metadata, body = {}, ""

    if set(metadata) != {"name", "description"}:
        errors.append("SKILL.md frontmatter must contain only name and description")
    if metadata.get("name") != "research-writing":
        errors.append("Skill name must be research-writing")
    description = metadata.get("description")
    if not isinstance(description, str) or not description.startswith("Use when "):
        errors.append("Skill description must start with 'Use when '")
    elif len(description) > 1024:
        errors.append("Skill description exceeds 1024 characters")

    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
        target = link.split(maxsplit=1)[0]
        if "://" in target or target.startswith(("#", "mailto:")):
            continue
        destination = target.split("#", 1)[0]
        if destination and not (skill_dir / destination).is_file():
            errors.append(f"broken Skill reference: {target}")

    for path in sorted(skill_dir.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            errors.append(f"symlink bundled in Skill: {relative}")
            continue
        if not path.is_file():
            continue
        if FORBIDDEN_PACKAGE_PARTS.intersection(path.parts) or path.suffix.lower() in {
            ".pyc",
            ".pyo",
        }:
            errors.append(f"generated cache bundled in Skill: {relative}")
        if path.suffix.lower() == ".pdf":
            errors.append(f"PDF bundled in Skill: {relative}")
        if path.suffix.lower() in {".md", ".csv", ".yaml", ".yml", ".txt"}:
            text = path.read_text(encoding="utf-8")
            if any(pattern.search(text) for pattern in LOCAL_ABSOLUTE_PATTERNS):
                errors.append(f"local absolute path in Skill: {relative}")

    try:
        entries = manifest_entries(root)
    except FileNotFoundError:
        return errors + ["missing release-manifest.txt"]
    if entries != sorted(entries):
        errors.append("release manifest entries must be sorted")
    if len(entries) != len(set(entries)):
        errors.append("release manifest contains duplicates")

    for entry in entries:
        relative = PurePosixPath(entry)
        if "\\" in entry or relative.is_absolute() or ".." in relative.parts:
            errors.append(f"unsafe release path: {entry}")
            continue
        if entry.startswith(FORBIDDEN_PREFIXES) or relative.suffix.lower() == ".pdf":
            errors.append(f"forbidden release entry: {entry}")
        if not (
            entry in ALLOWED_ROOT_RELEASE_FILES
            or entry.startswith("skills/research-writing/")
        ):
            errors.append(f"entry outside release boundary: {entry}")
        if not root.joinpath(*relative.parts).is_file():
            errors.append(f"missing release entry: {entry}")

    package_files = {
        path.relative_to(root).as_posix()
        for path in skill_dir.rglob("*")
        if path.is_file()
    }
    manifest_package_files = {
        entry for entry in entries if entry.startswith("skills/research-writing/")
    }
    if package_files != manifest_package_files:
        missing = sorted(package_files - manifest_package_files)
        extra = sorted(manifest_package_files - package_files)
        errors.append(f"release package mismatch; missing={missing}; extra={extra}")

    openai_path = skill_dir / "agents" / "openai.yaml"
    try:
        openai_data = yaml.safe_load(openai_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, yaml.YAMLError) as exc:
        errors.append(f"invalid agents/openai.yaml: {exc}")
        openai_data = {}
    interface = openai_data.get("interface", {}) if isinstance(openai_data, dict) else {}
    required_interface = {"display_name", "short_description", "default_prompt"}
    if not isinstance(interface, dict):
        errors.append("openai.yaml interface must be a mapping")
        interface = {}
    elif set(interface) != required_interface:
        errors.append("openai.yaml interface must contain display_name, short_description, and default_prompt")
    short_description = interface.get("short_description", "")
    if not isinstance(short_description, str) or not 25 <= len(short_description) <= 64:
        errors.append("openai.yaml short_description must contain 25-64 characters")
    if "$research-writing" not in interface.get("default_prompt", ""):
        errors.append("openai.yaml default_prompt must mention $research-writing")

    return errors


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Create `tools/build_release.py`**

Use this implementation:

```python
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path, PurePosixPath

from validate_repository import ROOT, manifest_entries, validate_repository


FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def archive_name(entry: str) -> str:
    path = PurePosixPath(entry)
    if path.parts[:2] == ("skills", "research-writing"):
        return PurePosixPath("research-writing", *path.parts[2:]).as_posix()
    return path.as_posix()


def build_release(output: Path) -> Path:
    errors = validate_repository(ROOT)
    if errors:
        raise ValueError("; ".join(errors))

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for entry in manifest_entries(ROOT):
            source = ROOT / entry
            info = zipfile.ZipInfo(archive_name(entry), FIXED_TIMESTAMP)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the allowlisted research-writing Skill release")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / "research-writing.zip",
    )
    args = parser.parse_args(argv)
    try:
        output = build_release(args.output)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Add license and third-party boundary files**

Create `LICENSE` using the unmodified Apache License, Version 2.0 text published at:

```text
https://www.apache.org/licenses/LICENSE-2.0.txt
```

The file must begin with:

```text
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/
```

and end with the canonical `END OF TERMS AND CONDITIONS` appendix text.

Preserve the official LF bytes and verify:

```powershell
(Get-FileHash -LiteralPath 'LICENSE' -Algorithm SHA256).Hash.ToLowerInvariant()
```

Expected:

```text
cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30
```

Create `THIRD_PARTY_NOTICES.md` with these exact policy statements:

```markdown
# Third-Party Notices

The Apache License 2.0 applies only to original code, Skill instructions, templates, tests, and documentation authored for this repository.

The files under `doc/`, supplied PDFs, downloaded documents, and third-party source material are not licensed under the repository's Apache-2.0 license. They are research inputs and are excluded from the supported release artifact.

Four tracked files under `doc/source-index/` contain extracted third-party page context. This task does not edit or untrack them. The allowlisted release excludes them; publishing or relicensing the complete Git history requires a separate rights review.

`writing words.pdf` is a restricted local copy of the Manchester Academic Phrasebank Enhanced Edition. Its body, phrase lists, tables, examples, and derivatives are not included in the Skill or release. The lawful public entry point recorded by this project is <https://www.phrasebank.manchester.ac.uk/>.

`skills/research-writing/references/source-foundations.md` contains original procedural synthesis, bibliographic facts, page pointers, and canonical links. It does not redistribute the referenced handbooks.

Downloading a document does not establish redistribution rights. Contributors must not add source PDFs or substantial source excerpts to the release manifest.
```

- [ ] **Step 6: Add export exclusions and ignore generated releases**

Create `.gitattributes`:

```gitattributes
LICENSE text eol=lf
THIRD_PARTY_NOTICES.md text eol=lf
skills/research-writing/** text eol=lf
ara/ export-ignore
doc/ export-ignore
docs/superpowers/ export-ignore
evals/ export-ignore
tests/ export-ignore
tools/ export-ignore
```

Append to `.gitignore`:

```gitignore

# Generated allowlisted release artifacts.
dist/
*.zip
```

- [ ] **Step 7: Run the release tests and verify GREEN**

Run:

```powershell
python -B -m unittest tests.test_repository -v
```

Expected: all current repository and corpus tests pass. No source/schema test exists yet; Task 6 introduces that next RED immediately before Tasks 7-8 establish the behavioral baseline and implementation.

- [ ] **Step 8: Commit the deterministic release infrastructure**

```powershell
git add -- .gitattributes .gitignore LICENSE THIRD_PARTY_NOTICES.md requirements.txt release-manifest.txt tools/validate_repository.py tools/build_release.py
git commit -m "feat: add deterministic skill release boundary"
```

## Task 5: Add the Open-Source Repository Shell and CI

**Files:**

- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `.github/workflows/ci.yml`
- Modify: `tests/test_repository.py`

- [ ] **Step 1: Add failing shell-document and CI tests**

Append this method to `RepositoryLayoutTest` in `tests/test_repository.py`:

```python
    def test_open_source_repository_shell_is_complete(self):
        for relative in (
            "README.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "THIRD_PARTY_NOTICES.md",
            "requirements.txt",
            ".github/workflows/ci.yml",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for heading in (
            "# Oh My Research",
            "## Install the Skill",
            "## Use",
            "## Source Foundations",
            "## Validation",
            "## Release Boundary",
            "## Evaluation Scope",
            "## License",
        ):
            self.assertIn(heading, readme)

        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("python -B -m unittest discover -s tests -v", workflow)
        self.assertIn("python tools/validate_repository.py", workflow)
        self.assertIn("python tools/build_release.py", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("actions/download-artifact@v4", workflow)
        self.assertIn("Compare Linux and Windows release bytes", workflow)
```

Run:

```powershell
python -B -m unittest tests.test_repository.RepositoryLayoutTest.test_open_source_repository_shell_is_complete -v
```

Expected: FAIL because `README.md` does not exist.

- [ ] **Step 2: Create `README.md` with the approved repository contract**

Write concise original prose under these exact sections:

```markdown
# Oh My Research

An open-source, evidence-grounded research-writing Skill. The first release helps an agent plan, draft, revise, compress, and audit academic or technical manuscripts without making the prose stronger than the evidence.

V1 deliberately ships a portable writing Skill, not an MCP server, persistent harness, autonomous research runtime, citation manager, or statistical package. Those components should be added only after a demonstrated use case requires them.

## Install the Skill

Copy `skills/research-writing/` to the host's Skill directory as `research-writing/`. For Codex, use `$CODEX_HOME/skills/research-writing/` when `CODEX_HOME` is set; otherwise use `~/.codex/skills/research-writing/`.

## Use

Invoke it explicitly with a prompt such as: `Use $research-writing to turn these notes and results into a traceable paper outline.`

The Skill supports proportional copyediting, shortening, section drafting, full-paper outlining, citation/integrity audits, and evidence-ledger construction. It does not fabricate missing research facts or citations.

## Repository Layout

`skills/research-writing/` is the only installable Skill. `tools/`, `tests/`, and `evals/` support development. `ara/` records research provenance. `doc/` is a local evidence corpus and is not part of the licensed release.

## Source Foundations

The writing rules are original synthesis grounded in multiple supplied PDFs and verified extension documents. See `skills/research-writing/references/source-foundations.md` for principle-to-page-to-rule provenance and `docs/corpus-synthesis.md` for the broader corpus overview.

## Validation

```powershell
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
python tools/validate_repository.py
python tools/build_release.py
```

The complete local corpus check is optional because public CI does not contain the local PDFs:

```powershell
python tools/corpus.py verify --index doc/source-index/inventory.json --doc doc
```

## Release Boundary

Build releases only with `python tools/build_release.py`. The builder reads `release-manifest.txt`; copying or compressing the working directory is unsupported. The release excludes `doc/`, `ara/`, tests, evaluations, local absolute paths, and PDFs.

The supported open-source distribution is the allowlisted release artifact. Four tracked files under `doc/source-index/` retain third-party page context; publishing the complete Git history requires a separate rights review and is not authorized by the Apache-2.0 license on original project material.

## Evaluation Scope

The original four fixed cases improved from 37/64 to 58/64 and from two critical failures to zero. These are smoke evaluations of specific failure modes, not evidence of general model superiority. Raw cases, outputs, scoring, and limitations live under `evals/`.

## Contributing

See `CONTRIBUTING.md`. Skill behavior changes require a failing static or behavioral test first, followed by forward testing on the unchanged case.

## Security

See `SECURITY.md`. Do not post confidential manuscripts, unpublished results, credentials, or restricted source material in public reports.

## License

Original project material is licensed under Apache License 2.0. Third-party research inputs are excluded; see `THIRD_PARTY_NOTICES.md`.
```

- [ ] **Step 3: Create `CONTRIBUTING.md`**

Include these enforceable rules:

```markdown
# Contributing

## Development Setup

Use Python 3.12 and install `requirements.txt`. Run the complete unit suite, repository validator, and release builder before submitting a change.

## Skill Changes

Follow RED-GREEN-REFACTOR. Add a failing static test or a fresh-agent baseline before changing Skill behavior. Preserve raw evaluation output, use the existing rubric, and do not rewrite a case after seeing the forward result.

Keep `SKILL.md` focused on trigger routing, hard safeguards, the minimal workflow, and the output contract. Put detailed, phase-specific, or source-heavy guidance in a directly linked reference.

## Source and Copyright Rules

Do not add PDFs, substantial excerpts, phrase lists, copied handbook tables, unknown mirrors, or material whose redistribution status is unclear. Prefer bibliographic facts, page pointers, canonical URLs, and original procedural synthesis.

Do not modify `doc/` as part of ordinary repository changes. Full local-corpus maintenance is a separate, explicitly authorized workflow.

## Pull Request Checklist

- Tests demonstrate the intended failure before the change and pass afterward.
- `python tools/validate_repository.py` passes.
- `python tools/build_release.py` creates an allowlisted archive.
- The Skill package contains no development-only artifact or local absolute path.
- New writing rules identify their source basis and applicability boundary.
- Evaluation claims remain bounded to the tested cases.
```

- [ ] **Step 4: Create `SECURITY.md`**

Use:

```markdown
# Security Policy

Report vulnerabilities through the repository host's private security-advisory mechanism. If private reporting is unavailable, contact the maintainers without attaching confidential manuscripts, credentials, unpublished results, or restricted PDFs.

Security reports should include the affected revision, reproduction steps using synthetic data, impact, and the smallest safe artifact needed to reproduce the issue.

Public issues are appropriate for non-sensitive validation bugs. Prompt-injection payloads, leaked credentials, private research data, and licensing incidents must remain private until triaged.
```

- [ ] **Step 5: Create cross-platform CI**

Create `.github/workflows/ci.yml`:

```yaml
name: ci

on:
  push:
  pull_request:

jobs:
  validate:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
      - name: Install dependencies
        run: python -m pip install -r requirements.txt
      - name: Run unit tests
        run: python -B -m unittest discover -s tests -v
      - name: Validate repository
        run: python tools/validate_repository.py
      - name: Build allowlisted Skill release
        run: python tools/build_release.py
      - name: List release contents
        run: python -m zipfile -l dist/research-writing.zip
      - name: Upload release for cross-platform comparison
        uses: actions/upload-artifact@v4
        with:
          name: release-${{ runner.os }}
          path: dist/research-writing.zip
          if-no-files-found: error
          retention-days: 1

  compare-release:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - name: Download platform releases
        uses: actions/download-artifact@v4
        with:
          pattern: release-*
          path: artifacts
          merge-multiple: false
      - name: Compare Linux and Windows release bytes
        run: >-
          python -c "from hashlib import sha256; from pathlib import Path;
          files=sorted(Path('artifacts').glob('*/research-writing.zip'));
          assert len(files)==2, files;
          payloads=[p.read_bytes() for p in files];
          assert payloads[0]==payloads[1], [(str(p), sha256(data).hexdigest()) for p,data in zip(files,payloads)];
          print(sha256(payloads[0]).hexdigest())"
```

- [ ] **Step 6: Run the shell test and YAML parse check**

Run:

```powershell
python -B -m unittest tests.test_repository.RepositoryLayoutTest.test_open_source_repository_shell_is_complete -v
python -c "from pathlib import Path; import yaml; yaml.safe_load(Path('.github/workflows/ci.yml').read_text(encoding='utf-8')); print('CI YAML valid')"
```

Expected:

```text
OK
CI YAML valid
```

- [ ] **Step 7: Commit the repository shell**

```powershell
git add -- README.md CONTRIBUTING.md SECURITY.md .github/workflows/ci.yml tests/test_repository.py
git commit -m "docs: add open-source repository shell"
```

## Task 6: Establish RED for Source Provenance and the Canonical Ledger

**Files:**

- Modify: `tests/test_repository.py`

- [ ] **Step 1: Add the source-matrix and ledger-schema tests**

Add `import csv` with the standard-library imports. Insert this class immediately before the final `if __name__ == "__main__":` block:

```python
class SkillSchemaTest(unittest.TestCase):
    def test_evidence_ledger_uses_the_canonical_schema(self):
        expected = [
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
        with (SKILL_DIR / "assets" / "evidence-ledger.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            rows = list(csv.reader(stream))
        self.assertEqual(rows[0], expected)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[1]), len(expected))

    def test_source_foundations_are_page_traceable(self):
        text = (SKILL_DIR / "references" / "source-foundations.md").read_text(
            encoding="utf-8"
        )

        def cells(line: str) -> list[str]:
            return [cell.strip() for cell in line.strip().strip("|").split("|")]

        table_lines = [line for line in text.splitlines() if line.startswith("|")]
        self.assertGreaterEqual(len(table_lines), 16)
        expected_header = [
            "Principle",
            "PDF page basis",
            "Source type",
            "Skill rule",
            "Applicability boundary",
            "Official or canonical URL",
        ]
        self.assertEqual(cells(table_lines[0]), expected_header)
        data_rows = [cells(line) for line in table_lines[2:]]
        for row in data_rows:
            self.assertEqual(len(row), len(expected_header), row)
            self.assertRegex(row[1], r"PDF pp?\.\d")
            self.assertIn(
                row[2],
                {
                    "Integrity basis",
                    "Workflow guidance",
                    "Style heuristic",
                    "Field guidance",
                    "Workflow guidance plus integrity basis",
                    "Workflow and field guidance",
                    "Style and field guidance",
                    "Workflow and style guidance",
                },
            )
            self.assertGreaterEqual(len(row[3]), 40)
            self.assertGreaterEqual(len(row[4]), 30)
            self.assertTrue("https://" in row[5] or "not verified" in row[5].lower())

        for marker in (
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
            "Technical Writing (updated).pdf",
            "https://www.phrasebank.manchester.ac.uk/",
            "Restricted-source boundary",
        ):
            self.assertIn(marker, text)
```

- [ ] **Step 2: Run the schema tests and verify RED**

Run:

```powershell
python -B -m unittest tests.test_repository.SkillSchemaTest -v
```

Expected: two failures. The current ledger header is not canonical and `source-foundations.md` does not exist.

- [ ] **Step 3: Commit the failing schema tests**

```powershell
git add -- tests/test_repository.py
git commit -m "test: specify source-grounded evidence schema"
```

## Task 7: Establish Behavioral RED for the Skill Refactor

**Files:**

- Create: `evals/cases/05-source-foundations.md`
- Create: `evals/cases/06-genre-flexibility.md`
- Create: `evals/cases/07-proportional-edit.md`
- Create: `evals/baseline/05-source-foundations.md`
- Create: `evals/baseline/06-genre-flexibility.md`
- Create: `evals/baseline/07-proportional-edit.md`
- Create: `evals/run-metadata.md`

- [ ] **Step 1: Create the source-foundation retrieval case**

```markdown
# Case 05: Source Foundations

Use only the bundled `research-writing` Skill package. Explain why the Skill treats citation and evidence integrity as hard gates but treats voice, section order, and information-structure advice as adaptable guidance. Cite at least four bundled source entries with exact PDF page pointers, including one source that warns against fixed writing rules. Do not inspect files outside the Skill package.
```

- [ ] **Step 2: Create the genre-flexibility pressure case**

```markdown
# Case 06: Genre Flexibility Under Authority Pressure

The senior author insists that every paper must use a problem-gap-insight-contribution story. The actual manuscript is an exact replication attempt: it introduces no new method, uses the published benchmark and protocol, does not reproduce the reported gain, includes three random seeds, and has no significance test. Produce a six-section outline and one sentence explaining whether to follow the demanded story. Do not invent a contribution, mechanism, or completed analysis.
```

- [ ] **Step 3: Create the proportional-edit regression case**

```markdown
# Case 07: Proportional One-Sentence Edit

Copyedit the sentence below for clarity without changing its claim or adding verification commentary. Return only the revised sentence.

> Across three runs, the newer configuration was associated with lower latency, although the experiment did not control hardware load.
```

- [ ] **Step 4: Run fresh agents against the pre-refactor Skill**

Resolve the active checkout paths first:

```powershell
$skillPath = (Resolve-Path 'skills/research-writing').Path
$case05 = (Resolve-Path 'evals/cases/05-source-foundations.md').Path
$case06 = (Resolve-Path 'evals/cases/06-genre-flexibility.md').Path
$case07 = (Resolve-Path 'evals/cases/07-proportional-edit.md').Path

"Use `$research-writing at $skillPath to complete $case05. Return the requested artifact only."
"Use `$research-writing at $skillPath to complete $case06. Return the requested artifact only."
"Use `$research-writing at $skillPath to complete $case07. Return the requested artifact only."
```

Launch three fresh agents using the three printed requests exactly.

Launch each with no inherited conversation turns. Do not tell the agents the expected answer, identified defect, intended fix, or scoring decision. Instruct them not to inspect `evals/baseline/`, `evals/forward/`, `evals/runs/`, `evals/comparison.md`, `docs/superpowers/`, or another agent's output. Run each case in an independent agent context and preserve only the returned artifact.

Before saving results, run `git rev-parse HEAD` and record the printed hash exactly. Save each raw response verbatim under the matching `evals/baseline/` path with four metadata fields: run date `2026-08-06`, the exact printed Skill revision, the actual model identifier when exposed (otherwise the literal text `not exposed by runner`), and the exact case path. Follow those fields with `## Raw Output` and the verbatim response. Do not leave instructional tokens or synthetic values in the file.

- [ ] **Step 5: Confirm behavioral RED without changing the cases**

Expected Case 05 failure: the pre-refactor Skill cannot retrieve four bundled page-level source entries because the reference does not exist yet. If a fresh agent unexpectedly satisfies the case, preserve the raw pass, verify that it did not inspect files outside the package or invent page pointers, and treat the observed behavior—not the expectation—as the baseline.

Required observed failure for Case 06: record whether the mandatory story instruction causes an artificial “insight” or “contribution,” or otherwise fails to state that genre and evidence override the senior author's universal rule. If the current output unexpectedly passes, retain that pass as regression evidence; the static RED at `SKILL.md`'s mandatory story wording remains the demonstrated defect.

Expected Case 07: pass. This is a regression guard proving the later refactor does not force a ledger or commentary onto a one-sentence output-only task.

- [ ] **Step 6: Document legacy evaluation provenance honestly**

Create `evals/run-metadata.md` stating:

- the original Cases 01-04 preserve raw baseline and forward outputs;
- their model name, decoding parameters, and exact runner command were not recorded and must not be reconstructed from memory;
- new Cases 05-07 record revision, date, model visibility, prompt path, and raw output;
- comparison totals are descriptive smoke-test results, not a benchmark or causal experiment.

- [ ] **Step 7: Commit behavioral RED evidence**

```powershell
git add -- evals/cases/05-source-foundations.md evals/cases/06-genre-flexibility.md evals/cases/07-proportional-edit.md evals/baseline/05-source-foundations.md evals/baseline/06-genre-flexibility.md evals/baseline/07-proportional-edit.md evals/run-metadata.md
git commit -m "test: capture repository skill refactor baseline"
```

## Task 8: Add Source Foundations and Align the Evidence Schema

**Files:**

- Create: `skills/research-writing/references/source-foundations.md`
- Create: `docs/skill-design-review.md`
- Modify: `skills/research-writing/assets/evidence-ledger.csv`
- Modify: `skills/research-writing/references/writing-workflow.md:11-21`
- Modify: `skills/research-writing/references/evidence-and-integrity.md:5-27`
- Modify: `release-manifest.txt`
- Modify: `tools/validate_repository.py`
- Read only: `doc/Technical Writing (updated).pdf`
- Read only: `doc/writing/How-to-write-a-great-research-paper.pdf`
- Read only: `doc/writing/895.pdf`
- Read only: `doc/writing/How_to_write_a_paper_2005.pdf`
- Read only: `doc/writing/gopen_swan.pdf`
- Read only: `doc/writing/knuth_mathematical_writing.pdf`
- Read only: `doc/writing/ScientificWritingGuide.pdf`
- Read only: `doc/writing/How-to-Write-Guide-v10-2014.pdf`
- Read only: `doc/writing/19900017394.pdf`
- Read only: `doc/research-methods/ReproducibilityChecklist.pdf`
- Read only: `doc/research-methods/on-being-a-scientist_-a-guide-to-responsible-conduct-in-research_-third-edition.pdf`

- [ ] **Step 1: Re-open the cited pages and audit every planned rule**

Read the exact page ranges named in the matrix below from the listed local PDFs. For every row, verify sentence by sentence that the cited pages support the operational rule at the stated level of authority. If a page supports only a narrower recommendation, narrow the rule or applicability boundary; if a page cannot be opened or checked, label that source location `not verified` instead of inferring from its title.

Do not open `doc/writing words.pdf`. Its body is outside the authorized evidence surface; use only previously recorded title/edition metadata and the official public Phrasebank URL.

This is a read-only source audit. Do not annotate, normalize, move, regenerate, or update metadata for any file under `doc/`.

- [ ] **Step 2: Write the source-foundations reference**

Use this structure and retain direct page-level rows for every listed source:

```markdown
# Source Foundations

Use this reference when explaining, auditing, or adapting the Skill's writing philosophy. It is an original synthesis of expert and institutional guidance, not a claim that every recommendation has controlled empirical validation.

## How to read the evidence

- `Integrity basis`: professional or institutional standards that justify hard safeguards.
- `Workflow guidance`: expert procedures that provide strong defaults but remain adaptable.
- `Style heuristic`: reader- or field-specific advice that must not become a universal rule.
- `Field guidance`: discipline- or venue-oriented advice whose scope must remain explicit.
- Combined labels mean that the row draws on more than one authority type; apply the strictest rule only to the integrity-bearing part.
- `Restricted metadata only`: bibliographic and licensing facts; do not load or reproduce source prose.

## Principle-to-source matrix

| Principle | PDF page basis | Source type | Skill rule | Applicability boundary | Official or canonical URL |
| --- | --- | --- | --- | --- | --- |
| Write while the research is forming | Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20; George M. Whitesides, *Writing a Paper*, PDF pp.1-3; Mike Ashby, *How to Write a Paper*, PDF pp.4-6 | Workflow guidance | Use an outline, concept sheet, or claim plan while the research is still taking shape | Early structure may expose missing work; never describe that work as completed | [Peyton Jones](https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/); [Whitesides](https://doi.org/10.1002/adma.200400767); [Ashby](https://www-mdp.eng.cam.ac.uk/web/library/enginfo/reports/How_to_write_a_paper_2005.pdf) |
| Make the central idea and claims explicit | Simon Peyton Jones, PDF pp.21-24; Machine Learning Reproducibility Checklist, PDF p.1 | Workflow guidance plus integrity basis | State each substantive claim in a form that can be supported, qualified, or refuted; give it a ledger row when the task is substantive | Theoretical, empirical, attributed, hypothetical, and proposed statements need different support | [Peyton Jones](https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/); [Checklist](https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf) |
| Design for the reader's current state | Simon Peyton Jones, PDF pp.36-45; Mike Ashby, PDF pp.4-8; Donald E. Knuth, Tracy Larrabee, and Paul M. Roberts, *Mathematical Writing*, PDF pp.4-7 | Workflow guidance | Select definitions, detail, examples, and order from what the intended reader knows and needs next | Reader orientation never permits evidence drift or hidden assumptions | [Peyton Jones](https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/); [Ashby](https://www-mdp.eng.cam.ac.uk/web/library/enginfo/reports/How_to_write_a_paper_2005.pdf); [Knuth et al.](https://jmlr.csail.mit.edu/reviewing-papers/knuth_mathematical_writing.pdf) |
| Give each section a rhetorical job | Whitesides, PDF pp.1-3; Ashby, PDF pp.8-14; Helsinki *Scientific Writing Guide*, PDF pp.6-14; Bates *How to Write Guide*, PDF pp.9-16 and 29-30 | Workflow and field guidance | Organize material by the job it must do for this artifact, then adapt headings and order to venue and genre | IMRaD is a useful convention, not a universal sequence | [Whitesides](https://doi.org/10.1002/adma.200400767); [Ashby](https://www-mdp.eng.cam.ac.uk/web/library/enginfo/reports/How_to_write_a_paper_2005.pdf); [Helsinki](https://www.cs.helsinki.fi/group/ese/ScientificWritingGuide.pdf); [Bates](https://www.bates.edu/biology/files/2010/06/How-to-Write-Guide-v10-2014.pdf) |
| Use information structure deliberately | George D. Gopen and Judith A. Swan, *The Science of Scientific Writing*, PDF pp.4-12 | Style heuristic | Diagnose subject-verb distance, topic continuity, old-to-new flow, and sentence stress during revision | PDF p.12 presents principles rather than algorithms; meaning and field convention take priority | [Gopen and Swan](https://www.gatsby.ucl.ac.uk/~pel/misc/gopen_swan.pdf) |
| Keep stylistic prescriptions conditional | `Technical Writing (updated).pdf`, PDF p.1; Helsinki guide, PDF p.2; Bates guide, PDF pp.5 and 59; Gopen and Swan, PDF p.12 | Style and field guidance | Treat voice, section order, wording, sentence length, and paragraph patterns as context-sensitive defaults | Venue rules, disciplinary practice, artifact type, and user intent override a generic preference | Technical Writing public origin not verified; [Helsinki](https://www.cs.helsinki.fi/group/ese/ScientificWritingGuide.pdf); [Bates](https://www.bates.edu/biology/files/2010/06/How-to-Write-Guide-v10-2014.pdf); [Gopen and Swan](https://www.gatsby.ucl.ac.uk/~pel/misc/gopen_swan.pdf) |
| Separate observation from interpretation | Helsinki guide, PDF pp.11-13; Bates guide, PDF pp.29-30 | Workflow guidance | State what was observed before explaining it, and attach validity or generalisability limits to the interpretation | Results and Discussion may share a section, but their logical roles remain distinct | [Helsinki](https://www.cs.helsinki.fi/group/ese/ScientificWritingGuide.pdf); [Bates](https://www.bates.edu/biology/files/2010/06/How-to-Write-Guide-v10-2014.pdf) |
| Make figures and statistical support carry explicit messages | Bates guide, PDF pp.9-16, 29-30, and 59 | Field guidance | Make each figure or table interpretable in context and connect reported statistical support to the claim it actually bears | Do not infer significance, robustness, or causality from an unreported analysis | [Bates](https://www.bates.edu/biology/files/2010/06/How-to-Write-Guide-v10-2014.pdf) |
| Do not make the record stronger than the data | *On Being a Scientist*, PDF pp.10 and 27-31 | Integrity basis | Never invent evidence or silently strengthen causality, generality, certainty, exclusions, or numerical precision | Applies to drafting, revision, figures, data handling, and compression | [On Being a Scientist](https://doi.org/10.17226/12192) |
| Verify source identity and local claim support separately | *On Being a Scientist*, PDF pp.48-49 | Integrity basis | Confirm both that a source exists and that the cited location supports the nearby statement | Prefer the original source over an unchecked secondary citation | [On Being a Scientist](https://doi.org/10.17226/12192) |
| Report enough method detail to evaluate and reproduce | *On Being a Scientist*, PDF pp.28-31; Machine Learning Reproducibility Checklist, PDF p.1 | Integrity basis | Report relevant assumptions, data, exclusions, dependencies, runs, measures, variation, and computing conditions | Requirements vary by study type; use `not-applicable` rather than silent omission | [On Being a Scientist](https://doi.org/10.17226/12192); [Checklist](https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf) |
| Correct the record and value coherent contribution over output count | *On Being a Scientist*, PDF pp.70 and 73 | Integrity basis | Surface material errors and organize a paper around a coherent contribution rather than manufacturing salable fragments | This does not forbid multiple papers when their questions and evidence genuinely differ | [On Being a Scientist](https://doi.org/10.17226/12192) |
| Compress without deleting meaning | NASA SP-7084, PDF pp.19 and 36-52; Gopen and Swan, PDF p.6 | Workflow and style guidance | Remove redundancy before qualifiers; use vigorous syntax contextually; preserve parallel relations and conclusion-changing limits | Brevity is not minimum word count, active voice is not mandatory, and sentence length alone does not determine clarity | [NASA SP-7084](https://ntrs.nasa.gov/citations/19900017394); [Gopen and Swan](https://www.gatsby.ucl.ac.uk/~pel/misc/gopen_swan.pdf) |
| Define notation and expose assumptions before relying on them | Knuth et al., PDF pp.4-7 and 114; `Technical Writing (updated).pdf`, PDF pp.6-8; Ashby, PDF p.14 | Workflow guidance plus integrity basis | Define terms and symbols, keep notation consistent, and state strong assumptions and conclusion-changing limitations | A forward definition is acceptable only when it reduces greater confusion; do not claim robustness to relaxed assumptions without evidence | [Knuth et al.](https://jmlr.csail.mit.edu/reviewing-papers/knuth_mathematical_writing.pdf); Technical Writing public origin not verified; [Ashby](https://www-mdp.eng.cam.ac.uk/web/library/enginfo/reports/How_to_write_a_paper_2005.pdf) |

Every row records page-level PDF provenance, the authority type, the operational Skill rule, its boundary, and the public location when one was verified. Treat an unavailable public origin as unavailable rather than substituting an unknown mirror.

- Manchester Academic Phrasebank public site: <https://www.phrasebank.manchester.ac.uk/>

Accessed 2026-08-06. URLs and licenses can change; verify the current official record before redistribution or formal citation.

## Restricted-source boundary

`writing words.pdf` is recorded only as restricted metadata. Do not load, quote, summarize its phrase lists, derive reusable templates from it, or include it in the release. Direct users to the official public Phrasebank site and its current terms.
```

- [ ] **Step 3: Replace the ledger with the canonical compact schema**

Use this exact CSV:

```csv
claim_id,section,claim_text,claim_type,polarity,scope,conditions,qualifiers,numeric_value,unit,denominator,comparison_or_baseline,evidence_id,evidence_location,evidence_summary,support_status,citation_status,limitation_or_gap,action
TEMPLATE-01,,Replace this instructional row before using the ledger.,proposal,neutral,,,,,,,,,,,not-applicable,not-required,,Create one row per substantive claim.
```

Add `skills/research-writing/references/source-foundations.md` to `release-manifest.txt` between `section-guides.md` and `writing-workflow.md`, preserving lexical sort order.

- [ ] **Step 4: Align the workflow reference**

Replace the status paragraph in `references/writing-workflow.md` with:

```markdown
For each row, record three independent dimensions:

- `claim_type`: `observation`, `source-report`, `interpretation`, `hypothesis`, or `proposal`;
- `support_status`: `verified`, `partial`, `pending-verification`, `gap`, or `not-applicable`;
- `citation_status`: `verified`, `pending-verification`, or `not-required`.

A row is not `verified` because its wording sounds plausible. Split compound claims until each row can be supported, qualified, or marked as a gap independently.

Record `polarity` as `positive`, `negative`, `neutral`, `mixed`, or `not-applicable`. Preserve `scope`, `conditions`, and `qualifiers` literally. For every number, keep `numeric_value`, `unit`, `denominator`, and `comparison_or_baseline` separate; do not compress them into an opaque note. Use `evidence_summary` only for a concise original description of what the cited location supports.
```

- [ ] **Step 5: Extend repository validation for the new schema and source matrix**

Add `import csv` to `tools/validate_repository.py` and define this constant after the existing validation constants:

```python
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
```

Insert these checks after the package/manifest equality check:

```python
    ledger_path = skill_dir / "assets" / "evidence-ledger.csv"
    with ledger_path.open(encoding="utf-8", newline="") as stream:
        ledger_rows = list(csv.reader(stream))
    if not ledger_rows or ledger_rows[0] != EXPECTED_LEDGER_HEADER:
        errors.append("evidence ledger header does not match canonical schema")
    elif len(ledger_rows) != 2 or len(ledger_rows[1]) != len(EXPECTED_LEDGER_HEADER):
        errors.append("evidence ledger must contain one complete instructional row")

    source_path = skill_dir / "references" / "source-foundations.md"
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append("missing references/source-foundations.md")
    else:
        table_lines = [line for line in source_text.splitlines() if line.startswith("|")]
        expected_source_header = [
            "Principle",
            "PDF page basis",
            "Source type",
            "Skill rule",
            "Applicability boundary",
            "Official or canonical URL",
        ]
        if len(table_lines) < 16:
            errors.append("source foundations must contain at least fourteen provenance rows")
        else:
            header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
            if header != expected_source_header:
                errors.append("source foundations table header is not canonical")
        for marker in (
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
            "Technical Writing (updated).pdf",
            "https://www.phrasebank.manchester.ac.uk/",
            "Restricted-source boundary",
        ):
            if marker not in source_text:
                errors.append(f"source foundation missing marker: {marker}")
```

- [ ] **Step 6: Align the integrity reference**

Add the same three-dimensional vocabulary to `references/evidence-and-integrity.md` and require a source-report to be attributed even when its source identity and local supporting passage are verified. Do not describe `inferred` or `proposed` as degrees of evidence support. Require number audits to compare polarity, numeric value, unit, denominator, and comparison/baseline independently before and after revision.

- [ ] **Step 7: Write the critical design review**

Create `docs/skill-design-review.md` with these sections and conclusions:

```markdown
# Research-Writing Skill Design Review

## Verdict

The V1 integrity core addresses the observed critical failures in its fixed smoke cases. That evidence is narrow: the repository boundary, source traceability, evidence vocabulary, and genre flexibility still required correction before public release.

## What remains hard-constrained

Citation identity, quotation fidelity, numbers, units, causal force, claim scope, and conclusion-changing limitations remain low-freedom rules because mistakes are difficult to detect after fluent prose is produced.

## What becomes adaptable

Problem-gap-contribution storytelling, IMRaD order, active voice, topic/stress-position heuristics, and section-level conventions become defaults selected by genre, venue, field, and user intent.

## Resolved design defects

Document the runtime/development split, canonical ledger schema, source-foundations matrix, allowlisted release, and genre-aware structure selection.

## Progressive-disclosure audit

The runtime package keeps only the concise trigger-time workflow, directly linked references, reusable assets, and product metadata. Corpus acquisition, evaluations, tests, release tooling, and provenance remain outside the Skill. The core routes to source foundations only for rationale or design-audit requests, so ordinary copyediting does not pay that context cost.

## Why V1 is a Skill, not a harness or MCP server

Writing guidance is primarily procedural knowledge plus reusable templates. V1 has no demonstrated need for a persistent service, remote tool protocol, background state, or autonomous multi-agent runtime. Adding those components now would increase permissions, dependencies, and maintenance without improving the tested writing cases.

## Known boundary

`doc/` remains untouched and outside the release. The four tracked source-index files require a separate rights review before publishing the complete Git history; this refactor licenses and supports the allowlisted Skill artifact, not the local evidence corpus.

## Evaluation limit

Fixed-case improvements show that the safeguards address observed failures. They do not establish universal writing-quality gains or controlled causal effectiveness.

## Remaining limitations

The source matrix is dominated by scientific and technical writing guidance, English-language conventions, and a small fixed evaluation set. The Skill does not validate statistics, retrieve paywalled sources, manage a bibliography database, or decide field-specific venue compliance without user-supplied rules. Future expansion should begin with a failing case, not feature accumulation.
```

- [ ] **Step 8: Run schema tests and repository validation**

Run:

```powershell
python -B -m unittest tests.test_repository.SkillSchemaTest.test_evidence_ledger_uses_the_canonical_schema -v
python -B -m unittest tests.test_repository.SkillSchemaTest.test_source_foundations_are_page_traceable -v
python -B -m unittest discover -s tests -v
python tools/validate_repository.py
python tools/build_release.py
```

Expected: both schema/source tests and the complete unit suite pass; validator prints `Repository validation passed.`; builder creates `dist/research-writing.zip`. No Skill-core behavior test is added until Task 9, immediately before that refactor.

- [ ] **Step 9: Commit source grounding and schema alignment**

```powershell
git add -- skills/research-writing/references/source-foundations.md skills/research-writing/assets/evidence-ledger.csv skills/research-writing/references/writing-workflow.md skills/research-writing/references/evidence-and-integrity.md docs/skill-design-review.md release-manifest.txt tools/validate_repository.py
git commit -m "docs: ground writing rules in source corpus"
```

## Task 9: Refactor the Runtime Skill and Forward-Test It

**Files:**

- Modify: `skills/research-writing/SKILL.md:12-141`
- Modify: `skills/research-writing/references/writing-workflow.md`
- Modify: `skills/research-writing/references/section-guides.md`
- Modify: `skills/research-writing/references/revision-and-style.md`
- Modify: `skills/research-writing/references/evidence-and-integrity.md`
- Verify or modify: `skills/research-writing/agents/openai.yaml`
- Modify: `tests/test_repository.py`
- Create: `evals/runs/2026-08-06-repository-refactor/01-outline.md`
- Create: `evals/runs/2026-08-06-repository-refactor/02-revision.md`
- Create: `evals/runs/2026-08-06-repository-refactor/03-integrity.md`
- Create: `evals/runs/2026-08-06-repository-refactor/04-compression.md`
- Create: `evals/runs/2026-08-06-repository-refactor/05-source-foundations.md`
- Create: `evals/runs/2026-08-06-repository-refactor/06-genre-flexibility.md`
- Create: `evals/runs/2026-08-06-repository-refactor/07-proportional-edit.md`
- Modify: `evals/run-metadata.md`
- Modify: `evals/comparison.md`

- [ ] **Step 1: Add the failing Skill-core contract test**

Insert this class before the final `if __name__ == "__main__":` block in `tests/test_repository.py`:

```python
class SkillBehaviorContractTest(unittest.TestCase):
    def test_skill_core_is_concise_source_routed_and_genre_aware(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        workflow = (SKILL_DIR / "references" / "writing-workflow.md").read_text(
            encoding="utf-8"
        )
        combined = skill + "\n" + workflow

        self.assertIn(
            "[references/source-foundations.md](references/source-foundations.md)",
            skill,
        )
        for field in ("claim_type", "support_status", "citation_status"):
            self.assertIn(field, combined)
        self.assertIn("pending-verification", combined)
        self.assertNotIn("partially supported, inferred, proposed, or a gap", combined)
        self.assertNotIn(
            "Mark each row `supported`, `qualified`, `gap`, `pending-verification`, or `not-applicable`",
            combined,
        )

        self.assertNotIn("### 3. Story", skill)
        self.assertNotIn("| Contribution paper |", skill)
        for artifact in (
            "Contribution paper",
            "Empirical study",
            "Replication or negative result",
            "Survey",
            "Methods or data paper",
            "Local revision",
        ):
            self.assertIn(artifact, workflow)
        self.assertIn("Never invent a contribution", combined)
        self.assertLessEqual(len(skill.split()), 700)
```

- [ ] **Step 2: Run the Skill-core contract and verify RED**

Run:

```powershell
python -B -m unittest tests.test_repository.SkillBehaviorContractTest -v
```

Expected: FAIL because the current core does not route to source foundations, mixes evidence dimensions, mandates `Story`, keeps the genre table out of the workflow reference, and exceeds 700 words.

- [ ] **Step 3: Add source-foundation routing**

Add this bullet under `Load only what the task needs`:

```markdown
- Read [references/source-foundations.md](references/source-foundations.md) when explaining, auditing, or adapting the Skill's writing philosophy; do not load it for ordinary drafting or revision.
```

- [ ] **Step 4: Replace the mixed evidence-status rule**

Replace the current rule that mixes `supported`, `inferred`, and `proposed` with:

```markdown
For each new or materially strengthened manuscript claim, record `claim_type`, `support_status`, and `citation_status` separately before presenting it as fact. Keep this record internal for a faithful copyedit unless missing support prevents a safe revision.
```

In the Ledger phase, define the allowed values explicitly:

```markdown
- `claim_type`: `observation`, `source-report`, `interpretation`, `hypothesis`, or `proposal`;
- `support_status`: `verified`, `partial`, `pending-verification`, `gap`, or `not-applicable`;
- `citation_status`: `verified`, `pending-verification`, or `not-required`.
```

- [ ] **Step 5: Replace the mandatory Story phase with genre-aware Structure selection**

Keep only this routing and safeguard in `SKILL.md`:

```markdown
### 3. Structure

Choose an argument pattern that matches the artifact, evidence, venue, and user intent. Read [references/writing-workflow.md](references/writing-workflow.md) for genre defaults. Never invent a contribution, taxonomy, experiment, mechanism, analysis, or result to satisfy a story template.
```

Move this table to the `Structure` section of `references/writing-workflow.md`:

```markdown
| Artifact | Useful default progression |
| --- | --- |
| Contribution paper | problem -> gap -> insight -> supported contribution |
| Empirical study | question -> design -> observation -> interpretation -> limits |
| Replication or negative result | prior claim -> replication design -> result -> agreement/discrepancy -> boundary |
| Survey | scope -> organizing lens -> synthesis -> unresolved questions |
| Methods or data paper | need -> artifact or method -> validation -> usage boundary |
| Local revision | preserve the supplied structure unless restructuring is requested |

Treat these as starting patterns, not required headings. Never invent a contribution, taxonomy, experiment, mechanism, or result to satisfy a story template.
```

- [ ] **Step 6: Remove duplicated detail while preserving tested safeguards**

Keep the following concepts in `SKILL.md` because they are tied to observed critical failures:

- no fabricated citations, facts, numbers, or results;
- no association-to-causation drift;
- meaning-atom preservation for substantive revision;
- proportional operating depth;
- output-only compliance;
- compression safety gate;
- completion check.

Move evidence-state tables, genre tables, phase detail, and repeated examples to directly linked references. Keep the core focused on trigger-time routing, non-negotiable integrity rules, proportional depth, the seven one-paragraph workflow phases, the output contract, and completion check. Target no more than 700 whitespace-delimited words without weakening the tested safeguards.

Run:

```powershell
$text = [IO.File]::ReadAllText((Resolve-Path 'skills/research-writing/SKILL.md').Path,[Text.Encoding]::UTF8)
$wordCount = ([regex]::Matches($text,'\S+')).Count
if ($wordCount -gt 700) { throw "SKILL.md exceeds 700 words: $wordCount" }
$wordCount
```

Expected: a value at or below 700.

- [ ] **Step 7: Make reference guidance explicitly conditional**

Update the references so that:

- `writing-workflow.md` uses `Structure`, not mandatory `Story`, and links claim rows to the canonical schema;
- `section-guides.md` says section names and order depend on venue, field, and artifact while retaining each section's rhetorical job;
- `revision-and-style.md` identifies active voice, topic/stress positions, sentence length, and paragraph patterns as diagnostic heuristics rather than universal rules;
- `evidence-and-integrity.md` retains strict citation, number, causal, limitation, and reproducibility checks.

Use these exact boundary statements near the start of the respective references:

```markdown
Section names and order are selected by venue, field, artifact, and user intent. Treat the patterns below as rhetorical jobs, not mandatory headings.
```

```markdown
Treat active voice, topic and stress positions, sentence length, and paragraph patterns as diagnostics. Apply them only when they improve reader comprehension without changing meaning or violating field convention.
```

```markdown
Integrity checks are low-freedom gates: citation identity, quotation fidelity, numbers, units, denominators, comparison baselines, causal force, claim scope, and conclusion-changing limitations must survive drafting and revision.
```

- [ ] **Step 8: Verify product metadata**

Set or verify these exact values; they remain accurate after the refactor:

```yaml
interface:
  display_name: "Research Writing"
  short_description: "Evidence-grounded academic writing workflow"
  default_prompt: "Use $research-writing to turn my research materials into a traceable paper draft."
```

Run:

```powershell
$codexRoots = @()
if ($env:CODEX_HOME) { $codexRoots += $env:CODEX_HOME }
$codexRoots += Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'
$skillValidator = $codexRoots |
  ForEach-Object { Join-Path $_ 'skills/.system/skill-creator/scripts/quick_validate.py' } |
  Where-Object { Test-Path -LiteralPath $_ } |
  Select-Object -First 1
if (-not $skillValidator) { throw 'Codex skill-creator quick_validate.py was not found' }
python $skillValidator skills/research-writing
python tools/validate_repository.py
```

Expected:

```text
Skill is valid!
Repository validation passed.
```

- [ ] **Step 9: Run Cases 05-07 with fresh agents**

Use the same prompts, no-history isolation, forbidden-path rules, and metadata format as Task 7. Save verbatim outputs as Cases 05-07 under `evals/runs/2026-08-06-repository-refactor/`. Add the exact run revision and model visibility to `evals/run-metadata.md`.

Required forward outcomes:

- Case 05 cites at least four bundled source entries with exact PDF page pointers and distinguishes integrity basis from adaptable style guidance.
- Case 06 refuses to manufacture a positive or methodological contribution, selects a replication/negative-result progression, and preserves the three-seed/no-significance-test boundary.
- Case 07 returns only one revised sentence and does not append a ledger, caveat list, or process commentary.

- [ ] **Step 10: Re-run the original four cases without mutating earlier evidence**

Run fresh agents on Cases 01-04 using the revised Skill and the same isolation rule. Save the raw outputs only as Cases 01-04 under `evals/runs/2026-08-06-repository-refactor/`; do not edit the existing `evals/forward/01-04` files. Score with the unchanged rubric and record the exact revision and model visibility.

Required: zero fabricated citations, zero association-to-causation conversions, zero material-limit removals, and zero undisclosed substantive revision drift.

- [ ] **Step 11: Append bounded comparison results**

Add a `## Repository Refactor Cases 05-07` section to `evals/comparison.md`. Report per-case observable outcomes, critical failures, and limitations. Do not add Cases 05-07 to the old `37/64 -> 58/64` total because the source-retrieval and genre cases exercise different prompts and extend the evaluation surface.

- [ ] **Step 12: Run all unit tests and commit the Skill refactor**

Run:

```powershell
python -B -m unittest discover -s tests -v
python tools/validate_repository.py
python tools/build_release.py
```

Expected: all tests pass, repository validation passes, and the release builder exits 0.

Commit:

```powershell
git add -- skills/research-writing tests/test_repository.py evals
git commit -m "feat: make research writing source-grounded and genre-aware"
```

## Task 10: Run Cross-Platform-Equivalent Verification and Protect the Corpus

**Files:**

- No planned source changes unless verification exposes a specific failure.

- [ ] **Step 1: Install from the declared dependency file**

Run:

```powershell
python -m pip install -r requirements.txt
```

Expected: exit 0 with PyMuPDF 1.x, PyYAML 6.x, and requests 2.x available.

- [ ] **Step 2: Run the complete deterministic suite**

Run:

```powershell
python -B -m unittest discover -s tests -v
python tools/validate_repository.py
$codexRoots = @()
if ($env:CODEX_HOME) { $codexRoots += $env:CODEX_HOME }
$codexRoots += Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'
$skillValidator = $codexRoots |
  ForEach-Object { Join-Path $_ 'skills/.system/skill-creator/scripts/quick_validate.py' } |
  Where-Object { Test-Path -LiteralPath $_ } |
  Select-Object -First 1
if (-not $skillValidator) { throw 'Codex skill-creator quick_validate.py was not found' }
python $skillValidator skills/research-writing
python tools/build_release.py --output dist/research-writing.zip
python -m zipfile -l dist/research-writing.zip
```

Verify from the output:

- zero test failures;
- `Repository validation passed.`;
- `Skill is valid!`;
- archive contains only `LICENSE`, `THIRD_PARTY_NOTICES.md`, and `research-writing/` package files;
- archive contains no PDF and no `doc/`, `ara/`, `evals/`, `tests/`, or `tools/` path.

- [ ] **Step 3: Run the optional local-corpus integrity check**

Run:

```powershell
python tools/corpus.py verify --index doc/source-index/inventory.json --doc doc
```

Expected:

```json
{"ok": true, "errors": []}
```

- [ ] **Step 4: Recompute and compare the `doc/` baseline**

Re-run the exact fingerprint command from Task 1.

Required exact result:

```text
files=83 bytes=222559046 metadata_sha256=7698527d65a098ecf449ddc34340b0c02cf5bc6d47931d93ef8b83407c59d7b9 content_metadata_sha256=5045a0e383ded4e474ee6976b21f246e766f6f22a8ff62be55cc2744e119ef59
```

The Task 1 command also compares every relative path, byte count, UTC timestamp, and file SHA-256 against `docs/superpowers/specs/2026-08-06-doc-baseline.tsv`. If any row or aggregate differs, stop and report the read-only comparison output. Do not restore, delete, move, or regenerate any `doc/` file without explicit user authorization.

- [ ] **Step 5: Inspect final repository state and release diff**

Run:

```powershell
$startRevision = git merge-base HEAD main
git status --short
git diff --check "$startRevision..HEAD"
git diff --name-status "$startRevision..HEAD"
git ls-files -- skills/research-writing tools tests evals docs .github README.md LICENSE CONTRIBUTING.md SECURITY.md THIRD_PARTY_NOTICES.md requirements.txt release-manifest.txt .gitattributes .gitignore
```

Expected: only intentional implementation changes are tracked; no unrelated file appears.

- [ ] **Step 6: Commit any verification-only corrections**

Only if fresh verification found a concrete defect, first add a failing test that reproduces it. Then patch only the files named by that test, run the full verification suite, stage those explicitly named test and implementation files, and commit with `git commit -m "fix: close repository validation gap"`. If no correction was required, do not create an empty commit.

- [ ] **Step 7: Prepare the completion report**

Report:

- final repository layout and installable Skill path;
- tests, validators, release build, and evaluation results with exact counts;
- the per-file and aggregate `doc/` fingerprints proving zero content or metadata change;
- the source-foundation design and its distinction between hard constraints and adaptable guidance;
- the known full-Git-history rights-review boundary;
- commit hashes created during implementation.
