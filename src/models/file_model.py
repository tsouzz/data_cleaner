from dataclasses import dataclass


@dataclass
class FileRecord:
    path: str
    name: str
    extension: str
    size: int
    created_at: str
    hash: str | None = None
