import os
from blake3 import blake3
from pathlib import Path


class FileHasher:

    CHUNK_SIZE = 8 * 1024 * 1024  

    def calculate_blake3(self, file_path: str) -> str:
        return self.calculate_full_hash(file_path)

    def calculate_full_hash(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        hasher = blake3(max_threads=os.cpu_count())

        with path.open("rb") as file:
            while chunk := file.read(self.CHUNK_SIZE):
                hasher.update(chunk)

        return hasher.hexdigest()