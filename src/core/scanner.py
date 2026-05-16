import os
from datetime import datetime, timezone
from pathlib import Path

from src.models.file_model import FileRecord
from src.services.cleaning_service import CleaningService


class FileScanner:

    def scan_directory(self, root: str) -> list[FileRecord]:
        root_path = Path(root).resolve()
        if not root_path.is_dir():
            raise NotADirectoryError(f"Não é uma pasta: {root}")

        records: list[FileRecord] = []
        for dirpath, dirnames, filenames in os.walk(
            root_path, topdown=True, followlinks=False
        ):
            dirnames[:] = [
                d for d in dirnames 
                if not d.startswith(".") and d != CleaningService.TO_DELETE_FOLDER
                ]
            
            for name in filenames:
                path = Path(dirpath) / name
                try:
                    stat = path.stat()
                except OSError:
                    continue
                if not path.is_file():
                    continue
                ext = path.suffix.lower()
                created = datetime.fromtimestamp(
                    stat.st_ctime, tz=timezone.utc
                ).isoformat()
                records.append(
                    FileRecord(
                        path=str(path),
                        name=name,
                        extension=ext,
                        size=stat.st_size,
                        created_at=created,
                    )
                )
        return records
