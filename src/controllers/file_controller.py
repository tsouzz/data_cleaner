from src.services.file_service import FileService


class FileController:

    def __init__(self):
        self.service = FileService()

    def scan(self, directory: str):
        try:
            result = self.service.scan_and_save(directory)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def exact_duplicates(self):
        try:
            groups = self.service.find_exact_duplicate_groups()
            return {"status": "success", "data": groups}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run_full_pipeline(self, directory: str):
        try:
            result = self.service.run_full_pipeline(directory)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
