import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile

from snapkeep.errors import ArchiveError, ArchiveVerificationError


def build_archive_name(
    source: Path,
    *,
    timestamp: Optional[datetime] = None,
    name: Optional[str] = None,
) -> str:
    """Build the timestamped archive filename."""
    if timestamp is None:
        timestamp = datetime.now()

    base_name = name if name is not None else source.name
    timestamp_text = timestamp.strftime("%Y%m%d-%H%M%S")

    return f"{base_name}_BACKUP_{timestamp_text}.zip"


def create_archive(
    source: Path,
    files: Iterable[Path],
    destination: Path,
    *,
    timestamp: Optional[datetime] = None,
    name: Optional[str] = None,
) -> Path:
    """Create and verify a ZIP snapshot without replacing existing files."""
    archive_name = build_archive_name(
        source,
        timestamp=timestamp,
        name=name,
    )

    archive_path: Optional[Path] = None
    owned_identity: Optional[tuple[int, int]] = None

    try:
        destination.mkdir(parents=True, exist_ok=True)

        # choose_archive_path is a convenience for the usual case. O_EXCL is
        # the actual guarantee: it atomically reserves a name without
        # truncating an archive created by another process.
        archive_path = choose_archive_path(destination, archive_name)

        while True:
            try:
                descriptor = os.open(
                    str(archive_path),
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o666,
                )
            except FileExistsError:
                archive_path = choose_archive_path(destination, archive_name)
                continue

            file_stat = os.fstat(descriptor)
            owned_identity = (file_stat.st_dev, file_stat.st_ino)
            break

        with os.fdopen(descriptor, "w+b") as output:
            with ZipFile(
                output,
                mode="w",
                compression=ZIP_DEFLATED,
            ) as archive:
                for path in files:
                    relative_path = path.relative_to(source)
                    archive.write(
                        path,
                        arcname=relative_path.as_posix(),
                    )

        verify_archive(archive_path)

    except ArchiveVerificationError:
        _remove_partial_archive(archive_path, owned_identity)
        raise

    except (OSError, ValueError, BadZipFile, UnicodeError) as error:
        _remove_partial_archive(archive_path, owned_identity)
        raise ArchiveError(
            f"could not create snapshot archive: {error}"
        ) from error

    return archive_path


def verify_archive(archive_path: Path) -> None:
    """Raise an error if a ZIP archive fails integrity verification."""
    try:
        with ZipFile(archive_path, mode="r") as archive:
            bad_file = archive.testzip()
    except (OSError, BadZipFile) as error:
        raise ArchiveVerificationError(
            f"archive verification failed: {error}"
        ) from error

    if bad_file is not None:
        raise ArchiveVerificationError(
            f"archive verification failed at: {bad_file}"
        )


def _remove_partial_archive(
    archive_path: Optional[Path],
    owned_identity: Optional[tuple[int, int]],
) -> None:
    """Remove only the incomplete file created by this operation."""
    if archive_path is None or owned_identity is None:
        return

    try:
        file_stat = archive_path.lstat()
        if (file_stat.st_dev, file_stat.st_ino) == owned_identity:
            archive_path.unlink()
    except OSError:
        # Cleanup is best effort. Never remove a replacement file.
        pass


def choose_archive_path(
    destination: Path,
    archive_name: str,
) -> Path:
    """Choose a currently unused archive name without reserving it."""
    archive_path = destination / archive_name

    if not archive_path.exists():
        return archive_path

    stem = archive_path.stem
    suffix = archive_path.suffix
    counter = 1

    while True:
        candidate = destination / f"{stem}-{counter}{suffix}"

        if not candidate.exists():
            return candidate

        counter += 1
