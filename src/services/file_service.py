import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.hasher import FileHasher
from src.core.scanner import FileScanner
from src.repositories.file_repository import FileRepository
from src.services.cleaning_service import CleaningService


class FileService:

    def __init__(self):
        self.scanner = FileScanner()
        self.hasher = FileHasher()
        self.repository = FileRepository()
        self.cleaning = CleaningService()
        self._save_batch_size = 500

    @staticmethod
    def _is_under_reserved_folder(path_str: str) -> bool:
        parts = Path(path_str).parts
        return CleaningService.TO_DELETE_FOLDER in parts

    def _hash_file(self, file_record):
        file_record.hash = self.hasher.calculate_blake3(file_record.path)
        return file_record

    def scan_and_save(self, directory: str):
        files = self.scanner.scan_directory(directory)
        batch = []

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = {executor.submit(self._hash_file, f): f for f in files}
            for future in as_completed(futures):
                try:
                    batch.append(future.result())
                    if len(batch) >= self._save_batch_size:
                        self.repository.save_many(batch)
                        batch = []
                except PermissionError as e:
                    print(f"[PERMISSION] Sem acesso: {futures[future].path}")
                except FileNotFoundError:
                    print(f"[NOT FOUND] Arquivo sumiu durante o scan: {futures[future].path}")
                except Exception as e:
                    print(f"[ERRO] {futures[future].path}: {e}")
        if batch:
            self.repository.save_many(batch)

        return {
            "directory": directory,
            "files_found": len(files),
        }

    def find_exact_duplicate_groups(self) -> list[dict]:
        return self.repository.find_exact_duplicate_groups()

    def run_full_pipeline(
        self,
        directory: str,
    ) -> dict:
        errors: list[str] = []
        moved_files: list[dict] = []

        scan_result = self.scan_and_save(directory)

        moved_to_delete = 0
        exact_groups = self.repository.find_exact_duplicate_groups()
        for g in exact_groups:
            files = list(g.get("files") or [])
            
            files = [f for f in files if not self._is_under_reserved_folder(f["path"])]
            if len(files) < 2:
                continue

            files_sorted = sorted(
                files,
                key=lambda f: (
                    f.get("created_at") is None,
                    f.get("created_at") or "",
                    f["path"],
                ),
            )
            
            keeper = files_sorted[0]["path"]
            for item in files_sorted[1:]:
                dup = item["path"]
                try:
                    r = self.cleaning.move_to_delete(dup)
                    if not self.repository.update_path(dup, r["destination"]):
                        errors.append(f"BD não atualizou path após mover: {dup}")
                    moved_files.append({
                        "duplicate": dup,
                        "moved_to": r["destination"],
                        "original_kept": keeper,
                    })
                except Exception as e:
                    errors.append(f"to_delete {dup}: {e}")

        return {
            "scan": scan_result,
            "exact_duplicate_groups": len(exact_groups),
            "moved_to_delete": moved_to_delete,
            "moved_files": moved_files,
            "errors": errors,
        }
