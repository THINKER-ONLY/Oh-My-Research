import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from datetime import date
from hashlib import sha256
from pathlib import Path, PurePosixPath, PureWindowsPath

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "research-writing"
TOOLS_DIR = ROOT / "tools"
MANIFEST = ROOT / "release-manifest.txt"

SOURCE_FOUNDATION_HEADER = [
    "Principle",
    "Source type and authority",
    "Supplied PDF and page",
    "Verified extension document and location",
    "Skill rule",
    "Applicability or conflict",
    "Canonical URL",
    "Access date",
]
UPSTREAM_SOURCE_GAP = (
    "not verified: introducing/indexing supplied PDF and page are not recorded"
)
DIRECT_EXTENSION_MARKER = "not applicable: direct supplied-PDF evidence"
UNAVAILABLE_URL_MARKER = "not verified: canonical public URL unavailable"
DIRECT_URL_MARKER = "not applicable: canonical URL not verified"
UNAVAILABLE_DATE_MARKER = "not applicable: access date unavailable"

EXPECTED_SOURCE_CONTRIBUTIONS = [
    (
        "Write while the research is forming",
        "Simon Peyton Jones",
        "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20",
    ),
    (
        "Write while the research is forming",
        "George M. Whitesides",
        "George M. Whitesides, *Writing a Paper*, PDF pp.1-3",
    ),
    (
        "Write while the research is forming",
        "Mike Ashby",
        "Mike Ashby, *How to Write a Paper*, PDF pp.4-6",
    ),
    (
        "Make the central idea and claims explicit",
        "Simon Peyton Jones",
        "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.12-13 and 21-24",
    ),
    (
        "Make the central idea and claims explicit",
        "Machine Learning Reproducibility Checklist",
        "Machine Learning Reproducibility Checklist, PDF p.1",
    ),
    (
        "Design for the reader's current state",
        "Simon Peyton Jones",
        "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.36-45",
    ),
    (
        "Design for the reader's current state",
        "Mike Ashby",
        "Mike Ashby, *How to Write a Paper*, PDF pp.4-8",
    ),
    (
        "Design for the reader's current state",
        "Donald E. Knuth",
        "Donald E. Knuth, Tracy Larrabee, and Paul M. Roberts, *Mathematical Writing*, PDF pp.4-7",
    ),
    (
        "Give each section a rhetorical job",
        "George M. Whitesides",
        "George M. Whitesides, *Writing a Paper*, PDF pp.1-3",
    ),
    (
        "Give each section a rhetorical job",
        "Mike Ashby",
        "Mike Ashby, *How to Write a Paper*, PDF pp.4-14",
    ),
    (
        "Give each section a rhetorical job",
        "Helsinki",
        "Helsinki *Scientific Writing Guide*, PDF pp.2 and 6-14",
    ),
    (
        "Give each section a rhetorical job",
        "Bates",
        "Bates *How to Write Guide*, PDF pp.5, 9-16, and 29-30",
    ),
    (
        "Use information structure deliberately",
        "George D. Gopen",
        "George D. Gopen and Judith A. Swan, *The Science of Scientific Writing*, PDF pp.4-12",
    ),
    (
        "Keep stylistic prescriptions conditional",
        "Technical Writing (updated).pdf",
        "`Technical Writing (updated).pdf`, PDF p.1",
    ),
    (
        "Keep stylistic prescriptions conditional",
        "Helsinki",
        "Helsinki *Scientific Writing Guide*, PDF p.2",
    ),
    (
        "Keep stylistic prescriptions conditional",
        "Bates",
        "Bates *How to Write Guide*, PDF pp.5 and 59",
    ),
    (
        "Keep stylistic prescriptions conditional",
        "George D. Gopen",
        "George D. Gopen and Judith A. Swan, *The Science of Scientific Writing*, PDF pp.6 and 12",
    ),
    (
        "Separate observation from interpretation",
        "Helsinki",
        "Helsinki *Scientific Writing Guide*, PDF pp.11-13",
    ),
    (
        "Separate observation from interpretation",
        "Bates",
        "Bates *How to Write Guide*, PDF pp.29-30",
    ),
    (
        "Make figures and statistical support carry explicit messages",
        "Bates",
        "Bates *How to Write Guide*, PDF pp.9-16, 29-30, and 59",
    ),
    (
        "Do not make the record stronger than the data",
        "On Being a Scientist",
        "*On Being a Scientist*, PDF pp.10 and 27-31",
    ),
    (
        "Verify source identity and local claim support separately",
        "On Being a Scientist",
        "*On Being a Scientist*, PDF pp.48-49",
    ),
    (
        "Report enough method detail to evaluate and reproduce",
        "On Being a Scientist",
        "*On Being a Scientist*, PDF pp.28-31",
    ),
    (
        "Report enough method detail to evaluate and reproduce",
        "Machine Learning Reproducibility Checklist",
        "Machine Learning Reproducibility Checklist, PDF p.1",
    ),
    (
        "Disclose questionable exclusions and divide papers by contribution",
        "On Being a Scientist",
        "*On Being a Scientist*, PDF pp.70 and 73",
    ),
    (
        "Compress without deleting meaning",
        "NASA SP-7084",
        "NASA SP-7084, PDF pp.19 and 36-52",
    ),
    (
        "Compress without deleting meaning",
        "George D. Gopen",
        "George D. Gopen and Judith A. Swan, *The Science of Scientific Writing*, PDF p.6",
    ),
    (
        "Define notation and expose assumptions before relying on them",
        "Donald E. Knuth",
        "Donald E. Knuth, Tracy Larrabee, and Paul M. Roberts, *Mathematical Writing*, PDF pp.4-7 and 114",
    ),
    (
        "Define notation and expose assumptions before relying on them",
        "Technical Writing (updated).pdf",
        "`Technical Writing (updated).pdf`, PDF pp.6-8",
    ),
    (
        "Define notation and expose assumptions before relying on them",
        "Mike Ashby",
        "Mike Ashby, *How to Write a Paper*, PDF p.14",
    ),
]
EXPECTED_SOURCE_URLS = {
    "Simon Peyton Jones": "https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/",
    "George M. Whitesides": "https://doi.org/10.1002/adma.200400767",
    "Mike Ashby": "https://www-mdp.eng.cam.ac.uk/web/library/enginfo/reports/How_to_write_a_paper_2005.pdf",
    "Machine Learning Reproducibility Checklist": "https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf",
    "Donald E. Knuth": "https://jmlr.csail.mit.edu/reviewing-papers/knuth_mathematical_writing.pdf",
    "Helsinki": "https://www.cs.helsinki.fi/group/ese/ScientificWritingGuide.pdf",
    "Bates": "https://www.bates.edu/biology/files/2010/06/How-to-Write-Guide-v10-2014.pdf",
    "George D. Gopen": "https://www.gatsby.ucl.ac.uk/~pel/misc/gopen_swan.pdf",
    "On Being a Scientist": "https://doi.org/10.17226/12192",
    "NASA SP-7084": "https://ntrs.nasa.gov/citations/19900017394",
    "Technical Writing (updated).pdf": DIRECT_URL_MARKER,
}


class RepositoryLayoutTest(unittest.TestCase):
    def test_open_source_repository_shell_is_complete(self):
        for name in (
            "README.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "THIRD_PARTY_NOTICES.md",
            "requirements.txt",
            ".github/workflows/ci.yml",
        ):
            self.assertTrue((ROOT / name).is_file(), name)

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
        for expected in (
            "ubuntu-latest",
            "windows-latest",
            "python -B -m unittest discover -s tests -v",
            "python tools/validate_repository.py",
            "python tools/build_release.py",
            "actions/upload-artifact@v4",
            "actions/download-artifact@v4",
            "Compare Linux and Windows release bytes",
        ):
            self.assertIn(expected, workflow)
        for expected in (
            "permissions:",
            "contents: read",
            "persist-credentials: false",
        ):
            self.assertIn(expected, workflow)

        self.assertTrue((ROOT / "docs" / "corpus-synthesis.md").is_file())
        self.assertIn(
            "[source-foundations matrix]"
            "(skills/research-writing/references/source-foundations.md)",
            readme,
        )
        self.assertIn(
            "[docs/corpus-synthesis.md](docs/corpus-synthesis.md)",
            readme,
        )
        self.assertNotIn("when the V1 source audit lands", readme)
        self.assertNotIn("The writing rules will be grounded", readme)

        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("declared project requirements", contributing)
        self.assertNotIn("pinned project requirements", contributing)
        self.assertIn(
            "Add a failing static test or a fresh-agent baseline before changing "
            "Skill behavior.",
            contributing,
        )
        self.assertIn(
            "Preserve raw evaluation output, use the existing rubric, and do not "
            "rewrite a case after seeing the forward result.",
            contributing,
        )
        for expected in (
            "For Skill behavior changes, use RED-GREEN-REFACTOR:",
            "a failing static test or a fresh-agent baseline",
            "observe the RED result when applicable",
            "Ordinary documentation, security, and configuration changes need only "
            "their corresponding static contract tests.",
            "A behavior change has a failing static test or fresh-agent baseline, "
            "with its RED result observed when applicable; ordinary documentation, "
            "security, and configuration changes have the corresponding static "
            "contract test.",
        ):
            self.assertIn(expected, contributing)

        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        for expected in (
            "repository host",
            "`Security` tab",
            "private security advisory",
            "`Report a vulnerability`",
            "hosting profile",
            "private contact",
            "Sensitive events must not be disclosed publicly.",
        ):
            self.assertIn(expected, security)

    def copy_release_repository(self, raw):
        repository = Path(raw) / "repository"
        (repository / "tools").mkdir(parents=True)
        (repository / "skills").mkdir()
        shutil.copytree(SKILL_DIR, repository / "skills" / "research-writing")
        for name in (
            "LICENSE",
            "THIRD_PARTY_NOTICES.md",
            "release-manifest.txt",
        ):
            shutil.copy2(ROOT / name, repository / name)
        for name in ("build_release.py", "validate_repository.py"):
            shutil.copy2(TOOLS_DIR / name, repository / "tools" / name)
        return repository

    def windows_short_path(self, path):
        if os.name != "nt":
            self.skipTest("8.3 path aliases are Windows-specific")
        import ctypes
        import ctypes.wintypes

        get_short_path = ctypes.windll.kernel32.GetShortPathNameW
        get_short_path.argtypes = [
            ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.LPWSTR,
            ctypes.wintypes.DWORD,
        ]
        get_short_path.restype = ctypes.wintypes.DWORD
        buffer = ctypes.create_unicode_buffer(32768)
        length = get_short_path(str(path), buffer, len(buffer))
        if not length:
            self.skipTest(f"8.3 short path unavailable for {path}")
        short_path = Path(buffer.value)
        if short_path == path:
            self.skipTest(f"8.3 short path alias unavailable for {path}")
        return short_path

    def run_repository_validator(self, repository):
        return subprocess.run(
            [sys.executable, str(repository / "tools" / "validate_repository.py")],
            cwd=repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def run_release_builder(self, repository, output):
        return subprocess.run(
            [
                sys.executable,
                str(repository / "tools" / "build_release.py"),
                "--output",
                str(output),
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def write_manifest(self, repository, entries):
        (repository / "release-manifest.txt").write_text(
            "\n".join(entries) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def manifest_lines(self, repository):
        return (repository / "release-manifest.txt").read_text(
            encoding="utf-8"
        ).splitlines()

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
        self.assertEqual(entries, sorted(entries), entries)
        self.assertEqual(len(entries), len(set(entries)), entries)
        for entry in entries:
            relative = PurePosixPath(entry)
            windows_relative = PureWindowsPath(entry)
            self.assertFalse(windows_relative.drive, entry)
            self.assertNotIn("\\", entry, entry)
            self.assertFalse(relative.is_absolute(), entry)
            self.assertNotIn("..", relative.parts, entry)
            self.assertEqual(relative.as_posix(), entry, entry)
            for part in windows_relative.parts:
                message = f"{entry}: {part}"
                self.assertEqual(part, part.rstrip(" ."), message)
                self.assertNotIn(":", part, message)
                self.assertFalse(PureWindowsPath(part).is_reserved(), message)
            self.assertTrue(ROOT.joinpath(*relative.parts).is_file(), entry)
            self.assertFalse(
                entry.casefold().startswith(("doc/", "ara/", "evals/", "tests/")),
                entry,
            )
            self.assertNotEqual(relative.suffix.lower(), ".pdf", entry)

        package_files = {
            path.relative_to(ROOT).as_posix()
            for path in SKILL_DIR.rglob("*")
            if path.is_file()
        }
        manifest_package_files = {
            entry for entry in entries if entry.startswith("skills/research-writing/")
        }
        self.assertEqual(package_files, manifest_package_files, entries)

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

        entries = [
            line.strip()
            for line in MANIFEST.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        skill_prefix = "skills/research-writing/"
        expected_names = [
            "research-writing/" + entry[len(skill_prefix) :]
            if entry.startswith(skill_prefix)
            else entry
            for entry in entries
        ]

        self.assertEqual(names, expected_names, names)
        self.assertIn("research-writing/SKILL.md", names, names)
        self.assertIn("LICENSE", names, names)
        self.assertIn("THIRD_PARTY_NOTICES.md", names, names)
        self.assertFalse(
            any(
                name.casefold().startswith(("doc/", "ara/", "evals/", "tests/"))
                for name in names
            ),
            names,
        )
        self.assertFalse(any(name.lower().endswith(".pdf") for name in names), names)
        self.assertTrue(
            all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in infos),
            infos,
        )
        self.assertTrue(all(info.create_system == 3 for info in infos), infos)
        self.assertTrue(
            all(info.compress_type == zipfile.ZIP_STORED for info in infos),
            infos,
        )

    def test_release_builder_rejects_repository_inputs_without_mutation(self):
        targets = (
            "LICENSE",
            "release-manifest.txt",
            "skills/research-writing/SKILL.md",
        )
        for target_name in targets:
            with self.subTest(target=target_name), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                target = repository.joinpath(*PurePosixPath(target_name).parts)
                original = target.read_bytes()

                result = self.run_release_builder(repository, target)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(target.read_bytes(), original, target_name)

    def test_release_builder_rejects_non_dist_repository_output(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            output = repository / "unsafe.zip"

            result = self.run_release_builder(repository, output)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(output.exists())

    def test_release_builder_rejects_symlink_to_repository_input(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            output = repository / "dist" / "alias.zip"
            output.parent.mkdir()
            try:
                output.symlink_to(repository / "LICENSE")
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")
            original = (repository / "LICENSE").read_bytes()

            result = self.run_release_builder(repository, output)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((repository / "LICENSE").read_bytes(), original)
            self.assertTrue(output.is_symlink())

    def test_release_builder_rejects_symlinked_repository_output_ancestor(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            long_repository = Path(raw) / "repository-with-a-long-component"
            repository.rename(long_repository)
            repository = long_repository
            external_output = Path(raw) / "external-output"
            external_output.mkdir()
            try:
                (repository / "dist").symlink_to(
                    external_output,
                    target_is_directory=True,
                )
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")
            output = repository / "dist" / "release.zip"
            if os.name == "nt":
                output = self.windows_short_path(repository) / "dist" / "release.zip"

            result = self.run_release_builder(repository, output)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((external_output / "release.zip").exists())

    def test_release_builder_rejects_manifest_snapshot_race(self):
        race_script = textwrap.dedent(
            """
            import sys
            from pathlib import Path

            repository = Path(sys.argv[1]).resolve()
            output = Path(sys.argv[2])
            sys.path.insert(0, str(repository / "tools"))
            import build_release

            original_validate = build_release.validate_repository
            mutated = False

            def racing_validate(root=None):
                global mutated
                validation_root = repository if root is None else Path(root).resolve()
                errors = original_validate() if root is None else original_validate(root)
                if validation_root == repository and not errors and not mutated:
                    restricted = (
                        repository
                        / "skills"
                        / "research-writing"
                        / "restricted.pdf"
                    )
                    restricted.write_bytes(b"%PDF-1.7\\nrestricted\\n")
                    manifest = repository / "release-manifest.txt"
                    entries = manifest.read_text(encoding="utf-8").splitlines()
                    entries.append(restricted.relative_to(repository).as_posix())
                    manifest.write_text(
                        "\\n".join(sorted(entries)) + "\\n",
                        encoding="utf-8",
                        newline="\\n",
                    )
                    mutated = True
                return errors

            build_release.validate_repository = racing_validate
            try:
                build_release.build_release(output)
            except (OSError, ValueError):
                raise SystemExit(0)
            raise SystemExit(7)
            """
        )
        for existing in (False, True):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                output = Path(raw) / "release.zip"
                original = b"previous release bytes"
                if existing:
                    output.write_bytes(original)

                result = subprocess.run(
                    [sys.executable, "-c", race_script, str(repository), str(output)],
                    cwd=repository,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                if existing:
                    self.assertEqual(output.read_bytes(), original)
                else:
                    self.assertFalse(output.exists())

    def test_release_builder_validates_immutable_snapshot_bytes(self):
        race_script = textwrap.dedent(
            """
            import os
            import sys
            from pathlib import Path

            repository = Path(sys.argv[1]).resolve()
            output = Path(sys.argv[2])
            sys.path.insert(0, str(repository / "tools"))
            import build_release

            notice = repository / "THIRD_PARTY_NOTICES.md"
            marker = b"\\n/etc/passwd\\n"
            invalid_bytes = notice.read_bytes()
            if not invalid_bytes.endswith(marker):
                raise SystemExit(8)
            valid_bytes = invalid_bytes[: -len(marker)]
            invalid_stat = notice.stat()
            original_validate = build_release.validate_repository
            raced = False

            def racing_validate(root=repository):
                global raced
                validation_root = Path(root).resolve()
                if validation_root != repository or raced:
                    return original_validate(root)
                raced = True
                notice.write_bytes(valid_bytes)
                try:
                    return original_validate(root)
                finally:
                    notice.write_bytes(invalid_bytes)
                    os.utime(
                        notice,
                        ns=(invalid_stat.st_atime_ns, invalid_stat.st_mtime_ns),
                    )

            build_release.validate_repository = racing_validate
            try:
                build_release.build_release(output)
            except (OSError, ValueError):
                raise SystemExit(0)
            raise SystemExit(7)
            """
        )
        marker = b"\n/etc/passwd\n"
        for existing in (False, True):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                notice = repository / "THIRD_PARTY_NOTICES.md"
                notice.write_bytes(notice.read_bytes() + marker)
                output = Path(raw) / "release.zip"
                original = b"previous release bytes"
                if existing:
                    output.write_bytes(original)

                result = subprocess.run(
                    [sys.executable, "-c", race_script, str(repository), str(output)],
                    cwd=repository,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                if existing:
                    self.assertEqual(output.read_bytes(), original)
                else:
                    self.assertFalse(output.exists())

    def test_validator_rejects_symlinked_skill_ancestor(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            external_skills = Path(raw) / "external-skills"
            shutil.move(repository / "skills", external_skills)
            try:
                (repository / "skills").symlink_to(external_skills, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            result = self.run_repository_validator(repository)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ancestor", (result.stdout + result.stderr).casefold())

    def test_validator_does_not_read_nested_fixed_file_links(self):
        scenarios = (
            (
                "SKILL.md",
                b"not frontmatter\n",
                "SKILL.md must begin with YAML frontmatter",
            ),
            (
                "agents/openai.yaml",
                b"[\n",
                "cannot parse agents/openai.yaml",
            ),
            (
                "assets/evidence-ledger.csv",
                b"not,a,ledger\n",
                "evidence ledger header does not match canonical schema",
            ),
            (
                "references/source-foundations.md",
                b"",
                "source foundations table header is not canonical",
            ),
        )
        for relative, external_bytes, forbidden_diagnostic in scenarios:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                target = repository / "skills" / "research-writing" / Path(relative)
                external = Path(raw) / ("external-" + Path(relative).name)
                external.write_bytes(external_bytes)
                target.unlink()
                try:
                    target.symlink_to(external)
                except (NotImplementedError, OSError) as exc:
                    self.skipTest(f"symlink creation unavailable: {exc}")

                result = self.run_repository_validator(repository)

                output = result.stdout + result.stderr
                self.assertNotEqual(result.returncode, 0, output)
                self.assertIn("ordinary non-linked file", output)
                self.assertNotIn(forbidden_diagnostic, output)

    def test_validator_allows_https_url_with_drive_shaped_path_segment(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            reference = (
                repository
                / "skills"
                / "research-writing"
                / "references"
                / "revision-and-style.md"
            )
            reference.write_text(
                reference.read_text(encoding="utf-8")
                + "\nSee https://example.test/C:/guide for details.\n",
                encoding="utf-8",
                newline="\n",
            )

            result = self.run_repository_validator(repository)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_allows_balanced_url_delimiters(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            reference = (
                repository
                / "skills"
                / "research-writing"
                / "references"
                / "revision-and-style.md"
            )
            reference.write_text(
                reference.read_text(encoding="utf-8")
                + "\nSee https://example.test/a(b)/c and "
                "https://[2001:db8::1]/guide for details.\n",
                encoding="utf-8",
                newline="\n",
            )

            result = self.run_repository_validator(repository)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_rejects_local_paths_after_bounded_url_masking(self):
        local_paths = (
            r"[remote](https://example.test/)C:\Users\alice\secret",
            "/root/private",
            "/etc/passwd",
            "~/private",
            r"\Users\alice",
            "vscode://file/root/private",
        )
        for local_path in local_paths:
            with self.subTest(local_path=local_path), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                reference = (
                    repository
                    / "skills"
                    / "research-writing"
                    / "references"
                    / "revision-and-style.md"
                )
                reference.write_text(
                    reference.read_text(encoding="utf-8") + f"\n{local_path}\n",
                    encoding="utf-8",
                    newline="\n",
                )

                result = self.run_repository_validator(repository)

                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"{local_path}\n{result.stdout}{result.stderr}",
                )

    def test_validator_rejects_local_uri_and_drive_relative_paths(self):
        local_paths = (
            "file:///home/alice/secret",
            "file://server/share",
            "file:../outside",
            "C:secret.md",
        )
        for local_path in local_paths:
            with self.subTest(local_path=local_path), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                reference = (
                    repository
                    / "skills"
                    / "research-writing"
                    / "references"
                    / "revision-and-style.md"
                )
                reference.write_text(
                    reference.read_text(encoding="utf-8") + f"\n{local_path}\n",
                    encoding="utf-8",
                    newline="\n",
                )

                result = self.run_repository_validator(repository)

                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"{local_path}\n{result.stdout}{result.stderr}",
                )

    def test_validator_rejects_unsupported_and_encoded_markdown_schemes(self):
        targets = (
            "ftp://example.test/guide",
            "file:%2E%2E/outside",
            "ssh://example.test/repository",
        )
        for target in targets:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                skill = repository / "skills" / "research-writing" / "SKILL.md"
                skill.write_text(
                    skill.read_text(encoding="utf-8") + f"\n[unsafe]({target})\n",
                    encoding="utf-8",
                    newline="\n",
                )

                result = self.run_repository_validator(repository)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_rejects_unknown_skill_file_types(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            binary = repository / "skills" / "research-writing" / "assets" / "payload.bin"
            binary.write_bytes(b"\x00\xffbinary")
            entry = binary.relative_to(repository).as_posix()
            entries = sorted(self.manifest_lines(repository) + [entry])
            self.write_manifest(repository, entries)

            result = self.run_repository_validator(repository)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("unsupported Skill file type", result.stdout + result.stderr)

    def test_validator_scans_root_release_text_for_local_paths(self):
        local_paths = ("file:///home/alice/secret", "/etc/passwd")
        for local_path in local_paths:
            with self.subTest(local_path=local_path), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                notice = repository / "THIRD_PARTY_NOTICES.md"
                notice.write_text(
                    notice.read_text(encoding="utf-8") + f"\n{local_path}\n",
                    encoding="utf-8",
                    newline="\n",
                )

                result = self.run_repository_validator(repository)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_and_builder_reject_noncanonical_license_text(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            (repository / "LICENSE").write_text(
                "not the canonical Apache License\n",
                encoding="utf-8",
                newline="\n",
            )
            output = Path(raw) / "release.zip"

            validation = self.run_repository_validator(repository)
            build = self.run_release_builder(repository, output)

            self.assertNotEqual(
                validation.returncode,
                0,
                validation.stdout + validation.stderr,
            )
            self.assertNotEqual(build.returncode, 0, build.stdout + build.stderr)
            self.assertFalse(output.exists())

    def test_validator_requires_both_legal_files_and_manifest_entries(self):
        for legal_name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
            with self.subTest(legal_name=legal_name), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                (repository / legal_name).unlink()
                entries = [
                    entry for entry in self.manifest_lines(repository) if entry != legal_name
                ]
                self.write_manifest(repository, entries)

                result = self.run_repository_validator(repository)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(legal_name, result.stdout + result.stderr)

    def test_validator_rejects_windows_invalid_and_control_characters(self):
        invalid_entries = [
            f"skills/research-writing/assets/bad{character}name.txt"
            for character in '<>"|?*'
        ]
        invalid_entries.append("skills/research-writing/assets/control\x1fname.txt")
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            entries = sorted(self.manifest_lines(repository) + invalid_entries)
            self.write_manifest(repository, entries)

            result = self.run_repository_validator(repository)
            output = result.stdout + result.stderr

            self.assertNotEqual(result.returncode, 0, output)
            self.assertGreaterEqual(output.count("Windows-invalid character"), 6, output)
            self.assertIn("ASCII control character", output)
            for entry in invalid_entries:
                self.assertIn(f"line {entries.index(entry) + 1}", output)

    def test_validator_rejects_manifest_and_archive_name_collisions(self):
        exact = "skills/research-writing/SKILL.md"
        case_variant = "skills/research-writing/skill.md"
        nfc = "skills/research-writing/assets/caf\u00e9.txt"
        nfd = "skills/research-writing/assets/cafe\u0301.txt"
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            entries = sorted(
                self.manifest_lines(repository) + [exact, case_variant, nfc, nfd]
            )
            self.write_manifest(repository, entries)

            result = self.run_repository_validator(repository)
            output = result.stdout + result.stderr

            self.assertNotEqual(result.returncode, 0, output)
            self.assertIn("archive name exact collision", output)
            self.assertIn("archive name casefold collision", output)
            self.assertIn("archive name NFC collision", output)
            self.assertIn("archive name NFD collision", output)

    def test_validator_rejects_combined_unicode_casefold_collisions(self):
        names = ("CAF\u00c9.txt", "cafe\u0301.txt")
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            assets = repository / "skills" / "research-writing" / "assets"
            entries = self.manifest_lines(repository)
            for name in names:
                path = assets / name
                path.write_text("safe text\n", encoding="utf-8", newline="\n")
                entries.append(path.relative_to(repository).as_posix())
            self.write_manifest(repository, sorted(entries))

            result = self.run_repository_validator(repository)
            output = result.stdout + result.stderr

            self.assertNotEqual(result.returncode, 0, output)
            self.assertIn("archive name NFC+casefold collision", output)
            self.assertIn("archive name NFD+casefold collision", output)

    def test_validator_rejects_duplicate_and_merge_yaml_keys(self):
        mutations = (
            (
                "duplicate Skill frontmatter key",
                "SKILL.md",
                lambda text: text.replace(
                    "name: research-writing\n",
                    "name: research-writing\nname: research-writing\n",
                    1,
                ),
            ),
            (
                "duplicate agent key",
                "agents/openai.yaml",
                lambda text: text.replace(
                    '  display_name: "Research Writing"\n',
                    '  display_name: "Research Writing"\n'
                    '  display_name: "Research Writing"\n',
                    1,
                ),
            ),
            (
                "agent merge key",
                "agents/openai.yaml",
                lambda _text: (
                    "interface:\n"
                    "  <<: &defaults\n"
                    '    display_name: "Research Writing"\n'
                    '    short_description: "Evidence-grounded academic writing workflow"\n'
                    '    default_prompt: "Use $research-writing for a draft."\n'
                ),
            ),
        )
        for label, relative_name, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                path = repository / "skills" / "research-writing" / relative_name
                path.write_text(
                    mutate(path.read_text(encoding="utf-8")),
                    encoding="utf-8",
                    newline="\n",
                )

                result = self.run_repository_validator(repository)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertRegex(
                    result.stdout + result.stderr,
                    r"(?i)(duplicate|merge) key",
                )

    def test_validator_rejects_agent_extra_top_level_key_and_empty_display_name(self):
        mutations = (
            lambda text: text + "extra: true\n",
            lambda text: text.replace(
                '  display_name: "Research Writing"',
                '  display_name: ""',
                1,
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                agent = (
                    repository
                    / "skills"
                    / "research-writing"
                    / "agents"
                    / "openai.yaml"
                )
                agent.write_text(
                    mutate(agent.read_text(encoding="utf-8")),
                    encoding="utf-8",
                    newline="\n",
                )

                result = self.run_repository_validator(repository)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_third_party_notice_states_only_current_verifiable_facts(self):
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        self.assertNotIn("This task", notice)
        self.assertIn(
            "The working repository tracks four provenance/index files under "
            "`doc/source-index/`.",
            notice,
        )
        self.assertIn(
            "The bundled "
            "`skills/research-writing/references/source-foundations.md` contains",
            notice,
        )
        self.assertNotIn("When present", notice)

    def test_manifest_diagnostics_include_line_and_suppress_package_cascade(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            original = "skills/research-writing/assets/writing-brief.md"
            invalid = original + " "
            entries = [
                invalid if entry == original else entry
                for entry in self.manifest_lines(repository)
            ]
            self.write_manifest(repository, entries)
            line_number = entries.index(invalid) + 1

            result = self.run_repository_validator(repository)
            output = result.stdout + result.stderr

            self.assertNotEqual(result.returncode, 0, output)
            self.assertIn(f"line {line_number}", output)
            self.assertNotIn("Skill files missing from manifest", output)
            self.assertNotIn("manifest lists non-physical Skill files", output)

    def test_validator_rejects_empty_instructional_ledger_row(self):
        required_mutations = {
            "claim_id": (0, ""),
            "claim_text": (2, ""),
            "claim_type": (3, "observation"),
            "polarity": (4, "positive"),
            "support_status": (15, "gap"),
            "citation_status": (16, "pending-verification"),
            "action": (18, ""),
        }
        for field, (index, invalid_value) in required_mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                ledger = (
                    repository
                    / "skills"
                    / "research-writing"
                    / "assets"
                    / "evidence-ledger.csv"
                )
                with ledger.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.reader(handle))
                rows[1][index] = invalid_value
                with ledger.open("w", encoding="utf-8", newline="") as handle:
                    csv.writer(handle, lineterminator="\n").writerows(rows)

                result = self.run_repository_validator(repository)

                output = result.stdout + result.stderr
                self.assertNotEqual(result.returncode, 0, output)
                self.assertIn("instructional row", output)

    def test_validator_rejects_source_matrix_rows_with_markers_outside_matrix(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            source = (
                repository
                / "skills"
                / "research-writing"
                / "references"
                / "source-foundations.md"
            )
            markers = (
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
            )
            header = (
                "| Principle | Source type and authority | Supplied PDF and page | "
                "Verified extension document and location | Skill rule | "
                "Applicability or conflict | Canonical URL | Access date |"
            )
            separator = "| --- | --- | --- | --- | --- | --- | --- | --- |"
            fake_rows = "\n".join(
                f"| fake {number} | Workflow guidance | {UPSTREAM_SOURCE_GAP} | "
                f"Fake Source {number}, PDF p.1 | A complete synthetic rule for "
                "validator placement testing only. | A complete synthetic boundary "
                f"for validator placement testing only. | https://example.com/{number} "
                "| 2026-08-07 |"
                for number in range(30)
            )
            source.write_text(
                "# Source Foundations\n\n"
                "## Principle-to-source matrix\n\n"
                f"{header}\n{separator}\n{fake_rows}\n\n"
                + "\n".join(markers)
                + "\n",
                encoding="utf-8",
                newline="\n",
            )

            result = self.run_repository_validator(repository)

            output = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, output)
            self.assertIn("source foundation missing extension marker: Simon Peyton Jones", output)

    def test_validator_requires_expected_principle_source_pairs_in_matrix(self):
        with tempfile.TemporaryDirectory() as raw:
            repository = self.copy_release_repository(raw)
            source = (
                repository
                / "skills"
                / "research-writing"
                / "references"
                / "source-foundations.md"
            )
            text = source.read_text(encoding="utf-8")
            text = text.replace(
                "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20",
                "Unnamed author, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20",
                1,
            )
            text += "\nSimon Peyton Jones\n"
            source.write_text(text, encoding="utf-8", newline="\n")

            result = self.run_repository_validator(repository)

            output = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, output)
            self.assertIn("principle-source pairs", output)

    def test_validator_rejects_invalid_atomic_source_provenance(self):
        mutations = {
            "bad placement": (
                f"| {UPSTREAM_SOURCE_GAP} | Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20 |",
                f"| Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20 | {UPSTREAM_SOURCE_GAP} |",
                "supplied PDF locator",
            ),
            "vague gap marker": (
                UPSTREAM_SOURCE_GAP,
                "not verified",
                "supplied PDF locator",
            ),
            "multiple extension sources": (
                "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20",
                "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20; Other Source, PDF p.2",
                "one source contribution",
            ),
            "multiple extension sources without semicolon": (
                "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20",
                "Simon Peyton Jones, *How to Write a Great Research Paper*, PDF pp.4-7 and 12-20 and Other Source, PDF p.2",
                "locator does not match source contribution",
            ),
            "multiple canonical URLs": (
                "https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/",
                "https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/; https://example.com/other",
                "exactly one HTTPS URL",
            ),
            "wrong canonical URL": (
                "https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/",
                "https://example.com/replacement",
                "canonical URL does not match source contribution",
            ),
            "missing access date": (
                "| 2026-08-07 |",
                "|  |",
                "access date",
            ),
        }
        for label, (old, new, diagnostic) in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                repository = self.copy_release_repository(raw)
                source = (
                    repository
                    / "skills"
                    / "research-writing"
                    / "references"
                    / "source-foundations.md"
                )
                text = source.read_text(encoding="utf-8")
                self.assertIn(old, text, f"mutation fixture missing for {label}")
                source.write_text(
                    text.replace(old, new, 1),
                    encoding="utf-8",
                    newline="\n",
                )

                result = self.run_repository_validator(repository)

                output = result.stdout + result.stderr
                self.assertNotEqual(result.returncode, 0, output)
                self.assertIn(diagnostic, output)


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
            encoding="utf-8",
            newline="",
        ) as handle:
            rows = list(csv.reader(handle))

        self.assertTrue(rows, "evidence ledger must contain a header")
        self.assertEqual(rows[0], expected)
        # The canonical asset explicitly requires one complete instructional row.
        self.assertEqual(len(rows), 2)
        for line_number, row in enumerate(rows[1:], start=2):
            self.assertEqual(
                len(row),
                len(expected),
                f"line {line_number}: expected {len(expected)} columns, "
                f"got {len(row)}: {row!r}",
            )

    def test_source_foundations_are_page_traceable(self):
        text = (SKILL_DIR / "references" / "source-foundations.md").read_text(
            encoding="utf-8"
        )

        def cells(line):
            stripped = line.strip()
            self.assertTrue(stripped.startswith("|"), line)
            self.assertTrue(stripped.endswith("|"), line)
            raw_cells = []
            current = []
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
                    if character == "|":
                        current.pop()
                    current.append(character)
                backslashes = 0

            self.assertFalse(
                current,
                f"table row must end with an unescaped pipe: {line}",
            )
            self.assertTrue(raw_cells and raw_cells[0] == "", line)
            return [cell.strip() for cell in raw_cells[1:]]

        lines = text.splitlines()
        heading = "## Principle-to-source matrix"
        self.assertIn(heading, lines)
        table_lines = []
        table_started = False
        for line in lines[lines.index(heading) + 1 :]:
            if not table_started and not line.strip():
                continue
            if line.startswith("|"):
                table_started = True
                table_lines.append(line)
            else:
                break

        self.assertGreaterEqual(len(table_lines), 2)
        self.assertEqual(
            cells(table_lines[0]),
            SOURCE_FOUNDATION_HEADER,
        )
        separator = cells(table_lines[1])
        self.assertEqual(len(separator), 8, table_lines[1])
        for cell in separator:
            self.assertRegex(cell, r"\A:?-{3,}:?\Z")

        data_rows = table_lines[2:]
        self.assertEqual(len(data_rows), 30)
        allowed_source_types = {
            "Integrity basis",
            "Workflow guidance",
            "Style heuristic",
            "Field guidance",
            "Workflow guidance plus integrity basis",
        }
        extension_locator = re.compile(
            r"^\S(?:.*\S)?,\s*(?:PDF pp?\.\d+(?:-\d+)?"
            r"(?:, \d+(?:-\d+)?)*"
            r"(?:,? and \d+(?:-\d+)?)?|section \S(?:.*\S)?)$"
        )
        https_url = re.compile(r"https://[^\s;|]+")
        actual_contributions = {}
        for matrix_line_number, line in enumerate(data_rows, start=3):
            row = cells(line)
            self.assertEqual(
                len(row),
                8,
                f"matrix line {matrix_line_number}: {line}",
            )
            self.assertTrue(all(row), f"matrix line {matrix_line_number}: empty cell")
            (
                principle,
                source_type,
                supplied,
                extension,
                skill_rule,
                boundary,
                url,
                access_date,
            ) = row
            self.assertIn(source_type, allowed_source_types)
            self.assertNotIn(";", supplied)
            self.assertNotIn(";", extension)
            self.assertNotIn(";", url)
            self.assertGreaterEqual(len(skill_rule), 40)
            self.assertGreaterEqual(len(boundary), 30)
            if url.startswith("https://"):
                self.assertRegex(url, rf"\A{https_url.pattern}\Z")
                self.assertEqual(access_date, "2026-08-07")
                date.fromisoformat(access_date)
            else:
                self.assertIn(url, {UNAVAILABLE_URL_MARKER, DIRECT_URL_MARKER})
                self.assertTrue(
                    re.fullmatch(r"\d{4}-\d{2}-\d{2}", access_date)
                    or access_date == UNAVAILABLE_DATE_MARKER
                )
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", access_date):
                    date.fromisoformat(access_date)

            matches = [
                contribution
                for contribution in EXPECTED_SOURCE_CONTRIBUTIONS
                if contribution[0] == principle
                and contribution[1] in f"{supplied}\n{extension}"
            ]
            self.assertEqual(len(matches), 1, row)
            _, marker, expected_locator = matches[0]
            key = (principle, marker)
            self.assertNotIn(key, actual_contributions, key)
            actual_contributions[key] = (supplied, extension)
            self.assertEqual(url, EXPECTED_SOURCE_URLS[marker])
            if marker == "Technical Writing (updated).pdf":
                self.assertEqual(supplied, expected_locator)
                self.assertEqual(extension, DIRECT_EXTENSION_MARKER)
                self.assertEqual(url, DIRECT_URL_MARKER)
                self.assertEqual(access_date, UNAVAILABLE_DATE_MARKER)
            else:
                self.assertEqual(supplied, UPSTREAM_SOURCE_GAP)
                self.assertEqual(extension, expected_locator)
                self.assertRegex(extension, extension_locator)

        self.assertEqual(
            set(actual_contributions),
            {(principle, marker) for principle, marker, _ in EXPECTED_SOURCE_CONTRIBUTIONS},
        )
        matrix_text = "\n".join(data_rows)
        self.assertNotIn("phrasebank", matrix_text.casefold())
        self.assertNotIn("Restricted-source boundary", matrix_text)
        self.assertIn("https://www.phrasebank.manchester.ac.uk/", text)
        self.assertIn("Phrasebank metadata access context: 2026-08-07", text)
        self.assertIn("Restricted-source boundary", text)
        self.assertIn("normalized from the previous document-wide date", text)
        self.assertIn("not a new access check", text)
        self.assertIn("separately authorized corpus audit", text)

    def test_source_foundations_scope_rows_to_supported_guidance(self):
        text = (SKILL_DIR / "references" / "source-foundations.md").read_text(
            encoding="utf-8"
        )
        rows = [
            line
            for line in text.splitlines()
            if line.startswith("|") and not line.startswith("| ---")
        ]
        row_29 = next(row for row in rows if "PDF pp.70 and 73" in row)
        row_31 = next(row for row in rows if "PDF pp.4-7 and 114" in row)
        self.assertIn("questionable exclusions", row_29)
        self.assertIn("basis", row_29)
        self.assertIn("analyses", row_29)
        self.assertIn("coherence", row_29)
        self.assertIn("completeness", row_29)
        self.assertIn("contribution", row_29)
        self.assertIn("do not establish a general correction protocol", row_29)
        self.assertNotIn("Surface material record errors", row_29)
        self.assertNotIn("Correct the record", row_29)

        row_29_cells = [cell.strip() for cell in row_29.strip("|").split("|")]
        self.assertEqual(row_29_cells[1], "Workflow guidance plus integrity basis")

        row_31_cells = [cell.strip() for cell in row_31.strip("|").split("|")]
        self.assertEqual(row_31_cells[1], "Workflow guidance")
        self.assertNotIn("integrity basis", row_31_cells[1].casefold())
        self.assertIn("variables", row_31)
        self.assertIn("notation", row_31)
        self.assertIn("symbols", row_31)
        self.assertIn("assumptions", row_31)
        self.assertIn("limitations", row_31)

    def test_design_review_describes_progressive_disclosure_rework(self):
        text = (ROOT / "docs" / "skill-design-review.md").read_text(encoding="utf-8")

        self.assertIn("genre-aware Structure", text)
        self.assertIn("claim type, support status, and citation status", text)
        self.assertIn("at most 700 words", text)
        self.assertIn("source-foundations matrix", text)
        self.assertIn("development provenance records", text)
        self.assertIn("only for rationale, adaptation, or design-audit requests", text)
        self.assertIn("not loaded for ordinary drafting or revision", text)
        self.assertIn("atomic", text)
        self.assertIn("unresolved upstream", text)
        self.assertIn("separately authorized corpus audit", text)
        self.assertIn("No post-refactor forward evaluation results are claimed", text)
        for stale_claim in (
            "1,223-word core",
            "not yet concise",
            "still needed before public release",
            "remains the next correction",
            "Task 9",
        ):
            self.assertNotIn(stale_claim, text)

    def test_evaluation_rubric_scores_structure_by_genre(self):
        rubric = (ROOT / "evals" / "rubric.md").read_text(encoding="utf-8")

        self.assertIn(
            "Clear progression appropriate to the selected genre and task", rubric
        )
        self.assertNotIn(
            "Clear problem-gap-insight-contribution progression", rubric
        )


class SkillBehaviorContractTest(unittest.TestCase):
    SOURCE_LINK = (
        "[references/source-foundations.md](references/source-foundations.md)"
    )
    STATUS_VALUES = {
        "claim_type": [
            "observation",
            "source-report",
            "interpretation",
            "hypothesis",
            "proposal",
        ],
        "support_status": [
            "verified",
            "partial",
            "pending-verification",
            "gap",
            "not-applicable",
        ],
        "citation_status": ["verified", "pending-verification", "not-required"],
    }
    PHASE_PATTERNS = [
        r"fram",
        r"ledger",
        r"structure",
        r"draft",
        r"revis",
        r"audit",
        r"deliver",
    ]
    STRUCTURE_PATTERNS = {
        "contribution": (
            r"contribution",
            [r"problem", r"gap", r"insight", r"contribution"],
        ),
        "empirical": (
            r"empirical",
            [r"question", r"design", r"observation", r"interpretation", r"limit"],
        ),
        "replication": (
            r"replication|negative[- ]result",
            [
                r"prior.*claim",
                r"replication.*design",
                r"result",
                r"agreement|discrepancy",
                r"boundar",
            ],
        ),
        "survey": (
            r"survey|review",
            [r"scope", r"organizing.*lens", r"synthes", r"unresolved.*question"],
        ),
        "methods-data": (
            r"method|data(?:set)?",
            [r"need", r"artifact|method", r"validation", r"usage.*boundar"],
        ),
        "local-revision": (
            r"local|sentence|revision",
            [r"preserv.*structure.*restructur"],
        ),
    }
    BOUNDARIES = {
        "section_guides": (
            "Section names and order are selected by venue, field, artifact, and "
            "user intent. Treat the patterns below as rhetorical jobs, not mandatory "
            "headings."
        ),
        "revision": (
            "Treat active voice, topic and stress positions, sentence length, and "
            "paragraph patterns as diagnostics. Apply them only when they improve "
            "reader comprehension without changing meaning or violating field "
            "convention."
        ),
        "integrity": (
            "Integrity checks are low-freedom gates: citation identity, quotation "
            "fidelity, numbers, units, denominators, comparison baselines, causal "
            "force, claim scope, and conclusion-changing limitations must survive "
            "drafting and revision."
        ),
    }

    def contract_files(self):
        references = SKILL_DIR / "references"
        return {
            "skill": (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"),
            "workflow": (references / "writing-workflow.md").read_text(
                encoding="utf-8"
            ),
            "section_guides": (references / "section-guides.md").read_text(
                encoding="utf-8"
            ),
            "revision": (references / "revision-and-style.md").read_text(
                encoding="utf-8"
            ),
            "integrity": (references / "evidence-and-integrity.md").read_text(
                encoding="utf-8"
            ),
            "openai": (SKILL_DIR / "agents" / "openai.yaml").read_text(
                encoding="utf-8"
            ),
        }

    def section_body(self, text, heading):
        level = len(heading) - len(heading.lstrip("#"))
        section = re.search(
            rf"^{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^#{{1,{level}}} |\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(section, heading)
        return section.group("body")

    def numbered_section_body(self, text, level, number):
        marks = "#" * level
        section = re.search(
            rf"^{re.escape(marks)}\s+{number}\.\s+[^\n]+\n"
            rf"(?P<body>.*?)(?=^#{{1,{level}}}\s|\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(section, f"level {level}, section {number}")
        return section.group("body")

    def enum_candidates(self, text, field):
        declaration = re.compile(
            rf"`{re.escape(field)}`\s*"
            r"(?::|=|(?:is|must be|may be|can be)\s+(?:one of\s+)?)\s*"
        )
        any_declaration = re.compile(
            r"`(?:"
            + "|".join(map(re.escape, self.STATUS_VALUES))
            + r")`\s*(?::|=|(?:is|must be|may be|can be)\s+"
            r"(?:one of\s+)?)\s*"
        )
        candidates = []
        for occurrence in declaration.finditer(text):
            tail = text[occurrence.end() :]
            stops = [position for position in (tail.find("\n\n"),) if position >= 0]
            next_declaration = any_declaration.search(tail)
            if next_declaration:
                stops.append(next_declaration.start())
            fragment = tail[: min(stops)] if stops else tail
            values = re.findall(r"`([^`]+)`", fragment)
            candidates.append(values)
        return candidates

    @staticmethod
    def markdown_tables(text):
        tables = []
        current = []
        fence = None
        for line in text.splitlines() + [""]:
            stripped = line.strip()
            fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
            if fence_match:
                marker = fence_match.group(1)[0]
                fence = None if fence == marker else marker
                if current:
                    tables.append(current)
                    current = []
                continue
            if fence is not None:
                continue
            if "|" in stripped:
                cells = [cell.strip() for cell in stripped.strip("|").split("|")]
                if len(cells) >= 2:
                    current.append(cells)
                    continue
            if current:
                tables.append(current)
                current = []
        return tables

    def genre_tables(self, text):
        return [
            table
            for table in self.markdown_tables(text)
            if len(table) >= 2
            and len(table[0]) == 2
            and re.search(r"artifact|genre", table[0][0], re.IGNORECASE)
            and re.search(
                r"progression|pattern|structure", table[0][1], re.IGNORECASE
            )
        ]

    def assert_terms(self, text, label, *groups):
        lowered = text.lower()
        for group in groups:
            alternatives = (group,) if isinstance(group, str) else group
            self.assertTrue(
                any(term.lower() in lowered for term in alternatives),
                f"{label}: missing one of {alternatives}",
            )

    def assert_core_size(self, skill):
        self.assertLessEqual(len(skill.split()), 700)

    def assert_output_limit_verification(self, skill):
        completion = self.section_body(skill, "## Completion check")
        completion_heading = re.search(
            r"(?m)^##\s+Completion check\s*$", skill
        )
        self.assertIsNotNone(completion_heading)
        completion_tail = skill[completion_heading.end() :]
        self.assertNotRegex(
            completion_tail,
            r"(?m)^#{1,6}\s+",
            "Completion check must be the final Skill section",
        )
        raw_confirm = re.search(r"(?i)\bconfirm(?:\s+that)?\b", completion_tail)
        self.assertIsNotNone(raw_confirm)
        outside_rule = skill[: completion_heading.end()] + completion_tail[
            raw_confirm.start() :
        ]
        rule_reference = re.compile(
            r"\boutput[- ]limits?\b|"
            r"\b(?:word|sentence|section|character)[- ]limits?\b|"
            r"\blimits?\s+(?:on|for|over)\s+words?\b|"
            r"\bword[- ]count(?:ing)?\b|"
            r"\bcount(?:ing)?\s+(?:the\s+)?words?\b|"
            r"\b(?:counting|word[- ]counting)\s+"
            r"(?:convention|method|rule)\b|"
            r"\bwhitespace[- ](?:delimited|separated)\b|"
            r"\bpunctuation\s+boundar(?:y|ies)\b|"
            r"\bbyte[- ]pair\b|\btokeni[sz]\w*\b",
            re.IGNORECASE,
        )
        self.assertNotRegex(
            outside_rule,
            rule_reference,
            "output-limit semantics must appear only in the pre-audit rule",
        )
        sentences = [
            " ".join(sentence.lower().split())
            for sentence in re.split(r"(?<=[.!?])\s+", completion)
            if sentence.strip()
        ]
        confirm_indexes = [
            index
            for index, sentence in enumerate(sentences)
            if re.match(r"^confirm\b", sentence)
        ]
        self.assertEqual(len(confirm_indexes), 1)
        confirm_index = confirm_indexes[0]
        self.assertGreater(confirm_index, 0, "output-limit rule must precede audit")
        audit = " ".join(sentences[confirm_index:])
        clauses = [
            clause.strip().rstrip(".!?").strip()
            for sentence in sentences[:confirm_index]
            for clause in re.split(r"\s*;\s*", sentence)
            if clause.strip()
        ]
        self.assertIn(
            len(clauses),
            (2, 3),
            "output-limit rule must contain verification, an optional unit list, "
            "and the counting fallback",
        )

        verification = clauses[0]
        fallback = clauses[-1]
        self.assertRegex(
            verification,
            r"^(?:before (?:final )?(?:delivery|delivering)|"
            r"prior to (?:final )?delivery|pre-delivery)\b",
        )
        self.assertRegex(verification, r"\b(?:verif\w*|validat\w*|check\w*)\b")
        self.assertRegex(
            verification,
            r"\b(?:mechanic\w*|programmatic\w*|automat\w*|"
            r"scripts?|tools?|counters?)\b",
        )
        self.assertRegex(
            verification,
            r"\b(?:explicit(?:ly)?(?:\s+(?:stated|declared))?|"
            r"stated|declared)\b",
        )
        self.assertRegex(verification, r"\blimits?\b")
        unit_scope = " ".join(clauses[:2]) if len(clauses) == 3 else verification
        for unit in ("word", "sentence", "section", "character"):
            self.assertRegex(unit_scope, rf"\b{unit}s?\b", unit)

        forbidden_rule_semantics = re.compile(
            r"\b(?:do\s+not|don't|never|need(?:s)?\s+not|needn't|"
            r"no\s+need\s+to)\b|"
            r"\b(?:optional(?:ly)?|advisory|recommend\w*|"
            r"non[- ]?compulsory|not\s+(?:required|mandatory|necessary|"
            r"compulsory|obligatory))\b|"
            r"\b(?:skip\w*|omit\w*|ignore\w*|avoid\w*|exclude\w*|"
            r"estimat\w*|approximat\w*|eyeball\w*|ballpark|rough(?:ly)?)\b|"
            r"\b(?:only\s+if|if\s+convenient|when\s+convenient|"
            r"if\s+time\s+permits?|when\s+time\s+permits?)\b|"
            r"\b(?:instead|alternatively|rather\s+than|in\s+place\s+of)\b|"
            r"\b(?:non[- ]whitespace|punctuation[- ]delimited|"
            r"punctuation\s+boundar(?:y|ies)|byte[- ]pair|encoding|"
            r"tokeni[sz]\w*)\b",
        )
        self.assertNotRegex(
            " ".join(clauses),
            forbidden_rule_semantics,
            "output-limit rule is weakened, skipped, or given an alternate basis",
        )

        if len(clauses) == 3:
            unit_clause = clauses[1]
            self.assertRegex(unit_clause, r"^include\b")
            self.assertRegex(unit_clause, r"\blimits?\b")
            self.assertRegex(
                unit_clause, r"\b(?:check|verification|validation)\b"
            )
            for unit in ("word", "sentence", "section", "character"):
                self.assertRegex(unit_clause, rf"\b{unit}s?\b", unit)

        missing_counting_rule = re.compile(
            r"(?:\b(?:absent|without|in\s+the\s+absence\s+of)\b"
            r"[^,;.!?]{0,60}\b(?:counting|word[- ]count(?:ing)?)\b"
            r"[^,;.!?]{0,30}\b(?:convention|method|rule)\b|"
            r"\b(?:if|when)\b[^,;.!?]{0,60}\bno\b[^,;.!?]{0,40}"
            r"\b(?:counting|word[- ]count(?:ing)?)\b[^,;.!?]{0,30}"
            r"\b(?:convention|method|rule)\b|"
            r"\b(?:if|when)\b[^,;.!?]{0,60}"
            r"\b(?:counting|word[- ]count(?:ing)?)\b[^,;.!?]{0,30}"
            r"\b(?:convention|method|rule)\b[^,;.!?]{0,30}"
            r"\b(?:is|was)\s+not\s+(?:specified|provided|stated|declared)\b)"
        )
        self.assertRegex(
            fallback,
            missing_counting_rule,
            "missing fallback condition for an absent counting convention",
        )
        self.assertRegex(fallback, r"\bwhitespace\b")
        self.assertRegex(fallback, r"\b(?:words?|tokens?|units?)\b")
        self.assertRegex(fallback, r"\b(?:count\w*|use|treat|split)\b")
        self.assertNotRegex(
            fallback,
            r"\b(?:may|might|could|optional(?:ly)?)\b",
            "whitespace fallback must be authoritative",
        )

        audit_clauses = [
            clause.strip().rstrip(".!?").strip()
            for sentence in sentences[confirm_index:]
            for clause in re.split(r"\s*;\s*", sentence)
            if clause.strip()
        ]
        self.assertGreaterEqual(len(audit_clauses), 7)
        audit_clauses[0] = re.sub(
            r"^confirm(?: that)?\s+", "", audit_clauses[0], count=1
        )
        required_audit = (
            r"no unsupported claim became fact",
            r"no citation, quotation, fact, number, method, or result was "
            r"invented or silently changed",
            r"no association became causation",
            r"no unstated method-result relation appeared",
            r"no meaning atom or material limitation disappeared",
            r"every new claim has separate canonical statuses",
            r"(?:and )?output order and supporting trace match the request",
        )
        for actual, expected in zip(audit_clauses, required_audit):
            self.assertRegex(actual, rf"^{expected}$")

        for epistemic_clause in audit_clauses[len(required_audit) :]:
            self.assertRegex(
                epistemic_clause,
                r"^(?:and\s+)?(?:findings|hypotheses|interpretations|"
                r"explanations|a causal explanation)\s+(?:may|might)\s+"
                r"(?:remain|be)\s+"
                r"(?:(?:explicitly|clearly)\s+"
                r"(?:labeled|labelled|qualified|marked)|"
                r"uncertain|unresolved|tentative|provisional|inconclusive|"
                r"a hypothesis)$",
                "completion audit contains an unsupported extra rule",
            )
            self.assertNotRegex(epistemic_clause, rule_reference)
            self.assertNotRegex(epistemic_clause, forbidden_rule_semantics)
            if re.match(r"^(?:and\s+)?a causal explanation\b", epistemic_clause):
                self.assertNotRegex(
                    epistemic_clause,
                    r"\bremain\s+(?:clearly\s+|explicitly\s+)?"
                    r"(?:hypotheses|interpretations|explanations|findings)\b",
                )

    def assert_source_route(self, skill):
        self.assertEqual(skill.count(self.SOURCE_LINK), 1)
        conditional = self.section_body(skill, "## Conditional loading")
        route = re.search(
            rf"(?ms)^-\s+Read\s+{re.escape(self.SOURCE_LINK)}(?P<body>.*?)"
            r"(?=^\s*-\s+|\n\s*\n|\Z)",
            conditional,
        )
        self.assertIsNotNone(route)
        self.assert_terms(
            route.group(0),
            "source-foundations route",
            "explaining",
            "auditing",
            "adapting",
            "writing philosophy",
            "do not load",
            "ordinary drafting",
            "revision",
        )

    def assert_phase_headings(self, skill):
        workflow = self.section_body(skill, "## Workflow")
        headings = re.findall(
            r"^###\s+(\d+)\.\s+(.+?)(?:\s+#+)?\s*$",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual([number for number, _title in headings], list("1234567"))
        for (_number, title), pattern in zip(headings, self.PHASE_PATTERNS):
            self.assertRegex(title.lower(), pattern)

    def assert_no_story_heading(self, skill, workflow):
        self.assertNotRegex(
            skill + "\n" + workflow,
            r"(?m)^#{2,3} 3\. Story$",
        )

    def assert_status_declarations(self, skill, files):
        ledger = self.numbered_section_body(skill, 3, 2)
        for field, expected in self.STATUS_VALUES.items():
            self.assertEqual(self.enum_candidates(ledger, field), [expected])
            self.assertEqual(self.enum_candidates(skill, field), [expected])

        for field, expected in self.STATUS_VALUES.items():
            for name in ("workflow", "integrity"):
                self.assertEqual(
                    self.enum_candidates(files[name], field),
                    [expected],
                    f"{name}: {field}",
                )
            for name in ("section_guides", "revision"):
                self.assertEqual(
                    self.enum_candidates(files[name], field),
                    [],
                    f"{name}: {field}",
                )

    def assert_structure_table(self, workflow):
        genre_tables = self.genre_tables(workflow)
        self.assertEqual(len(genre_tables), 1)
        structure = self.numbered_section_body(workflow, 2, 3)
        self.assertEqual(self.genre_tables(structure), genre_tables)
        rows = genre_tables[0]
        self.assertEqual(len(rows[0]), 2)
        self.assertTrue(all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]))
        parsed = {}
        for row in rows[2:]:
            self.assertEqual(len(row), 2)
            artifact, progression = row
            categories = [
                name
                for name, (artifact_pattern, _progression_patterns) in self.STRUCTURE_PATTERNS.items()
                if re.search(artifact_pattern, artifact, re.IGNORECASE)
            ]
            self.assertEqual(len(categories), 1, artifact)
            category = categories[0]
            self.assertNotIn(category, parsed)
            parsed[category] = progression
        self.assertEqual(set(parsed), set(self.STRUCTURE_PATTERNS))
        for category, progression in parsed.items():
            cursor = 0
            for pattern in self.STRUCTURE_PATTERNS[category][1]:
                match = re.search(pattern, progression[cursor:], re.IGNORECASE)
                self.assertIsNotNone(match, f"{category}: {pattern}")
                cursor += match.end()

    def assert_no_legacy_taxonomy(self, skill, references):
        combined = skill + "\n" + references
        for legacy in (
            "partially supported, inferred, proposed, or a gap",
            "Mark each row `supported`, `qualified`, `gap`, "
            "`pending-verification`, or `not-applicable`",
            "support, qualification, or a gap",
        ):
            self.assertNotIn(legacy, combined)

    def assert_safeguard(self, files, label):
        skill = files["skill"]
        if label == "fabrication":
            core = self.section_body(skill, "## Core principle")
            self.assert_terms(
                core,
                label,
                ("never fabricate", "do not invent"),
                "citation",
                "quotation",
                "number",
                "method",
                "result",
            )
        elif label == "causality":
            core = self.section_body(skill, "## Core principle").lower()
            self.assertRegex(
                core,
                r"(?:never|do not)[^.]{0,80}association[^.]{0,40}causation",
            )
        elif label == "user prose verification":
            depth = self.section_body(skill, "## Proportional operating depth").lower()
            self.assertRegex(
                depth,
                r"(?:do not|never)[^.]{0,100}user-provided prose[^.]{0,80}verified",
            )
        elif label == "faithful copyedit":
            ledger = self.numbered_section_body(skill, 3, 2)
            self.assert_terms(
                ledger,
                label,
                "faithful copyedit",
                "internal",
                "missing support",
                "safe revision",
            )
        elif label == "restricted sources":
            core = self.section_body(skill, "## Core principle").lower()
            self.assertRegex(
                core,
                r"(?:do not|never)[^.]{0,40}copy[^.]{0,80}restricted"
                r"[^.]{0,80}(?:phrasebank|handbook)",
            )
            self.assert_terms(core, label, "lawful source")
        elif label == "meaning atoms":
            revise = self.numbered_section_body(skill, 3, 5)
            self.assert_terms(
                revise,
                label,
                "meaning atoms",
                "proposition",
                "scope",
                "polarity",
                "causal force",
                "comparison",
                "population",
                "conditions",
                "quantities",
                "units",
                "uncertainty",
                "conclusion-changing limitations",
                "recheck",
            )
        elif label == "proportional depth":
            depth = self.section_body(skill, "## Proportional operating depth")
            self.assert_terms(
                depth,
                label,
                "smallest workflow",
                "new paragraphs or sections",
                "full-paper ceremony",
                "sentence",
            )
            normalized = " ".join(depth.lower().split())
            sentence_subject = (
                r"\b(?:new\s+prose|new\s+(?:(?:paragraphs?|sections?)"
                r"(?:,\s*(?:(?:and|or)\s+)?|\s+(?:and|or)\s+))*sentences?|"
                r"(?:a|any|each|every)\s+"
                r"(?:new\s+)?sentence)\b"
            )
            positive_requirement = (
                r"(?![^.]{0,80}\b(?:do(?:es)?\s+not|never|need(?:s)?\s+not|"
                r"must\s+not|should\s+not)\b)"
                r"[^.]{0,80}\b(?:need(?:s)?|require(?:s)?|use(?:s)?|run(?:s)?|"
                r"follow(?:s)?|(?:must|should)\s+(?:use|run|follow))\b"
            )
            full_workflow = (
                r"[^.]{0,160}(?:\bfull(?:-paper)?\s+(?:workflow|ceremony)\b|"
                r"\bbrief\b[^.]{0,80}\bledger\b[^.]{0,80}\bstructure\b"
                r"[^.]{0,80}\bdraft\b[^.]{0,80}\baudit\b)"
            )
            self.assertNotRegex(
                normalized,
                sentence_subject + positive_requirement + full_workflow,
            )
        elif label == "output-only compliance":
            deliver = self.numbered_section_body(skill, 3, 7)
            self.assert_terms(
                deliver,
                label,
                "requested artifact first",
                "output-only",
                "internal",
                "pending-verification",
            )
        elif label == "compression safety":
            compression = self.section_body(skill, "## Compression safety gate")
            self.assert_terms(
                compression,
                label,
                "conclusion type",
                "causal force",
                "numbers",
                "comparison",
                "scope",
                "conclusion-changing limitations",
                ("cut", "remove"),
                "recheck",
                ("shortest faithful", "constraint"),
            )
        elif label == "completion check":
            completion = self.section_body(skill, "## Completion check")
            self.assert_terms(
                completion,
                label,
                "unsupported claim",
                "fact",
                "citation",
                "number",
                ("invented", "changed"),
                "association",
                "causation",
                "limitation",
                "canonical statuses",
                "output order",
            )
        else:
            self.fail(f"unknown safeguard: {label}")

    def assert_no_global_contract_overrides(self, skill):
        permissive_modal = r"(?:may|might|can|could)"
        epistemic_subject = (
            r"(?:findings?|hypotheses?|interpretations?|explanations?)"
        )
        forbidden_permissions = (
            re.compile(
                rf"\b{epistemic_subject}\b[^.!?;]{{0,80}}\b{permissive_modal}\s+"
                r"(?:(?:be\s+)?fabricat\w*|"
                r"invent\w*(?:\s+\w+){0,3}\s+citations?)\b",
                re.IGNORECASE,
            ),
            re.compile(
                rf"\bhypotheses?\b[^.!?;]{{0,80}}\b{permissive_modal}\s+"
                r"(?:be\s+)?(?:stat\w*|present\w*|treat\w*)\s+as\s+"
                r"(?:a\s+)?facts?\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?:the\s+)?(?:following\s+|preceding\s+)?"
                r"(?:completion|delivery|output[- ]limit|verification)\s+"
                r"(?:rule|check|requirement)\b[^.!?;]{0,40}"
                r"(?:\b(?:is|are|be|becomes?|remains?)\s+"
                r"(?:merely\s+|only\s+)?(?:optional|advisory|non[- ]?compulsory|"
                r"not\s+(?:required|mandatory|necessary|compulsory|obligatory))\b|"
                r"\b(?:may|can|could)\s+be\s+(?:skipp\w*|omit\w*|ignor\w*))",
                re.IGNORECASE,
            ),
        )
        for clause in re.split(r"[.!?;]+", skill):
            normalized = " ".join(clause.split())
            for forbidden in forbidden_permissions:
                self.assertNotRegex(
                    normalized,
                    forbidden,
                    "Skill globally permits an integrity breach or weakens a "
                    "completion rule",
                )

    def assert_note_proximity_guard(self, skill, workflow):
        core = self.section_body(skill, "## Core principle")
        normalized = " ".join(core.lower().split())
        self.assertIn(
            "do not infer temporal order, intervention exposure, group assignment "
            "or comparison design, or method-result relationships from proximity in "
            "notes; when unstated, report facts separately.",
            normalized,
        )
        ledger = self.numbered_section_body(workflow, 2, 2)
        relation_paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", ledger)
            if "method-result relationship" in paragraph.lower()
        ]
        self.assertEqual(len(relation_paragraphs), 1)
        relation = " ".join(relation_paragraphs[0].lower().split())
        self.assertRegex(
            relation,
            r"^treat\s+a\s+method-result relationship\s+as\s+its\s+own\s+claim\b",
        )
        self.assertRegex(relation, r"\bnote proximity\s+is\s+not\s+support\b")
        self.assertRegex(
            relation,
            r"\brequire\s+explicit\s+timing,\s+exposure,\s+or\s+comparison\s+"
            r"evidence\s+before\s+connecting\s+the\s+two\.\s+without\s+it,\s+"
            r"state\s+the\s+method\s+and\s+observation\s+separately\b",
        )
        prohibition_clauses = [
            clause
            for clause in re.split(r"(?<=[.!?])\s+", relation)
            if re.search(r"\bdo\s+not\s+connect\s+them\b", clause)
        ]
        self.assertEqual(len(prohibition_clauses), 1)
        prohibition = prohibition_clauses[0]
        self.assertRegex(prohibition, r"\bdo\s+not\s+connect\s+them\s+with\b")
        guarded_connectors = [
            (double_quoted or backticked).rstrip(".,")
            for double_quoted, backticked in re.findall(
                r'"([^"]+)"|`([^`]+)`', prohibition
            )
        ]
        self.assertCountEqual(
            guarded_connectors,
            ["after", "using", "with", "under", "associated with"],
        )
        completion = self.section_body(skill, "## Completion check")
        self.assert_terms(
            completion,
            "method-result completion gate",
            "no unstated method-result relation",
        )

    def assert_reference_boundaries(self, files):
        for name, boundary in self.BOUNDARIES.items():
            paragraphs = [
                paragraph.strip()
                for paragraph in re.split(r"\n\s*\n", files[name])
                if paragraph.strip()
            ]
            self.assertGreaterEqual(len(paragraphs), 2, name)
            normalized_boundary = " ".join(boundary.split())
            normalized_paragraph = " ".join(paragraphs[1].split())
            self.assertEqual(normalized_paragraph, normalized_boundary, name)

    def assert_genre_section_guidance(self, section_guides):
        introduction = self.section_body(section_guides, "## Introduction")
        self.assert_terms(
            introduction,
            "genre-aware introduction",
            "replication",
            "negative-result",
            "prior claim",
            "replication question",
            "without manufacturing novelty",
        )
        self.assertNotRegex(
            introduction.lower(),
            r"(?:must|always)[^.]{0,80}problem[^.]{0,40}gap"
            r"[^.]{0,40}insight[^.]{0,40}contribution",
        )
        self.assertNotIn("source-verification gap", section_guides)

    def assert_unresolved_citation_delivery(self, files):
        core_delivery = self.numbered_section_body(files["skill"], 3, 7)
        workflow_delivery = self.numbered_section_body(files["workflow"], 2, 7)
        for label, text in (
            ("core delivery", core_delivery),
            ("workflow delivery", workflow_delivery),
        ):
            self.assertRegex(
                text.lower(),
                r"output-only[^.]{0,100}(?:omit|qualif)[^.]{0,40}any claim"
                r"[^.]{0,120}citation"
                r"[^.]{0,80}pending-verification[^.]{0,120}internal"
                r"[^.]{0,80}do not append",
                label,
            )
        citation_rules = self.section_body(files["integrity"], "## Citations")
        citation_paragraphs = [
            paragraph
            for paragraph in re.split(r"\n\s*\n", citation_rules)
            if paragraph.strip()
        ]
        delivery_index = next(
            (
                index
                for index, paragraph in enumerate(citation_paragraphs)
                if "pending-verification" in paragraph.lower()
            ),
            None,
        )
        self.assertIsNotNone(delivery_index)
        citation_delivery = "\n\n".join(citation_paragraphs[delivery_index:])
        self.assertRegex(
            citation_delivery.lower(),
            r"citation[^.]{0,100}pending-verification[^.]{0,100}claim"
            r"[^.]{0,80}(?:omit|qualif)",
        )
        self.assertRegex(
            citation_delivery.lower(),
            r"output-only[^.]{0,120}internal[^.]{0,80}do not append",
        )
        pre_delivery = self.section_body(
            files["integrity"], "## Pre-Delivery Audit"
        )
        audit_items = re.findall(
            r"(?ms)^-\s+.*?(?=^-\s+|\Z)",
            pre_delivery,
        )
        audit_delivery_index = next(
            (
                index
                for index, item in enumerate(audit_items)
                if "citation" in item.lower()
            ),
            None,
        )
        self.assertIsNotNone(audit_delivery_index)
        pre_delivery_rules = "\n".join(audit_items[audit_delivery_index:])
        self.assertRegex(
            pre_delivery_rules.lower(),
            r"citation[^.]{0,120}pending-verification[^.]{0,100}claim"
            r"[^.]{0,80}(?:omit|qualif)",
        )
        self.assertRegex(
            pre_delivery_rules.lower(),
            r"output-only[^.]{0,120}internal[^.]{0,100}(?:omit|qualif)",
        )
        for label, text in (
            ("core delivery", core_delivery),
            ("workflow delivery", workflow_delivery),
            ("citation rules", citation_delivery),
            ("pre-delivery audit", pre_delivery_rules),
        ):
            self.assertNotIn("support_status", text.lower(), label)
            self.assertNotRegex(
                text.lower(),
                r"`(?:verified|partial|gap|not-applicable)`",
                label,
            )
        for label, text in (
            ("core delivery", core_delivery),
            ("workflow delivery", workflow_delivery),
            ("citation rules", citation_delivery),
            ("pre-delivery audit", pre_delivery_rules),
        ):
            self.assertNotRegex(text.lower(), r"\bsupport(?:_status)?\b", label)

    def assert_openai_metadata(self, openai):
        self.assertEqual(
            yaml.safe_load(openai),
            {
                "interface": {
                    "display_name": "Research Writing",
                    "short_description": "Evidence-grounded academic writing workflow",
                    "default_prompt": (
                        "Use $research-writing to turn my research materials into a "
                        "traceable paper draft."
                    ),
                }
            },
        )

    def assert_behavior_contract(self, files, *, check_core_size=True):
        skill = files["skill"]
        workflow = files["workflow"]
        references = "\n".join(
            (
                workflow,
                files["section_guides"],
                files["revision"],
                files["integrity"],
            )
        )

        if check_core_size:
            self.assert_core_size(skill)
        self.assert_no_global_contract_overrides(skill)
        self.assert_source_route(skill)
        self.assert_phase_headings(skill)
        self.assert_no_story_heading(skill, workflow)
        self.assert_status_declarations(skill, files)
        self.assert_structure_table(workflow)
        for name in ("skill", "section_guides", "revision", "integrity"):
            self.assertEqual(
                self.genre_tables(files[name]),
                [],
                f"{name}: genre tables belong only in workflow section 3",
            )
        self.assert_no_legacy_taxonomy(skill, references)
        for safeguard in (
            "fabrication",
            "causality",
            "user prose verification",
            "faithful copyedit",
            "restricted sources",
            "meaning atoms",
            "proportional depth",
            "output-only compliance",
            "compression safety",
            "completion check",
        ):
            self.assert_safeguard(files, safeguard)
        self.assert_output_limit_verification(skill)
        self.assert_note_proximity_guard(skill, workflow)
        self.assertIn("Never invent a contribution", skill + "\n" + workflow)
        self.assert_reference_boundaries(files)
        self.assert_genre_section_guidance(files["section_guides"])
        self.assert_unresolved_citation_delivery(files)
        self.assert_openai_metadata(files["openai"])

    def test_skill_core_is_concise_source_routed_and_genre_aware(self):
        self.assert_behavior_contract(self.contract_files())

    def test_skill_behavior_contract_accepts_semantic_formatting_variants(self):
        original = self.contract_files()
        files = dict(original)
        files["skill"] = files["skill"].replace(
            "- Read " + self.SOURCE_LINK,
            "- Read\n  " + self.SOURCE_LINK,
            1,
        )
        files["skill"] = files["skill"].replace(
            "Do not impose full-paper ceremony on sentences or skip "
            "traceability when creating claims.",
            "New sentences should avoid the full workflow and full-paper ceremony; "
            "retain claim traceability.",
            1,
        )
        output_limit_rule = (
            "Before delivery, mechanically verify explicit word, sentence, section, "
            "and character limits; absent a counting convention, count words by "
            "whitespace."
        )
        self.assertIn(output_limit_rule, files["skill"])
        files["skill"] = files["skill"].replace(
            output_limit_rule,
            "Before delivery, use a script to validate stated word, sentence, "
            "section, and character limits. Absent a counting rule, use "
            "whitespace-delimited tokens.",
            1,
        )
        files["skill"] = files["skill"].replace(
            "output order and supporting trace match the request.",
            "output order and supporting trace match the request; hypotheses may "
            "remain explicitly labeled.",
            1,
        )
        clearly_labeled = files["skill"].replace(
            "hypotheses may remain explicitly labeled.",
            "hypotheses may remain clearly labeled.",
            1,
        )
        self.assertNotEqual(clearly_labeled, files["skill"])
        self.assert_output_limit_verification(clearly_labeled)
        split_rule = files["skill"].replace(
            "Before delivery, use a script to validate stated word, sentence, "
            "section, and character limits. Absent a counting rule, use "
            "whitespace-delimited tokens.",
            "Before delivery, mechanically validate every declared output limit. "
            "Include limits on words, sentences, sections, and characters in this "
            "check. Absent a counting convention, count words by whitespace.",
            1,
        )
        self.assertNotEqual(split_rule, files["skill"])
        self.assert_output_limit_verification(split_rule)
        natural_output_rules = (
            (
                "Before delivering, mechanically verify all explicitly stated "
                "limits for words, sentences, sections, and characters; if no "
                "word-counting method is specified, use whitespace-delimited "
                "tokens."
            ),
            (
                "Before delivery, mechanically verify explicit word, sentence, "
                "section, and character limits. If no counting convention exists, "
                "count words by whitespace."
            ),
            (
                "Before delivery, perform a mechanical check of stated limits on "
                "words, sentences, sections, and characters. Without a "
                "word-counting convention, count whitespace-separated tokens as "
                "words."
            ),
            (
                "Prior to final delivery, mechanically validate declared limits "
                "for words, sentences, sections, and characters. Absent a counting "
                "method, split on whitespace to count words."
            ),
        )
        for natural_rule in natural_output_rules:
            with self.subTest(natural_output_rule=natural_rule):
                variant = re.sub(
                    re.escape(
                        "Before delivery, use a script to validate stated word, "
                        "sentence, section, and character limits. Absent a counting "
                        "rule, use whitespace-delimited tokens."
                    ),
                    natural_rule,
                    files["skill"],
                    count=1,
                )
                self.assertNotEqual(variant, files["skill"])
                self.assert_output_limit_verification(variant)
        uncertain_findings = files["skill"].replace(
            "hypotheses may remain explicitly labeled.",
            "findings may remain uncertain.",
            1,
        )
        self.assertNotEqual(uncertain_findings, files["skill"])
        self.assert_output_limit_verification(uncertain_findings)
        provisional_interpretations = files["skill"].replace(
            "hypotheses may remain explicitly labeled.",
            "interpretations might remain provisional.",
            1,
        )
        self.assertNotEqual(provisional_interpretations, files["skill"])
        self.assert_output_limit_verification(provisional_interpretations)
        phase_titles = {
            1: "Frame request",
            2: "Build evidence ledger",
            3: "Structure the argument",
            4: "Draft from evidence",
            5: "Revise without meaning drift",
            6: "Audit integrity",
            7: "Deliver the requested artifact",
        }
        for number, title in phase_titles.items():
            files["skill"] = re.sub(
                rf"(?m)^### {number}\. [^\n]+$",
                f"###   {number}. {title} ###",
                files["skill"],
                count=1,
            )
        files["workflow"] = re.sub(
            r"(?m)^## 3\. [^\n]+$",
            "## 3. Choose a genre-aware structure",
            files["workflow"],
            count=1,
        )
        files["workflow"] = re.sub(
            r"(?m)^## 7\. [^\n]+$",
            "## 7. Deliver under output constraints",
            files["workflow"],
            count=1,
        )
        files["workflow"] = files["workflow"].replace(
            '"after," "using," "with," "under," or "associated with."',
            "`associated with`, `under`, `with`, `using`, or `after`.",
            1,
        )
        files["workflow"] = re.sub(
            r"(?mi)^\|\s*(?:artifact|genre)[^|]*\|"
            r"[^|]*(?:progression|pattern|structure)[^|]*\|\s*$",
            "| Genre | Default pattern |",
            files["workflow"],
            count=1,
        )
        files["workflow"] = re.sub(
            r"(?<=\w)\s*[-=]+>\s*(?=\w)",
            "; ",
            files["workflow"],
        )
        files["workflow"] = "\n".join(
            line.strip().strip("|").strip()
            if line.strip().startswith("|") and line.strip().endswith("|")
            else line
            for line in files["workflow"].splitlines()
        )
        files["workflow"] += "\n"
        declaration_prefix = re.compile(
            r"(?m)^- (?=`(?:claim_type|support_status|citation_status)`\s*:)"
        )
        for name in ("workflow", "integrity"):
            files[name] = declaration_prefix.sub("", files[name])
        for name, boundary in self.BOUNDARIES.items():
            files[name] = files[name].replace(
                boundary,
                textwrap.fill(boundary, width=54),
                1,
            )
        files["openai"] = textwrap.dedent(
            """
            # Product metadata may be commented and reflowed.
            interface:
              display_name: Research Writing
              short_description: >-
                Evidence-grounded academic writing workflow
              default_prompt: >-
                Use $research-writing to turn my research materials into a
                traceable paper draft.
            """
        ).lstrip()

        for name in files:
            self.assertNotEqual(files[name], original[name], name)
        self.assert_behavior_contract(files, check_core_size=False)
        for global_clause in (
            "Findings may remain uncertain.",
            "Interpretations might remain provisional.",
        ):
            with self.subTest(global_clause=global_clause):
                accepted = dict(files)
                accepted["skill"] = accepted["skill"].replace(
                    "## Conditional loading",
                    global_clause + "\n\n## Conditional loading",
                    1,
                )
                self.assert_behavior_contract(accepted, check_core_size=False)

    def test_skill_behavior_contract_rejects_structural_regressions(self):
        genre_table_pattern = re.compile(
            r"(?mi)^\|[^\n|]*(?:artifact|genre)[^\n|]*\|"
            r"[^\n|]*(?:progression|pattern|structure)[^\n|]*\|\r?\n"
            r"(?:^\|.*\|\r?\n?)+"
        )

        def insert_global_clause(text, clause):
            text = text.replace(
                "academic and technical manuscripts", "technical manuscripts", 1
            )
            changed = text.replace(
                "## Conditional loading",
                clause + "\n\n## Conditional loading",
                1,
            )
            self.assertIn(len(changed.split()), (698, 700))
            return changed

        structural_mutations = (
            (
                "fabrication allowed before conditional loading",
                "skill",
                lambda text: insert_global_clause(
                    text, "Findings may be fabricated."
                ),
                lambda files: self.assert_behavior_contract(files),
            ),
            (
                "hypotheses allowed as fact before conditional loading",
                "skill",
                lambda text: insert_global_clause(
                    text, "Hypotheses may be stated as fact."
                ),
                lambda files: self.assert_behavior_contract(files),
            ),
            (
                "citation invention allowed before conditional loading",
                "skill",
                lambda text: insert_global_clause(
                    text, "Explanations may invent citations."
                ),
                lambda files: self.assert_behavior_contract(files),
            ),
            (
                "completion rule made optional before conditional loading",
                "skill",
                lambda text: insert_global_clause(
                    text, "The following completion rule is optional."
                ),
                lambda files: self.assert_behavior_contract(files),
            ),
            (
                "fabrication allowed in epistemic audit tail",
                "skill",
                lambda text: text.replace(
                    "output order and supporting trace match the request.",
                    "output order and supporting trace match the request; findings "
                    "may be fabricated.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "hypotheses allowed as fact in audit tail",
                "skill",
                lambda text: text.replace(
                    "output order and supporting trace match the request.",
                    "output order and supporting trace match the request; hypotheses "
                    "may be stated as fact.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "citation invention allowed in audit tail",
                "skill",
                lambda text: text.replace(
                    "output order and supporting trace match the request.",
                    "output order and supporting trace match the request; "
                    "explanations may invent citations.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "output-limit override after completion section",
                "skill",
                lambda text: text + "\n# Skip output-limit verification.\n",
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "requested output limits",
                "skill",
                lambda text: text.replace("explicit word", "requested word", 1),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "specified output limits",
                "skill",
                lambda text: text.replace("explicit word", "specified word", 1),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "enforced rather than verified limits",
                "skill",
                lambda text: text.replace(
                    "mechanically verify", "mechanically enforce", 1
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "counter enforces rather than verifies limits",
                "skill",
                lambda text: text.replace(
                    "mechanically verify explicit",
                    "use a counter to enforce stated",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "malformed epistemic audit tail",
                "skill",
                lambda text: text.replace(
                    "output order and supporting trace match the request.",
                    "output order and supporting trace match the request; a causal "
                    "explanation may remain hypotheses.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "optional verification at audit start",
                "skill",
                lambda text: text.replace(
                    "Confirm that no unsupported claim became fact;",
                    "Confirm mechanical verification is optional; no unsupported "
                    "claim became fact;",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "anaphoric verification weakening inside audit",
                "skill",
                lambda text: text.replace(
                    "no unsupported claim became fact;",
                    "no unsupported claim became fact; the preceding requirement "
                    "applies only when convenient;",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "alternate word basis inside audit",
                "skill",
                lambda text: text.replace(
                    "no unsupported claim became fact;",
                    "no unsupported claim became fact; punctuation boundaries "
                    "determine the authoritative total instead;",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "estimated total inside audit",
                "skill",
                lambda text: text.replace(
                    "no unsupported claim became fact;",
                    "no unsupported claim became fact; an estimate is sufficient "
                    "for the total;",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "anaphoric output verification negation",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "Do not perform that verification. Absent a counting "
                    "convention, count words by whitespace.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "punctuation spans override word count",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace, but regard each "
                    "punctuation-delimited span as one word for the final count.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "byte-pair encoding overrides word count",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace, but byte-pair encoding determines "
                    "the authoritative word total.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "no-need output-limit verification follow-on",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. There is no need to verify output "
                    "limits.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "estimated output-limit follow-on",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Output limits can be estimated.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "skipped output-limit counting follow-on",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Skip output-limit counting.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "recommended rather than compulsory verification",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Output-limit verification is "
                    "recommended rather than compulsory.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "unmarked punctuation word-count basis",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Count words by punctuation "
                    "boundaries.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "tokenizer determines word count",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. A tokenizer determines the word "
                    "count.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "removed mechanical output-limit qualifier",
                "skill",
                lambda text: text.replace(
                    "mechanically verify", "verify", 1
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "optional output-limit follow-on without mechanical qualifier",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Output-limit verification is "
                    "optional.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "recommended but noncompulsory output-limit verification",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Mechanical output-limit "
                    "verification is recommended, not compulsory.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "punctuation method overrides whitespace default",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Instead, count words by "
                    "punctuation boundaries.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "contradictory output-limit prohibition follow-on",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Do not mechanically verify "
                    "output limits.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "contradictory output-limit verification follow-on",
                "skill",
                lambda text: text.replace(
                    "count words by whitespace.",
                    "count words by whitespace. Mechanical output-limit "
                    "verification is not mandatory.",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "optional mechanical output-limit verification",
                "skill",
                lambda text: text.replace(
                    "Before delivery, mechanically verify explicit word, sentence, "
                    "section, and character limits",
                    "Before delivery, mechanical verification of explicit word, "
                    "sentence, section, and character limits is optional",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "reversed whitespace word-count default",
                "skill",
                lambda text: text.replace(
                    "absent a counting convention, count words by whitespace",
                    "without a convention, ignore whitespace and count words using "
                    "a tokenizer",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "weakened mechanical output-limit verification",
                "skill",
                lambda text: text.replace(
                    "mechanically verify", "do not mechanically verify", 1
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "removed default whitespace word-count convention",
                "skill",
                lambda text: text.replace(
                    "absent a counting convention, count words by whitespace",
                    "choose a convenient word-count convention",
                    1,
                ),
                lambda files: self.assert_output_limit_verification(files["skill"]),
            ),
            (
                "unconditional duplicate source route",
                "skill",
                lambda text: text
                + "\n- Read "
                + self.SOURCE_LINK
                + " for all tasks.\n",
                lambda files: self.assert_source_route(files["skill"]),
            ),
            (
                "alternate support status",
                "integrity",
                lambda text: text.replace("`partial`", "`qualified`", 1),
                lambda files: self.assert_status_declarations(files["skill"], files),
            ),
            (
                "additional status taxonomy",
                "integrity",
                lambda text: text
                + "\n`support_status` is one of `supported`, `qualified`, or `gap`.\n",
                lambda files: self.assert_status_declarations(files["skill"], files),
            ),
            (
                "single-value status taxonomy",
                "integrity",
                lambda text: text + "\n`support_status`: `qualified`.\n",
                lambda files: self.assert_status_declarations(files["skill"], files),
            ),
            (
                "unformatted single-value status taxonomy",
                "integrity",
                lambda text: text + "\n`support_status`: qualified.\n",
                lambda files: self.assert_status_declarations(files["skill"], files),
            ),
            (
                "status taxonomy phrased with may be",
                "integrity",
                lambda text: text
                + "\n`support_status` may be `supported` or `qualified`.\n",
                lambda files: self.assert_status_declarations(files["skill"], files),
            ),
            (
                "alternate status taxonomy outside the Skill ledger",
                "skill",
                lambda text: text + "\n`support_status`: `qualified`.\n",
                lambda files: self.assert_status_declarations(files["skill"], files),
            ),
            (
                "missing workflow-local status declaration",
                "workflow",
                lambda text: re.sub(
                    r"(?m)^.*?`support_status`\s*"
                    r"(?::|=|(?:is|must be)\s+(?:one of\s+)?)"
                    r"[^\r\n]*(?:\r?\n|$)",
                    "",
                    text,
                    count=1,
                ),
                lambda files: self.assert_status_declarations(files["skill"], files),
            ),
            (
                "renamed Structure phase",
                "skill",
                lambda text: re.sub(
                    r"(?m)^### 3\. [^\n]+$",
                    "### 3. Outline",
                    text,
                    count=1,
                ),
                lambda files: self.assert_phase_headings(files["skill"]),
            ),
            (
                "workflow phases reparented under another section",
                "skill",
                lambda text: text.replace(
                    "### 1. Frame", "## Notes\n\n### 1. Frame", 1
                ),
                lambda files: self.assert_phase_headings(files["skill"]),
            ),
            (
                "duplicate genre row",
                "workflow",
                lambda text: re.sub(
                    r"(?mi)^(\|[^|\n]*(?:survey|review)[^|\n]*\|[^\n]+\|)$",
                    r"\1\n\1",
                    text,
                    count=1,
                ),
                lambda files: self.assert_structure_table(files["workflow"]),
            ),
            (
                "second genre table",
                "workflow",
                lambda text: text
                + "\n\n## Duplicate Genre Defaults\n\n"
                + genre_table_pattern.search(text).group(0)
                + "\n",
                lambda files: self.assert_structure_table(files["workflow"]),
            ),
            (
                "genre table outside Structure phase",
                "workflow",
                lambda text: genre_table_pattern.sub("", text, count=1)
                + "\n\n## Genre Defaults Appendix\n\n"
                + genre_table_pattern.search(text).group(0),
                lambda files: self.assert_structure_table(files["workflow"]),
            ),
            (
                "genre table fenced as code",
                "workflow",
                lambda text: genre_table_pattern.sub(
                    lambda match: "```text\n" + match.group(0) + "```\n",
                    text,
                    count=1,
                ),
                lambda files: self.assert_structure_table(files["workflow"]),
            ),
            (
                "genre table duplicated in section guides",
                "section_guides",
                lambda text: text
                + "\n\n"
                + genre_table_pattern.search(original["workflow"]).group(0),
                lambda files: self.assert_behavior_contract(files),
            ),
            (
                "missing genre row",
                "workflow",
                lambda text: re.sub(
                    r"(?mi)^\|[^|\n]*(?:method|data(?:set)?)[^|\n]*\|"
                    r"[^\n]+\|\r?\n",
                    "",
                    text,
                    count=1,
                ),
                lambda files: self.assert_structure_table(files["workflow"]),
            ),
            (
                "mandatory Story heading",
                "workflow",
                lambda text: re.sub(
                    r"(?m)^## 3\. [^\n]+$",
                    "## 3. Story",
                    text,
                    count=1,
                ),
                lambda files: self.assert_no_story_heading(
                    files["skill"], files["workflow"]
                ),
            ),
            (
                "overbroad full-workflow trigger",
                "skill",
                lambda text: text.replace(
                    "new paragraphs or sections",
                    "new prose",
                    1,
                ),
                lambda files: self.assert_safeguard(files, "proportional depth"),
            ),
            (
                "explicit sentence full-workflow trigger",
                "skill",
                lambda text: text.replace(
                    "Do not impose full-paper ceremony on sentences",
                    "New sentences need the full workflow. "
                    "Do not impose full-paper ceremony on sentences",
                    1,
                ),
                lambda files: self.assert_safeguard(files, "proportional depth"),
            ),
            (
                "sentence added to full-workflow list",
                "skill",
                lambda text: text.replace(
                    "new paragraphs or sections need",
                    "new paragraphs or sections or sentences need",
                    1,
                ),
                lambda files: self.assert_safeguard(files, "proportional depth"),
            ),
            (
                "parallel new-prose full-workflow rule",
                "skill",
                lambda text: text.replace(
                    "Do not impose full-paper ceremony on sentences",
                    "New prose needs the full workflow. "
                    "Do not impose full-paper ceremony on sentences",
                    1,
                ),
                lambda files: self.assert_safeguard(files, "proportional depth"),
            ),
            (
                "parallel paragraph-and-sentence full-workflow rule",
                "skill",
                lambda text: text.replace(
                    "Do not impose full-paper ceremony on sentences",
                    "New paragraphs and sentences need the full workflow. "
                    "Do not impose full-paper ceremony on sentences",
                    1,
                ),
                lambda files: self.assert_safeguard(files, "proportional depth"),
            ),
            (
                "negated method-result claim gate",
                "workflow",
                lambda text: text.replace(
                    "Treat a method-result relationship",
                    "Never treat a method-result relationship",
                    1,
                ),
                lambda files: self.assert_note_proximity_guard(
                    files["skill"], files["workflow"]
                ),
            ),
            (
                "ignored method-result evidence gate",
                "workflow",
                lambda text: text.replace(
                    "require explicit timing",
                    "ignore explicit timing",
                    1,
                ),
                lambda files: self.assert_note_proximity_guard(
                    files["skill"], files["workflow"]
                ),
            ),
            (
                "permissive method-result connector gate",
                "workflow",
                lambda text: text.replace(
                    "do not connect them",
                    "freely connect them",
                    1,
                ),
                lambda files: self.assert_note_proximity_guard(
                    files["skill"], files["workflow"]
                ),
            ),
            (
                "separate method and observation despite explicit evidence",
                "workflow",
                lambda text: text.replace(
                    "Without it",
                    "Even with explicit evidence",
                    1,
                ),
                lambda files: self.assert_note_proximity_guard(
                    files["skill"], files["workflow"]
                ),
            ),
            (
                "permissive method-result connector follow-on",
                "workflow",
                lambda text: text.replace(
                    "do not connect them with",
                    "do not connect them. You may connect them with",
                    1,
                ),
                lambda files: self.assert_note_proximity_guard(
                    files["skill"], files["workflow"]
                ),
            ),
            (
                "boundary moved away from reference start",
                "revision",
                lambda text: text.replace(
                    self.BOUNDARIES["revision"] + "\n\n", "", 1
                )
                + "\n"
                + self.BOUNDARIES["revision"]
                + "\n",
                lambda files: self.assert_reference_boundaries(files),
            ),
            (
                "oversized core",
                "skill",
                lambda text: text
                + "\n"
                + ("excess " * max(1, 701 - len(text.split()))),
                lambda files: self.assert_core_size(files["skill"]),
            ),
            (
                "changed product metadata",
                "openai",
                lambda text: text.replace("Research Writing", "Research Writer", 1),
                lambda files: self.assert_openai_metadata(files["openai"]),
            ),
            (
                "ambiguous output-only citation delivery",
                "skill",
                lambda text: re.sub(
                    r"(?ms)(^### 7\. [^\n]+$.*?)(`pending-verification`)",
                    lambda match: match.group(1) + "unresolved",
                    text,
                    count=1,
                ),
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
            (
                "pending citation retained in output-only artifact",
                "skill",
                lambda text: text.replace(
                    "omit or qualify any claim",
                    "retain every claim",
                    1,
                ),
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
            (
                "pending citation behavior depends on support status",
                "skill",
                lambda text: text.replace(
                    "citation remains `pending-verification`",
                    "citation remains `pending-verification` and `support_status` "
                    "is `gap`",
                    1,
                ),
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
            (
                "core pending citation behavior depends on support sufficiency",
                "skill",
                lambda text: text.replace(
                    "do not append commentary.",
                    "do not append commentary.\n\n"
                    "Apply this only when support is insufficient.",
                    1,
                ),
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
            (
                "workflow pending citation behavior depends on support sufficiency",
                "workflow",
                lambda text: text.replace(
                    "do not append commentary.",
                    "do not append commentary.\n\n"
                    "Apply this only when support is insufficient.",
                    1,
                ),
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
            (
                "pending citation behavior depends on a support value",
                "integrity",
                lambda text: text.replace(
                    "only if the affected claim is omitted or visibly qualified",
                    "only if the affected claim is omitted or visibly qualified "
                    "and its support is `gap`",
                    1,
                ),
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
            (
                "pending citation behavior depends on support sufficiency",
                "integrity",
                lambda text: text.replace(
                    "only if the affected claim is omitted or visibly qualified",
                    "only if the affected claim is omitted or visibly qualified "
                    "and support is insufficient",
                    1,
                ),
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
            (
                "pending citation dependency moved to a new paragraph",
                "integrity",
                lambda text: text.replace(
                    "otherwise include the unresolved citation in the issues list.",
                    "otherwise include the unresolved citation in the issues list.\n\n"
                    "Apply this only when `support_status` is `gap`.",
                    1,
                ),
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
            (
                "pre-delivery dependency moved to a separate bullet",
                "integrity",
                lambda text: text
                + "\n- Apply this only when support is insufficient.\n",
                lambda files: self.assert_unresolved_citation_delivery(files),
            ),
        )
        connector_mutations = tuple(
            (
                "missing " + connector + " connector guard",
                "workflow",
                lambda text, token=token: text.replace(token, "", 1),
                lambda files: self.assert_note_proximity_guard(
                    files["skill"], files["workflow"]
                ),
            )
            for connector, token in (
                ("after", '"after,"'),
                ("using", '"using,"'),
                ("with", '"with,"'),
                ("under", '"under,"'),
                ("associated with", '"associated with."'),
            )
        )
        safeguard_mutators = {
            "fabrication": lambda text: text.replace(
                "Never fabricate", "May fabricate", 1
            ),
            "causality": lambda text: text.replace(
                "Never turn association into causation.",
                "Association and causation are related.",
                1,
            ),
            "user prose verification": lambda text: text.replace(
                "independently verified", "well written", 1
            ),
            "faithful copyedit": lambda text: text.replace(
                "Keep this record internal", "Publish this record", 1
            ),
            "restricted sources": lambda text: text.replace(
                "Do not copy restricted", "Copy restricted", 1
            ),
            "meaning atoms": lambda text: text.replace(
                "causal force, temporal order", "tone, cadence", 1
            ),
            "proportional depth": lambda text: text.replace(
                "smallest workflow", "largest workflow", 1
            ),
            "output-only compliance": lambda text: text.replace(
                "Honor output-only constraints", "Ignore output constraints", 1
            ),
            "compression safety": lambda text: text.replace(
                "Freeze conclusion type", "Consider wording", 1
            ),
            "completion check": lambda text: text.replace(
                "no unsupported claim became fact", "claims read smoothly", 1
            ),
        }
        safeguard_mutations = tuple(
            (
                "missing " + label,
                "skill",
                mutate,
                lambda files, safeguard=label: self.assert_safeguard(
                    files, safeguard
                ),
            )
            for label, mutate in safeguard_mutators.items()
        )
        mutations = structural_mutations + connector_mutations + safeguard_mutations
        original = self.contract_files()
        self.assert_behavior_contract(original)
        for label, name, mutate, checker in mutations:
            with self.subTest(label=label):
                changed = dict(original)
                changed[name] = mutate(original[name])
                self.assertNotEqual(changed[name], original[name])
                with self.assertRaises(AssertionError):
                    checker(changed)


class SkillSemanticCompletenessTest(unittest.TestCase):
    """High-priority semantic gates expressed as observable invariants.

    The parser checks status tables, phase boundaries, and required transitions
    rather than accepting an isolated slogan.  It remains a static contract,
    so fresh-agent pressure tests are still needed for behavioral validation.
    """

    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        references = SKILL_DIR / "references"
        cls.workflow = (references / "writing-workflow.md").read_text(
            encoding="utf-8"
        )
        cls.integrity = (references / "evidence-and-integrity.md").read_text(
            encoding="utf-8"
        )
        cls.revision = (references / "revision-and-style.md").read_text(
            encoding="utf-8"
        )
        cls.brief = (SKILL_DIR / "assets" / "writing-brief.md").read_text(
            encoding="utf-8"
        )
        cls.ledger = (SKILL_DIR / "assets" / "evidence-ledger.csv").read_text(
            encoding="utf-8"
        )

    @staticmethod
    def section(text, heading):
        level = len(heading) - len(heading.lstrip("#"))
        match = re.search(
            rf"^{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^#{{1,{level}}}\s|\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        if not match:
            raise AssertionError(f"missing section: {heading}")
        return match.group("body")

    @staticmethod
    def tables(text):
        """Return markdown tables outside fenced code blocks as cell lists."""
        tables, current, fence = [], [], None
        for line in text.splitlines() + [""]:
            stripped = line.strip()
            if re.match(r"^(`{3,}|~{3,})", stripped):
                fence = None if fence else stripped[0]
                if current:
                    tables.append(current)
                    current = []
                continue
            if fence:
                continue
            if "|" in stripped and stripped.startswith("|"):
                cells = [cell.strip() for cell in stripped.strip("|").split("|")]
                if len(cells) >= 2:
                    current.append(cells)
                    continue
            if current:
                tables.append(current)
                current = []
        return tables

    def table_after(self, text, heading):
        body = self.section(text, heading)
        tables = self.tables(body)
        self.assertTrue(tables, f"no table in {heading}")
        return tables[0]

    def test_support_and_citation_statuses_have_operational_definitions(self):
        semantics = self.section(self.integrity, "### Status semantics and identity")
        normalized = " ".join(semantics.casefold().split())
        for status in ("verified", "partial", "pending-verification", "gap", "not-applicable"):
            match = re.search(
                rf"`{re.escape(status)}`\s+(?:means|is valid|answers)[^.;]+[.;]",
                normalized,
            )
            self.assertIsNotNone(match, status)
            self.assertGreater(len(match.group(0)), len(status) + 20)
        citation = re.search(
            r"`citation_status`[^.]+\.", normalized,
        )
        self.assertIsNotNone(citation)
        for term in ("source identity", "exact supporting location", "citation format"):
            self.assertIn(term, normalized, term)
        self.assertRegex(normalized, r"stable `claim_id`")
        self.assertRegex(normalized, r"`evidence_id`[^.]+source registry")

    def test_delivery_matrix_blocks_unsupported_claims_even_when_citation_identity_is_known(self):
        rows = self.table_after(self.integrity, "## Delivery decision matrix")
        self.assertEqual(rows[0][:2], ["`support_status`", "`citation_status`"])
        data = rows[2:]
        self.assertGreaterEqual(len(data), 5)
        by_support = {row[0].casefold(): row for row in data}
        self.assertIn("`verified`", by_support)
        self.assertIn("`partial`, `pending-verification`, or `gap`", by_support)
        self.assertIn("`not-applicable`", by_support)
        verified_pending = next(
            row for row in data
            if row[0].casefold() == "`verified`"
            and "`pending-verification`" in row[1].casefold()
        )
        self.assertRegex(verified_pending[2].casefold(), r"omit|qualif")
        unresolved = by_support["`partial`, `pending-verification`, or `gap`"]
        self.assertRegex(unresolved[2].casefold(), r"qualif|split|omit")
        self.assertRegex(unresolved[2].casefold(), r"never.*unqualified.*fact")
        inapplicable = by_support["`not-applicable`"]
        self.assertRegex(inapplicable[2].casefold(), r"genuinely|bypass")
        self.assertRegex(
            self.integrity.casefold(),
            r"(?:hypothesis|proposal)[^\n]+explicitly labeled",
        )

    def test_meaning_vector_is_shared_by_core_and_revision_reference(self):
        expected = (
            "proposition",
            "scope",
            "polarity",
            "causal force",
            "temporal order",
            "design",
            "intervention exposure",
            "group assignment",
            "comparison",
            "method-result relation",
            "population",
            "conditions",
            "qualifiers",
            "quantities",
            "units",
            "uncertainty",
            "conclusion-changing limitations",
        )
        for name, text, heading in (
            ("core", self.skill, "### 5. Revise"),
            ("revision", self.revision, "## Meaning vector"),
        ):
            body = self.section(text, heading).casefold()
            self.assertRegex(body, r"meaning vector|canonical meaning")
            for term in expected:
                self.assertIn(term.casefold(), body, f"{name}: {term}")

    def test_method_result_connectors_are_conditionally_guarded(self):
        ledger = self.section(self.workflow, "## 2. Ledger")
        paragraphs = [" ".join(p.casefold().split()) for p in re.split(r"\n\s*\n", ledger) if p.strip()]
        relation = next(p for p in paragraphs if "method-result relationship" in p)
        self.assertRegex(relation, r"note proximity is not support")
        self.assertRegex(relation, r"require explicit timing.*exposure.*comparison")
        self.assertRegex(relation, r"without it, state the method and observation separately")
        denied = re.search(r"do not connect them with ([^.]+)\.", relation)
        self.assertIsNotNone(denied)
        for connector in ("after", "using", "with", "under", "associated with"):
            self.assertIn(connector, denied.group(1))
        self.assertRegex(
            relation,
            r"if the record explicitly supports the relation, retain the connector",
        )

    def test_audit_has_a_bounded_feedback_loop_and_stop_condition(self):
        rows = self.table_after(self.workflow, "## Audit feedback and stop")
        self.assertEqual(rows[0][:2], ["Audit outcome", "Required transition"])
        data = rows[2:]
        self.assertGreaterEqual(len(data), 3)
        joined = " ".join(" ".join(row).casefold() for row in data)
        self.assertRegex(joined, r"gate.*fail.*return.*ledger|draft|revise")
        self.assertRegex(joined, r"re-?audit")
        self.assertRegex(joined, r"bounded|attempt")
        self.assertRegex(joined, r"stop.*unresolved|do not deliver")
        self.assertRegex(joined, r"all.*pass.*deliver")

    def test_output_only_and_compression_constraints_are_consistent(self):
        deliver = self.section(self.skill, "### 7. Deliver")
        self.assertRegex(
            " ".join(deliver.casefold().split()),
            r"output-only[^.]+evidence[^.]+(?:omit|qualif)[^.]+internal[^.]+commentary",
        )
        compression = self.section(self.revision, "## Compression")
        self.assertRegex(compression.casefold(), r"output-only")
        self.assertRegex(compression.casefold(), r"shortest faithful")
        self.assertRegex(compression.casefold(), r"(?:meaning|evidence) drift")
        self.assertRegex(compression.casefold(), r"internal")

    def test_external_material_is_untrusted_data_and_permissions_are_explicit(self):
        body = self.section(self.workflow, "## Input and permission boundary")
        lowered = body.casefold()
        for data_kind in ("pdf", "notes", "draft", "code", "code comments", "imperative"):
            self.assertIn(data_kind, lowered, data_kind)
        self.assertRegex(lowered, r"untrusted data")
        self.assertRegex(lowered, r"not instructions")
        self.assertRegex(lowered, r"system or user authorization")
        self.assertRegex(lowered, r"tool|write|external access")

    def test_author_signoff_and_original_immutability_are_explicit(self):
        body = self.section(self.workflow, "## 1. Frame").casefold()
        self.assertIn("author retains final sign-off", body)
        self.assertRegex(body, r"preserve the supplied original")
        self.assertRegex(body, r"substantive changes.*approval")
        self.assertRegex(self.brief.casefold(), r"author final sign-off")

    def test_bundled_assets_are_copied_to_working_project_and_template_row_has_lifecycle(self):
        body = self.section(self.workflow, "## 2. Ledger").casefold()
        self.assertRegex(body, r"copy the template into the user's working project")
        self.assertRegex(body, r"never modify the installed skill package")
        self.assertRegex(body, r"bundled assets")
        self.assertRegex(body, r"template-01.*instructional")
        self.assertRegex(body, r"remove or replace")
        self.assertRegex(body, r"never treat it as a claim")
        rows = list(csv.reader(self.ledger.splitlines()))
        self.assertEqual(rows[1][0], "TEMPLATE-01")
        self.assertIn("instructional", rows[1][2].casefold())

    def test_source_foundations_are_design_provenance_not_domain_evidence_and_notes_are_source_reports(self):
        foundations = (SKILL_DIR / "references" / "source-foundations.md").read_text(
            encoding="utf-8"
        )
        intro = " ".join(
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", foundations)
            if paragraph.strip()
        )
        intro = intro.split("## How to read the evidence", 1)[0].casefold()
        self.assertIn("design provenance", intro)
        self.assertIn("not domain evidence", intro)
        self.assertRegex(intro, r"do not cite")
        integrity = self.section(self.integrity, "### Status semantics and identity").casefold()
        self.assertRegex(integrity, r"user-provided notes.*source-report")
        self.assertRegex(integrity, r"explicitly attributed")

    def test_counting_convention_covers_cjk_and_mixed_text(self):
        text = "\n".join((self.workflow, self.revision)).casefold()
        self.assertRegex(text, r"cjk|chinese|japanese|korean")
        self.assertRegex(text, r"(?:character|language-aware)[^.]{0,140}(?:convention|count)")
        self.assertRegex(text, r"mixed text")

    def test_design_sensitive_claim_words_require_design_and_analysis_support(self):
        rows = self.table_after(self.integrity, "## Design-sensitive wording")
        self.assertEqual(rows[0][:3], ["Term family", "Required basis", "Fallback"])
        self.assertGreaterEqual(len(rows), 4)
        terms = " ".join(" ".join(row).casefold() for row in rows[2:])
        for term in (
            "prediction", "mediation", "mechanism", "intervention",
            "causal identification", "effect", "impact", "robust",
            "generalizes", "significant", "demonstrated", "proved",
            "novel", "sota",
        ):
            self.assertIn(term, terms, term)
        for row in rows[2:]:
            self.assertRegex(" ".join(row).casefold(), r"design|analysis")
            self.assertRegex(" ".join(row).casefold(), r"qualif|replace|do not use")



if __name__ == "__main__":
    unittest.main()
