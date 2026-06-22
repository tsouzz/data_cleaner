import argparse
import logging
import sys
import time
from pathlib import Path

from src.controllers.file_controller import FileController
from src.database.connection import create_tables
from src.utils.logger import setup_logger

logger = logging.getLogger("media_cleaner")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="media_cleaner",
        description=(
            "Escaneia um diretório, calcula hashes BLAKE3 dos arquivos e "
            "move duplicatas exatas para uma pasta de quarentena (to_delete)."
        ),
    )
    parser.add_argument(
        "directory",
        help="Diretório a ser escaneado (caminho absoluto ou relativo).",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Apenas escaneia e grava hashes no banco, sem mover duplicatas.",
    )
    parser.add_argument(
        "--list-duplicates",
        action="store_true",
        help="Lista os grupos de duplicatas exatas já conhecidos sem escanear novamente.",
    )
    return parser


def _validate_directory(directory: str) -> None:
    path = Path(directory)
    if not path.exists():
        raise NotADirectoryError(f"Diretório não encontrado: {directory}")
    if not path.is_dir():
        raise NotADirectoryError(f"Não é uma pasta: {directory}")


def _log_scan_summary(directory: str, scan_data: dict, elapsed: float) -> None:
    logger.info("[SUCCESS]")
    logger.info("Diretório:              %s", directory)
    logger.info("Arquivos encontrados:   %d", scan_data.get("files_found", 0))
    logger.info("Tempo de execução:      %.2fs", elapsed)


def _log_duplicate_groups(groups: list[dict]) -> None:
    logger.info("Grupos de duplicatas:   %d", len(groups))
    if not groups:
        return
    logger.info("--- Grupos de duplicatas ---")
    for g in groups:
        logger.info("Hash: %s", g.get("hash"))
        for f in g.get("paths", []):
            logger.info("  %s", f)


def _log_pipeline_summary(directory: str, data: dict, elapsed: float) -> int:
    logger.info("[SUCCESS]")
    logger.info("Diretório:              %s", directory)
    logger.info("Arquivos encontrados:   %d", data["scan"].get("files_found", 0))
    logger.info("Grupos de duplicatas:   %d", data.get("exact_duplicate_groups", 0))
    logger.info("Arquivos movidos:       %d", len(data.get("moved_files", [])))

    moved_files = data.get("moved_files", [])
    if moved_files:
        logger.info("")
        logger.info("--- Arquivos movidos ---")
        for item in moved_files:
            logger.info("")
            logger.info("  Duplicata:    %s", item["duplicate"])
            logger.info("  Movido para:  %s", item["moved_to"])
            logger.info("  Original:     %s", item["original_kept"])

    errors = data.get("errors", [])
    if errors:
        logger.warning("")
        logger.warning("--- Erros (%d) ---", len(errors))
        for err in errors:
            logger.warning("  %s", err)

    logger.info("")
    logger.info("Tempo de execução:      %.2fs", elapsed)

    return 1 if errors else 0


def main() -> int:
    setup_logger()
    create_tables()
    parser = build_parser()
    args = parser.parse_args()

    controller = FileController()

    try:
        _validate_directory(args.directory)
    except NotADirectoryError as e:
        logger.error(str(e))
        return 1

    start = time.perf_counter()

    if args.list_duplicates:
        result = controller.exact_duplicates()
        elapsed = time.perf_counter() - start
        if result["status"] != "success":
            logger.error("Falha ao listar duplicatas: %s", result["message"])
            return 1
        _log_duplicate_groups(result["data"])
        logger.info("Tempo de execução:      %.2fs", elapsed)
        return 0

    if args.scan_only:
        logger.info("Iniciando scan em: %s", args.directory)
        result = controller.scan(args.directory)
        elapsed = time.perf_counter() - start
        if result["status"] != "success":
            logger.error("Falha no scan: %s", result["message"])
            return 1
        _log_scan_summary(args.directory, result["data"], elapsed)
        return 0

    logger.info("Iniciando scan em: %s", args.directory)
    result = controller.run_full_pipeline(args.directory)
    elapsed = time.perf_counter() - start

    if result["status"] != "success":
        logger.error("Falha no pipeline: %s", result["message"])
        return 1

    return _log_pipeline_summary(args.directory, result["data"], elapsed)


if __name__ == "__main__":
    sys.exit(main())
