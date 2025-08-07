# php_parser.py

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


class PHPParser:
    """
    Parser minimalista per file PHP, allineato a ASTParser:
      - Estrae definizioni di funzione (FunctionDef) con signature formale
      - Estrae chiamate a funzione (Call) con args reali
      - Aggiunge metadata filesystem (created, last_modified)
      - Mantiene per ogni definizione la lista di chiamate interne
    """

    _fn_def_re = re.compile(
        r'^\s*(?:public|protected|private|static|\s)*function\s+&?\s*'
        r'(?P<name>[A-Za-z_]\w*)\s*\((?P<params>[^\)]*)\)',
        re.IGNORECASE
    )
    _call_re = re.compile(r'(?P<name>[A-Za-z_]\w*)\s*\(')

    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Analizza un file .php e ritorna una lista di dict con i campi:
          - type: "FunctionDef" | "Call"
          - name: nome della funzione
          - lineno: numero di linea
          - file: percorso file
          - created: datetime di creazione file
          - last_modified: datetime di ultima modifica
          - signature: List[str] (solo per FunctionDef)
          - args: List[str] (solo per Call)
          - calls: List[str] (solo per FunctionDef)
        """
        path = Path(file_path)
        if not path.is_file():
            raise ValueError(f"PHPParser: file non trovato: {file_path}")

        # Metadata filesystem
        stats = path.stat()
        created = datetime.fromtimestamp(stats.st_ctime)
        last_modified = datetime.fromtimestamp(stats.st_mtime)

        # Lettura sorgente
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"PHPParser: impossibile leggere {file_path}: {e}")
            return []

        parsed: List[Dict] = []
        current_def: Dict = None

        for lineno, line in enumerate(source.splitlines(), start=1):
            # ===== Definizione funzione =====
            m_def = self._fn_def_re.match(line)
            if m_def:
                name = m_def.group("name")
                params = m_def.group("params").strip()
                # Costruisci signature formale
                signature = [
                    p.strip().split()[-1]
                    for p in params.split(",")
                    if p.strip()
                ]
                fn_dict = {
                    "type": "FunctionDef",
                    "name": name,
                    "lineno": lineno,
                    "file": file_path,
                    "created": created,
                    "last_modified": last_modified,
                    "signature": signature,
                    "calls": []
                }
                parsed.append(fn_dict)
                current_def = fn_dict
                continue

            # ===== Chiamate a funzione =====
            for m_call in self._call_re.finditer(line):
                call_name = m_call.group("name")
                if call_name.lower() in {
                    "if", "while", "for", "switch", "echo", "return", "array"
                }:
                    continue
                # Estrai args reali (approssimato)
                after = line[m_call.end():]
                paren = re.match(r'\s*(?P<inside>[^\)]*)\)', after)
                args = (
                    [a.strip() for a in paren.group("inside").split(",")]
                    if paren else []
                )
                call_dict = {
                    "type": "Call",
                    "name": call_name,
                    "lineno": lineno,
                    "file": file_path,
                    "created": created,
                    "last_modified": last_modified,
                    "args": args
                }
                parsed.append(call_dict)
                if current_def is not None:
                    current_def["calls"].append(call_name)

        return parsed
