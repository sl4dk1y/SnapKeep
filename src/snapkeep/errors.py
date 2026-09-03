class SnapKeepError(Exception):
    """Base exception for expected SnapKeep failures."""


class ArchiveError(SnapKeepError):
    """Raised when a snapshot archive cannot be created."""


class ArchiveVerificationError(ArchiveError):
    """Raised when a created archive fails integrity verification."""
