from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from zipfile import ZIP_DEFLATED, ZipFile


def build_archive_name(
    source: Path,
    *,
    timestamp: Optional[datetime] = None,
) -> str:
    """Build a timestamped snapshot archive name."""
    if timestamp is None:
        timestamp = datetime.now()

    project_name = source.name or "snapshot"
    stamp = timestamp.strftime("%Y%m%d-%H%M%S")

    return f"{project_name}_BACKUP_{stamp}.zip"


def create_archive(
    source: Path,
    files: Iterable[Path],
    destination: Path,
    *,
    timestamp: Optional[datetime] = None,
) -> Path:
    """Create and verify a ZIP snapshot."""
    destination.mkdir(parents=True, exist_ok=True)

    archive_path = destination / build_archive_name(
        source,
        timestamp=timestamp,
    )

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

    return archive_path


def verify_archive(archive_path: Path) -> None:
    """Raise an error if a ZIP archive fails integrity verification."""
    with ZipFile(archive_path, mode="r") as archive:
        bad_file = archive.testzip()

    if bad_file is not None:
        raise ValueError(
            f"archive verification failed at: {bad_file}"
        )
