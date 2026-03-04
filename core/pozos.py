from pathlib import Path
from datetime import datetime
import re

from .naming import parse_year_from_period


def load_pozos_map(path: str) -> dict:
    """
    Formato esperado por línea (TSV o espacios):
      CASUB-216    OB-0302-127    Gonzalo Moreno
    """
    pozos = {}
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            parts = re.split(r"\t+|\s{2,}", line)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) < 2:
                continue

            casub_tag = parts[0].upper()
            ob_code = parts[1].upper()
            name = parts[2].strip() if len(parts) >= 3 else ""

            pozos[ob_code] = {"casub_tag": casub_tag, "name": name}

    return pozos


def _norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", (s or "").upper())


def find_pozo_folder_in_bases(base_dirs: list[Path], ob_code: str, pozos_map: dict) -> Path | None:
    ob_norm = ob_code.strip().upper()
    info = pozos_map.get(ob_norm)
    casub_tag = info["casub_tag"] if info else None

    casub_key = _norm(casub_tag) if casub_tag else None
    ob_key = _norm(ob_norm)

    print(f"DEBUG search: ob={ob_norm} casub={casub_tag}")

    # 1) Primer nivel (rápido)
    for base in base_dirs:
        if not base.exists():
            continue
        try:
            for p in base.iterdir():
                if not p.is_dir():
                    continue
                pname = _norm(p.name)

                if casub_key and casub_key in pname:
                    return p
                if ob_key in pname:
                    return p
        except Exception:
            continue

    # 2) Fallback recursivo
    for base in base_dirs:
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if not p.is_dir():
                    continue
                pname = _norm(p.name)

                if casub_key and casub_key in pname:
                    return p
                if ob_key in pname:
                    return p
        except Exception:
            continue

    return None


def move_report_to_destination(
    renamed_file: Path,
    base_dirs: list[Path],
    ob_code: str,
    start: str,
    end: str,
    pozos_map: dict,
) -> Path | None:
    pozo_folder = find_pozo_folder_in_bases(base_dirs, ob_code, pozos_map)
    if not pozo_folder:
        return None

    year = parse_year_from_period(start, end)
    target_dir = pozo_folder / str(year)
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / renamed_file.name
    if target_path.exists():
        timestamp = datetime.now().strftime("%H%M%S")
        target_path = target_dir / f"{renamed_file.stem}_{timestamp}{renamed_file.suffix}"

    renamed_file.replace(target_path)
    return target_path