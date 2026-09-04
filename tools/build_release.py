from __future__ import annotations

import argparse
import os
import stat
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from validate_repository import ROOT, safe_release_source_records, validate_repository


FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
SKILL_PREFIX = "skills/research-writing/"


@dataclass(frozen=True)
class FileIdentity:
    resolved_path: str
    device: int
    inode: int
    mode: int
    size: int
    modified_ns: int


@dataclass(frozen=True)
class SnapshotPayload:
    entry: str
    archive_name: str
    source: Path
    identity: FileIdentity
    data: bytes


@dataclass(frozen=True)
class ReleaseSnapshot:
    manifest_bytes: bytes
    manifest_identity: FileIdentity
    entries: tuple[str, ...]
    payloads: tuple[SnapshotPayload, ...]


def archive_name(entry: str) -> str:
    if entry.startswith(SKILL_PREFIX):
        return "research-writing/" + entry[len(SKILL_PREFIX) :]
    return PurePosixPath(entry).as_posix()


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _is_linklike(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        if sys.version_info >= (3, 12) and path.is_junction():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _identity(path: Path, status: os.stat_result | None = None) -> FileIdentity:
    if status is None:
        status = path.stat(follow_symlinks=False)
    return FileIdentity(
        resolved_path=os.path.normcase(os.fspath(path.resolve(strict=True))),
        device=status.st_dev,
        inode=status.st_ino,
        mode=status.st_mode,
        size=status.st_size,
        modified_ns=status.st_mtime_ns,
    )


def _stable_stat_signature(status: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_size,
        status.st_mtime_ns,
    )


def _read_stable_file(path: Path) -> tuple[bytes, FileIdentity]:
    if _is_linklike(path):
        raise ValueError(f"release input became linked: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if _stable_stat_signature(before) != _stable_stat_signature(after):
        raise ValueError(f"release input changed while being read: {path}")
    opened_identity = _identity(path, before)
    if _is_linklike(path) or _identity(path) != opened_identity:
        raise ValueError(f"release input identity changed while being read: {path}")
    return b"".join(chunks), opened_identity


def _source_signature(
    sources: tuple[tuple[object, Path], ...],
) -> tuple[tuple[int, str, str], ...]:
    return tuple(
        (
            record.line_number,
            record.value,
            os.path.normcase(os.fspath(_absolute(path))),
        )
        for record, path in sources
    )


def _capture_release_snapshot() -> ReleaseSnapshot:
    manifest_bytes, source_records = safe_release_source_records(ROOT)
    stable_manifest_bytes, manifest_identity = _read_stable_file(
        ROOT / "release-manifest.txt"
    )
    if stable_manifest_bytes != manifest_bytes:
        raise ValueError("release manifest changed while capturing the release snapshot")

    payloads: list[SnapshotPayload] = []
    for record, source in source_records:
        data, identity = _read_stable_file(source)
        payloads.append(
            SnapshotPayload(
                entry=record.value,
                archive_name=archive_name(record.value),
                source=source,
                identity=identity,
                data=data,
            )
        )

    confirmed_manifest, confirmed_sources = safe_release_source_records(ROOT)
    confirmed_manifest_bytes, confirmed_manifest_identity = _read_stable_file(
        ROOT / "release-manifest.txt"
    )
    if (
        confirmed_manifest != manifest_bytes
        or confirmed_manifest_bytes != manifest_bytes
        or confirmed_manifest_identity != manifest_identity
        or _source_signature(confirmed_sources) != _source_signature(source_records)
    ):
        raise ValueError("release inputs changed while capturing the release snapshot")
    return ReleaseSnapshot(
        manifest_bytes=manifest_bytes,
        manifest_identity=manifest_identity,
        entries=tuple(record.value for record, _source in source_records),
        payloads=tuple(payloads),
    )


def _validate_release_snapshot(snapshot: ReleaseSnapshot) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="research-writing-snapshot-") as raw:
        snapshot_root = Path(raw)
        resolved_snapshot_root = snapshot_root.resolve(strict=True)
        (snapshot_root / "release-manifest.txt").write_bytes(snapshot.manifest_bytes)
        for payload in snapshot.payloads:
            relative = PurePosixPath(payload.entry)
            target = snapshot_root.joinpath(*relative.parts)
            resolved_target = target.resolve(strict=False)
            if not resolved_target.is_relative_to(resolved_snapshot_root):
                raise ValueError(
                    f"release snapshot entry escapes temporary root: {payload.entry}"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload.data)
        return validate_repository(snapshot_root)


def _validate_output_path(output: Path, input_paths: list[Path]) -> Path:
    output = _absolute(output)
    resolved_output = output.resolve(strict=False)
    root_absolute = _absolute(ROOT)
    resolved_root = root_absolute.resolve(strict=True)
    dist_absolute = root_absolute / "dist"
    resolved_dist = dist_absolute.resolve(strict=False)

    is_lexically_in_root = output.is_relative_to(root_absolute)
    is_resolved_in_root = resolved_output.is_relative_to(resolved_root)
    if is_lexically_in_root:
        current = root_absolute
        for part in output.relative_to(root_absolute).parts:
            current = current / part
            if _is_linklike(current):
                raise ValueError(
                    "repository-local output has a symlink, junction, or "
                    f"reparse-point ancestor: {current.relative_to(root_absolute).as_posix()}"
                )
    if is_lexically_in_root or is_resolved_in_root:
        if resolved_output == resolved_dist or not resolved_output.is_relative_to(resolved_dist):
            raise ValueError("repository-local output must be inside the resolved dist directory")

    if output.is_symlink():
        raise ValueError("release output must not be a symlink")
    if sys.version_info >= (3, 12) and output.is_junction():
        raise ValueError("release output must not be a junction")
    if output.exists() and not output.is_file():
        raise ValueError("release output must be a regular file path")

    if output.exists():
        for input_path in input_paths:
            try:
                aliases_input = output.samefile(input_path)
            except OSError:
                aliases_input = False
            if aliases_input:
                raise ValueError(
                    f"release output aliases repository input {input_path.relative_to(ROOT).as_posix()}"
                )
    return output


def _write_archive(
    temporary_output: Path, payloads: list[tuple[str, bytes]]
) -> None:
    with zipfile.ZipFile(temporary_output, "w") as archive:
        for name, data in payloads:
            info = zipfile.ZipInfo(name, date_time=FIXED_TIMESTAMP)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def _verify_archive(temporary_output: Path, payloads: list[tuple[str, bytes]]) -> None:
    expected_names = [name for name, _data in payloads]
    with zipfile.ZipFile(temporary_output, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if names != expected_names:
            raise ValueError("release archive members do not match the manifest")
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ValueError(f"release archive contains a corrupt member: {corrupt_member}")
        for info, (expected_name, expected_data) in zip(infos, payloads, strict=True):
            if info.filename != expected_name or archive.read(info) != expected_data:
                raise ValueError(f"release archive member verification failed: {expected_name}")
            if info.date_time != FIXED_TIMESTAMP:
                raise ValueError(f"release archive timestamp mismatch: {expected_name}")
            if info.create_system != 3:
                raise ValueError(f"release archive platform mismatch: {expected_name}")
            if info.compress_type != zipfile.ZIP_STORED:
                raise ValueError(f"release archive compression mismatch: {expected_name}")
            if info.external_attr != 0o100644 << 16:
                raise ValueError(f"release archive mode mismatch: {expected_name}")


def build_release(output: Path) -> Path:
    snapshot = _capture_release_snapshot()
    snapshot_errors = _validate_release_snapshot(snapshot)
    if snapshot_errors:
        raise ValueError("; ".join(snapshot_errors))
    errors = validate_repository()
    if errors:
        raise ValueError("; ".join(errors))
    validated_snapshot = _capture_release_snapshot()
    if validated_snapshot != snapshot:
        raise ValueError("release inputs changed during repository validation")

    source_paths = [payload.source for payload in snapshot.payloads]
    control_paths = [ROOT / "release-manifest.txt"]
    output = _validate_output_path(Path(output), source_paths + control_paths)
    payloads = [(payload.archive_name, payload.data) for payload in snapshot.payloads]

    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    temporary_output = Path(raw_temporary)
    try:
        _write_archive(temporary_output, payloads)
        _verify_archive(temporary_output, payloads)
        if _capture_release_snapshot() != snapshot:
            raise ValueError("release inputs changed while building the release archive")
        _validate_output_path(output, source_paths + control_paths)
        os.replace(temporary_output, output)
    except BaseException:
        temporary_output.unlink(missing_ok=True)
        raise
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic Skill release archive.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / "research-writing.zip",
        help="Path to the output ZIP archive.",
    )
    args = parser.parse_args(argv)
    try:
        output = build_release(args.output)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
