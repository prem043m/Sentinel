from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class FileInfo:
    """Strongly typed model representing file or directory metadata.

    Attributes:
        name: The basename of the file or directory.
        path: The absolute canonical path.
        size: Size in bytes (0 for directories).
        extension: File extension including the dot (e.g., '.txt'), or empty string.
        is_directory: True if the path represents a directory.
        modified_at: Unix timestamp of the last modification.
    """
    name: str
    path: str
    size: int
    extension: str
    is_directory: bool
    modified_at: float
