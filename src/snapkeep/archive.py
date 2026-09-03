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
    """Build a timestamped snapshot archive name."""
    if timestamp is None:
        timestamp = datetime.now()

    project_name = name if name is not None else source.name or "snapshot"
    stamp = timestamp.strftime("%Y%m%d-%H%M%S")

    return f"{project_name}_BACKUP_{stamp}.zip"

def create_archive(
    source: Path,
    files: Iterable[Path],
    destination: Path,
    *,
    timestamp: Optional[datetime] = None,
    name: Optional[str] = None,
) -> Path:
    """Create and verify a ZIP snapshot."""
    archive_name = build_archive_name(
        source,
        timestamp=timestamp,
        name=name,
    )

    archive_path = choose_archive_path(
        destination,
        archive_name,
    )

    try:
        destination.mkdir(parents=True, exist_ok=True)

        with ZipFile(
            archive_path,
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
        _remove_partial_archive(archive_path)
        raise

    except (OSError, ValueError, BadZipFile) as error:
        _remove_partial_archive(archive_path)
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


def _remove_partial_archive(archive_path: Path) -> None:
    """Best-effort cleanup of an incomplete archive."""
    try:
        archive_path.unlink(missing_ok=True)
    except OSError:
        pass

def choose_archive_path(
    destination: Path,
    archive_name: str,
) -> Path:
    """Choose a non-existing archive path without overwriting snapshots."""
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