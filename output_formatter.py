#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import textwrap
from typing import List, Dict, Any, Optional
from datetime import datetime


class OutputFormatter:
    """
    Format dell’output finale in tabella ASCII con evidenziazione dei mismatch
    e tabella separata per duplicati di definizione.
    Implementa wrapping interno delle celle troppo lunghe.
    """

    RED_START = "\033[31m"
    RED_END = "\033[0m"
    ALERT_EMOJI = " 🚨"

    def __init__(self, wrap_width: int = 40):
        """
        wrap_width: numero massimo di caratteri per cella prima del wrapping
        """
        self.wrap_width = wrap_width

    def format(
        self,
        *,
        inline_map: List[Dict[str, Any]],
        style: str = "table",
        unused_defs: Optional[List[str]] = None,
        mismatches: Optional[List[Dict[str, Any]]] = None,
        duplicates: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Genera la tabella ASCII completa, con wrapping automatico:
          - style in ("table","plain","txt") → sempre table
          - Tabella principale: titolo, descrizione, underscore, dati, separatore
          - Se 'duplicates' non vuoto, aggiunge tabella duplicati con stesso schema.
        """
        st = style.lower()
        if st not in ("table", "plain", "txt"):
            raise ValueError(f"Solo 'table'|'plain'|'txt' supportati, non: {style!r}")

        mismatches = mismatches or []
        duplicates = duplicates or []

        # Mappa dei mismatch
        mm = {(m["function"], m["line"]): m for m in mismatches}
        severe = {
            k for k, m in mm.items()
            if ("undefined" in m["issue"].lower()
                or abs(m.get("actual", 0) - m.get("expected", 0)) > 1)
        }

        # Costruzione righe logiche con data file
        data_rows: List[List[str]] = []
        idx = 1
        for fn in inline_map:
            func = fn["func_name"]
            file_def = fn["file"]
            line_def = fn["lineno"]
            created: datetime = fn.get("created", datetime.min)
            modified: datetime = fn.get("last_modified", datetime.min)
            date_cell = (f"Ult.mod: {modified:%d-%m-%Y}; "
                         f"Creaz: {created:%d-%m-%Y}")
            sig = fn.get("signature", [])
            sig_str = f"({', '.join(sig)})" if sig else "(nessuno)"
            lang = fn.get("language", "")
            calls = fn.get("calls", [])

            if not calls:
                data_rows.append([
                    str(idx), "definizione", func,
                    file_def, date_cell, str(line_def),
                    sig_str, "", "", "", lang, "OK"
                ])
                idx += 1
            else:
                for c in calls:
                    call_file = c.get("caller_file", "")
                    call_line = c.get("caller_lineno", "")
                    args = c.get("args", [])
                    args_str = f"({', '.join(args)})" if args else "(nessuno)"
                    key = (func, call_line)
                    if key in mm:
                        label = f"{self.RED_START}MISMATCH{self.RED_END}"
                        if key in severe:
                            label += self.ALERT_EMOJI
                    else:
                        label = "OK"
                    data_rows.append([
                        str(idx), "richiamo", func,
                        file_def, date_cell, str(line_def),
                        sig_str, call_file, str(call_line),
                        args_str, lang, label
                    ])
                    idx += 1

        # Definizione header e descrizioni
        headers = [
            "#", "Tipo", "Funzione", "File def.", "Date file", "Riga def.",
            "Parametri definiti", "File rich.", "Riga rich.",
            "Parametri pass.", "Lang", "Congruenza"
        ]
        descriptions = [
            "Indice progressivo",
            "Definizione o richiamo",
            "Nome funzione",
            "Path file definizione",
            "Ultima modifica & creazione file",
            "Linea dove è definita",
            "Parametri formali dichiarati",
            "File della richiamata",
            "Linea della chiamata",
            "Parametri effettivi passati",
            "Linguaggio (py/php)",
            "OK o segnalazione MISMATCH"
        ]

        # Wrap dati per la tabella principale
        wrapped_main = [
            [textwrap.wrap(cell, self.wrap_width) or [''] for cell in row]
            for row in data_rows
        ]

        # Costruisci sub-righe per dati
        main_subrows: List[List[str]] = []
        cols = len(headers)
        for group in wrapped_main:
            height = max(len(col) for col in group)
            for i in range(height):
                main_subrows.append([
                    group[j][i] if i < len(group[j]) else ''
                    for j in range(cols)
                ])

        # Calcola larghezze colonne
        widths = [0] * cols
        for i in range(cols):
            widths[i] = max(
                len(headers[i]),
                len(descriptions[i]),
                *(len(r[i]) for r in main_subrows)
            )

        # Separatori
        sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        under_sep = "+" + "+".join("_" * (w + 2) for w in widths) + "+"

        out: List[str] = []
        # Margine superiore
        out.extend(["", "", ""])
        # Titoli
        out.append("|" + "|".join(f" {headers[i].ljust(widths[i])} "
                                 for i in range(cols)) + "|")
        # Descrizioni
        out.append("|" + "|".join(f" {descriptions[i].ljust(widths[i])} "
                                 for i in range(cols)) + "|")
        # Linea di underscore
        out.append(under_sep)
        # Dati
        for row in main_subrows:
            out.append("|" + "|".join(f" {row[i].ljust(widths[i])} "
                                     for i in range(cols)) + "|")
        # Linea di separazione finale
        out.append(sep)

        # Tabella duplicati
        if duplicates:
            dup_headers = ["Funzione", "File principale", "Duplicato in"]
            dup_desc = [
                "Funzione principale",
                "File dove originariamente definita",
                "Percorso file duplicato"
            ]
            # Prepara righe duplicati
            dup_rows = []
            for d in duplicates:
                dup_rows.append([
                    d["func_name"],
                    os.path.basename(d.get("original_file", d["file"])),
                    d["file"]
                ])

            # Wrap e sub-righe duplicati
            wrapped_dup = [
                [textwrap.wrap(cell, self.wrap_width) or [''] for cell in dup_headers],
                [textwrap.wrap(cell, self.wrap_width) or [''] for cell in dup_desc]
            ]
            for row in dup_rows:
                wrapped_dup.append([
                    textwrap.wrap(cell, self.wrap_width) or ['']
                    for cell in row
                ])

            dup_sub: List[List[str]] = []
            for group in wrapped_dup:
                h = max(len(col) for col in group)
                for i in range(h):
                    dup_sub.append([
                        group[j][i] if i < len(group[j]) else '' for j in range(3)
                    ])

            dup_w = [0] * 3
            for i in range(3):
                dup_w[i] = max(
                    len(dup_headers[i]),
                    len(dup_desc[i]),
                    *(len(r[i]) for r in dup_sub)
                )

            dup_sep = "+" + "+".join("-" * (w + 2) for w in dup_w) + "+"
            dup_under = "+" + "+".join("_" * (w + 2) for w in dup_w) + "+"

            # Margine e header duplicati
            out.extend(["", "", ""])
            out.append("|" + "|".join(f" {dup_headers[i].ljust(dup_w[i])} "
                                     for i in range(3)) + "|")
            out.append("|" + "|".join(f" {dup_desc[i].ljust(dup_w[i])} "
                                     for i in range(3)) + "|")
            out.append(dup_under)
            # Righe duplicati
            for row in dup_sub:
                out.append("|" + "|".join(f" {row[i].ljust(dup_w[i])} "
                                         for i in range(3)) + "|")
            out.append(dup_sep)

        return "\n".join(out)
