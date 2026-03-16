"""Carpeta de descargas por lista (~/Downloads/<lista>), búsqueda de .xls existentes y espera/renombrado de nuevos."""
from pathlib import Path
from datetime import datetime
import time

from .naming import expected_filename_for  # si lo necesitas después


DOWNLOAD_POLL_INTERVAL = 1.0
DOWNLOAD_WAIT_TIMEOUT = 120


def downloads_folder_for_subfolder(subfolder: str) -> Path:
    """Devuelve ~/Downloads/<subfolder>, creando el directorio si no existe (ej. P5, P12)."""
    home = Path.home()
    downloads = home / "Downloads"
    target = downloads / subfolder
    target.mkdir(parents=True, exist_ok=True)
    return target


def find_existing_files_for_code(download_dir: Path, code: str, expected_name: str):
    """Busca un .xls ya descargado para el código: nombre exacto o glob *{code}*.xls. Retorna lista de Paths."""
    exact = download_dir / expected_name
    if exact.exists():
        return [exact]
    found = list(download_dir.glob(f"*{code}*.xls"))
    return found


def wait_for_new_xls_and_rename(
    download_dir: Path,
    expected_name: str,
    timeout: float = DOWNLOAD_WAIT_TIMEOUT,
):
    """Espera un nuevo .xls (sin .crdownload), lo renombra a expected_name y retorna el path final."""
    deadline = time.time() + timeout
    seen_before = set(download_dir.iterdir())

    while time.time() < deadline:
        crdownloads = list(download_dir.glob("*.crdownload"))
        if crdownloads:
            time.sleep(DOWNLOAD_POLL_INTERVAL)
            continue

        xls_files = [p for p in download_dir.glob("*.xls") if p not in seen_before]
        if xls_files:
            xls_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            found = xls_files[0]
            target = download_dir / expected_name

            if target.exists():
                timestamp = datetime.now().strftime("%H%M%S")
                target = download_dir / f"{target.stem}_{timestamp}{target.suffix}"

            found.rename(target)
            return target

        time.sleep(DOWNLOAD_POLL_INTERVAL)

    return None