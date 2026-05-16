from pathlib import Path

from src.database.connection import get_connection
from src.models.file_model import FileRecord


class FileRepository:

    _UPSERT_SQL = """
            INSERT INTO files (
                path, name, extension, size, created_at,
                hash
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                name = excluded.name,
                extension = excluded.extension,
                size = excluded.size,
                created_at = excluded.created_at,
                hash = excluded.hash
            """

    def save(self, file_record: FileRecord):
        self.save_many([file_record])

    def save_many(self, records: list[FileRecord]):
        if not records:
            return
        with get_connection() as conn:
            conn.executemany(
                self._UPSERT_SQL,
                [
                    (
                        r.path,
                        r.name,
                        r.extension,
                        r.size,
                        r.created_at,
                        r.hash,
                    )
                    for r in records
                ],
            )

    def update_path(self, old_path: str, new_path: str) -> bool:
        name = Path(new_path).name
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE files SET path = ?, name = ? WHERE path = ?",
                (new_path, name, old_path),
            )
            return cursor.rowcount > 0

    def find_exact_duplicate_groups(self) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT f.path, f.hash, f.size, f.created_at
                FROM files f
                INNER JOIN (
                    SELECT hash FROM files
                    WHERE hash IS NOT NULL AND hash != ''
                    GROUP BY hash
                    HAVING COUNT(*) > 1
                ) d ON f.hash = d.hash
                ORDER BY f.hash, f.created_at, f.path
                """
            )
            rows = [dict(r) for r in cursor.fetchall()]

        groups: list[dict] = []
        current_hash = None
        bucket: list[dict] = []
        for row in rows:
            h = row["hash"]
            if h != current_hash:
                if bucket:
                    groups.append(
                        {
                            "hash": current_hash,
                            "files": bucket,
                            "paths": [f["path"] for f in bucket],
                        }
                    )
                current_hash = h
                bucket = []
            bucket.append(
                {
                    "path": row["path"],
                    "created_at": row.get("created_at"),
                    "size": row.get("size"),
                }
            )
        if bucket:
            groups.append(
                {
                    "hash": current_hash,
                    "files": bucket,
                    "paths": [f["path"] for f in bucket],
                }
            )
        return groups

    def list_rows_with_hashes(self) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT path, hash
                FROM files
                WHERE hash IS NOT NULL
                AND hash != ''
                """
            )
            return [dict(r) for r in cursor.fetchall()]
