#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import textwrap
from typing import List, Dict, Any, Optional
from datetime import datetime


class OutputFormatter:
    """
    Formats the final output as ASCII tables with:
      - a main table showing function definitions and calls,
      - an optional duplicates table listing duplicate definitions.
    Cells are wrapped to a maximum width.
    """

    RED_START = "\033[31m"
    RED_END = "\033[0m"
    ALERT_EMOJI = " 🚨"

    def __init__(self, wrap_width: int = 40):
        """
        :param wrap_width: max characters per cell before wrapping
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
        Generate the ASCII report.

        :param inline_map: list of dicts with keys:
            - func_name, file, created, last_modified, lineno,
              signature (List[str]), calls (List[Dict])
        :param style: must be "table", "plain", or "txt"
        :param mismatches: list of dicts with keys "function", "line", etc.
        :param duplicates: list of dicts with keys "func_name", "file", "lineno",
                           and optionally "original_file"
        :return: multi-line ASCII string
        """
        st = style.lower()
        if st not in ("table", "plain", "txt"):
            raise ValueError(f"Only 'table'|'plain'|'txt' supported, not: {style!r}")

        mismatches = mismatches or []
        duplicates = duplicates or []

        # Build mismatch lookup
        mm = {(m["function"], m["line"]): m for m in mismatches}
        severe = {
            key for key, m in mm.items()
            if ("undefined" in m["issue"].lower()
                or abs(m.get("actual", 0) - m.get("expected", 0)) > 1)
        }

        # Build main data rows
        data_rows: List[List[str]] = []
        idx = 1
        for fn in inline_map:
            func = fn["func_name"]
            file_def = fn["file"]
            line_def = fn["lineno"]
            created: datetime = fn.get("created", datetime.min)
            modified: datetime = fn.get("last_modified", datetime.min)
            date_cell = f"Mod: {modified:%d-%m-%Y}; Cr: {created:%d-%m-%Y}"
            sig = fn.get("signature", [])
            sig_str = f"({', '.join(sig)})" if sig else "()"
            lang = fn.get("language", "")
            calls = fn.get("calls", [])

            if not calls:
                data_rows.append([
                    str(idx), "definition", func,
                    file_def, date_cell, str(line_def),
                    sig_str, "", "", "", lang, "OK"
                ])
                idx += 1
            else:
                for c in calls:
                    call_file = c.get("caller_file", "")
                    call_line = c.get("caller_lineno", "")
                    args = c.get("args", [])
                    args_str = f"({', '.join(args)})" if args else "()"
                    key = (func, call_line)
                    if key in mm:
                        status = f"{self.RED_START}MISMATCH{self.RED_END}"
                        if key in severe:
                            status += self.ALERT_EMOJI
                    else:
                        status = "OK"
                    data_rows.append([
                        str(idx), "call", func,
                        file_def, date_cell, str(line_def),
                        sig_str, call_file, str(call_line),
                        args_str, lang, status
                    ])
                    idx += 1

        # Define headers and descriptions
        headers = [
            "#", "Type", "Function", "Def. file", "File dates", "Def. line",
            "Signature", "Call file", "Call line", "Call args", "Lang", "Status"
        ]
        descriptions = [
            "Row index",
            "definition or call",
            "function name",
            "file path of definition",
            "modified & created dates",
            "line of definition",
            "declared signature",
            "file path of call",
            "line of call",
            "arguments passed",
            "language (py/php)",
            "OK or MISMATCH"
        ]

        # Wrap main rows
        wrapped_main = [
            [textwrap.wrap(cell, self.wrap_width) or [''] for cell in row]
            for row in data_rows
        ]

        # Build subrows for main table
        main_subrows: List[List[str]] = []
        cols = len(headers)
        for group in wrapped_main:
            height = max(len(col) for col in group)
            for i in range(height):
                main_subrows.append([
                    group[j][i] if i < len(group[j]) else ''
                    for j in range(cols)
                ])

        # Compute column widths
        widths = [0] * cols
        for i in range(cols):
            widths[i] = max(
                len(headers[i]),
                len(descriptions[i]),
                *(len(r[i]) for r in main_subrows)
            )

        # Build separators
        sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        under_sep = "+" + "+".join("_" * (w + 2) for w in widths) + "+"

        out: List[str] = []
        # Top margin
        out.extend(["", "", ""])
        # Header titles
        out.append("|" + "|".join(f" {headers[i].ljust(widths[i])} " for i in range(cols)) + "|")
        # Header descriptions
        out.append("|" + "|".join(f" {descriptions[i].ljust(widths[i])} " for i in range(cols)) + "|")
        # Underline
        out.append(under_sep)
        # Data rows
        for row in main_subrows:
            out.append("|" + "|".join(f" {row[i].ljust(widths[i])} " for i in range(cols)) + "|")
        # Bottom separator
        out.append(sep)

        # Duplicates table (if any)
        if duplicates:
            dup_headers = ["Function", "Original file", "Duplicate"]
            dup_desc = ["function name", "file of definition", "path of duplicate"]
            # Wrap duplicates
            wrapped_dup = [
                [textwrap.wrap(cell, self.wrap_width) or [''] for cell in dup_headers],
                [textwrap.wrap(cell, self.wrap_width) or [''] for cell in dup_desc]
            ]
            for d in duplicates:
                orig = d.get("original_file", d["file"])
                wrapped_dup.append([
                    textwrap.wrap(d["func_name"], self.wrap_width) or [''],
                    textwrap.wrap(orig, self.wrap_width) or [''],
                    textwrap.wrap(d["file"], self.wrap_width) or ['']
                ])

            # Build subrows for duplicates
            dup_sub: List[List[str]] = []
            for group in wrapped_dup:
                height = max(len(col) for col in group)
                for i in range(height):
                    dup_sub.append([
                        group[j][i] if i < len(group[j]) else '' for j in range(3)
                    ])

            # Compute widths
            dup_w = [0] * 3
            for i in range(3):
                dup_w[i] = max(
                    len(dup_headers[i]),
                    len(dup_desc[i]),
                    *(len(r[i]) for r in dup_sub)
                )

            dup_sep = "+" + "+".join("-" * (w + 2) for w in dup_w) + "+"
            dup_under = "+" + "+".join("_" * (w + 2) for w in dup_w) + "+"

            # Spacer and headers
            out.extend(["", "", ""])
            out.append("|" + "|".join(f" {dup_headers[i].ljust(dup_w[i])} " for i in range(3)) + "|")
            out.append("|" + "|".join(f" {dup_desc[i].ljust(dup_w[i])} " for i in range(3)) + "|")
            out.append(dup_under)
            # Duplicate rows
            for row in dup_sub:
                out.append("|" + "|".join(f" {row[i].ljust(dup_w[i])} " for i in range(3)) + "|")
            out.append(dup_sep)

        return "\n".join(out)
