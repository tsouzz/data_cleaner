from pathlib import Path
import shutil


class CleaningService:

    TO_DELETE_FOLDER = "to_delete"

    def _cleanup_empty_parents(self, start_dir: Path, stop_at: Path) -> None:
        
        current = start_dir
        try:
            stop_at = stop_at.resolve()
        except Exception:
            return

        while True:
            try:
                current_resolved = current.resolve()
            except Exception:
                break

            if current_resolved == stop_at:
                break

            try:
                current.rmdir()
            except OSError:
                break

            parent = current.parent
            if parent == current:
                break
            current = parent

    def _move_under_drive_root(self, file_path: str, folder_name: str) -> dict:
        original = Path(file_path).resolve()
        if not original.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        drive_root = original.anchor
        drive_root_path = Path(drive_root).resolve()
        relative_path = original.relative_to(drive_root)

        destination = Path(drive_root) / folder_name / relative_path

        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(original), str(destination))
        
        self._cleanup_empty_parents(original.parent, drive_root_path)

        return {
            "original": str(original),
            "destination": str(destination),
        }

    def move_to_delete(self, file_path: str) -> dict:
        return self._move_under_drive_root(file_path, self.TO_DELETE_FOLDER)
