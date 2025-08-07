# file_crawler.py

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    import chardet
    _HAS_CHARDET = True
except ImportError:
    _HAS_CHARDET = False

DEFAULT_EXCLUDE_DIRS = ['.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules']
MAX_FILE_SIZE_KB = 2000


def get_code_files(
    input_dir: str,
    exclude_dirs: Optional[List[str]] = None,
    max_file_size_kb: int = MAX_FILE_SIZE_KB
) -> List[Dict]:
    """
    Scansiona ricorsivamente la directory di progetto per file .py e .php,
    escludendo:
      - directory di sistema o virtualenv
      - file temporanei (.swp, ~)
      - file troppo grandi o non leggibili

    Ritorna per ciascun file un dict con:
      - path: percorso assoluto (str)
      - language: "py" o "php"
      - created: datetime di creazione file
      - last_modified: datetime di ultima modifica file
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    root = Path(input_dir)
    if not root.is_dir():
        raise ValueError(f"Percorso non valido o non-directory: {input_dir}")

    code_files: List[Dict] = []
    patterns = [
        ("*.py",  "py"),
        ("*.php", "php")
    ]

    for pattern, lang in patterns:
        for path in root.rglob(pattern):
            # Escludi directory indesiderate
            if any(part in exclude_dirs for part in path.parts):
                continue

            # Escludi file temporanei
            if path.name.endswith(('~', '.swp')):
                continue

            # Filtra dimensione file
            try:
                stats = path.stat()
                size_kb = stats.st_size / 1024
            except OSError:
                continue
            if size_kb == 0 or size_kb > max_file_size_kb:
                continue

            # Verifica leggibilità / encoding
            try:
                raw = path.read_bytes()
                if lang == "py" and _HAS_CHARDET:
                    enc = chardet.detect(raw).get("encoding") or "utf-8"
                else:
                    enc = "utf-8"
                raw.decode(enc)
            except Exception:
                logging.getLogger(__name__).warning(
                    f"file_crawler: salto file non leggibile {path}"
                )
                continue

            # Metadati filesystem
            created = datetime.fromtimestamp(stats.st_ctime)
            last_mod = datetime.fromtimestamp(stats.st_mtime)

            code_files.append({
                "path": str(path),
                "language": lang,
                "created": created,
                "last_modified": last_mod
            })

    # Ordina per percorso
    code_files.sort(key=lambda x: x["path"])
    return code_files
