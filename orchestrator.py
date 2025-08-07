#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
orchestrator.py

Coordina l’intera pipeline:
 1) Crawl file
 2) Parse AST/PHP
 3) Map definizioni
 4) Build call graph & inline mapping
 5) Check congruenza parametri
 6) Format report
Mostra barra progresso globale e log tabellare degli stati.
"""

import os
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
from tqdm import tqdm

from file_crawler import get_code_files
from ast_parser import ASTParser
from php_parser import PHPParser
from function_mapper import FunctionMapper
from call_graph_builder import CallGraphBuilder
from param_checker import check_parameter_congruence
from output_formatter import OutputFormatter

# Esclusioni standard
DEFAULT_EXCLUDE_DIRS = {"__pycache__", ".git", "venv", "env", ".idea", "node_modules"}
VALID_FORMATS = {"table", "plain", "json", "tree", "csv", "txt"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run_orchestrator(directory_path: str, format_style: str) -> str:
    """
    Esegue la pipeline e restituisce il report ASCII colorato con evidenze.
    Accetta 'table', 'plain'/'txt', 'json', 'tree', 'csv'.
    Le modalità 'plain' e 'txt' sono alias di 'table'.
    """
    # Validazione
    if not os.path.isdir(directory_path):
        raise ValueError(f"Path non valido: {directory_path}")
    fmt = format_style.lower()
    if fmt not in VALID_FORMATS:
        raise ValueError(f"Formato non supportato: {format_style!r}")

    # Mappa alias plain/txt -> table
    style = "table" if fmt in {"plain", "txt"} else fmt

    statuses: List[Tuple[str, str, str]] = []
    code_files: List[Dict[str, Any]] = []
    parsed_nodes: List[Dict[str, Any]] = []
    function_map: List[Dict[str, Any]] = []
    call_graph: Dict[str, List[Dict[str, Any]]] = {}
    inline_map: List[Dict[str, Any]] = []
    unused_defs: List[str] = []
    mismatches: List[Dict[str, Any]] = []
    duplicates: List[Dict[str, Any]] = []
    report: str = ""

    # Fasi del workflow
    phases = ["Crawl", "Parse", "Map", "CallGraph", "Check", "Report"]

    with tqdm(total=len(phases), desc="Elaborazione", unit="step") as pbar:
        # 1) Crawl
        try:
            code_files = get_code_files(directory_path, exclude_dirs=DEFAULT_EXCLUDE_DIRS)
            statuses.append(("Crawl", "OK", f"{len(code_files)} file trovati"))
        except Exception as e:
            statuses.append(("Crawl", "ERROR", str(e)))
            logger.error("Errore in Crawl", exc_info=True)
            raise
        pbar.update(1)

        # 2) Parse
        try:
            parser_py = ASTParser()
            parser_php = PHPParser()
            for cf in code_files:
                nodes = parser_py.parse_file(cf["path"]) if cf["language"] == "py" \
                        else parser_php.parse_file(cf["path"])
                for n in nodes:
                    n["language"] = cf["language"]
                    n["last_modified"] = cf["last_modified"]
                parsed_nodes.extend(nodes)
            statuses.append(("Parse", "OK", f"{len(parsed_nodes)} nodi estratti"))
        except Exception as e:
            statuses.append(("Parse", "ERROR", str(e)))
            logger.error("Errore in Parse", exc_info=True)
            raise
        pbar.update(1)

        # 3) Map definizioni
        try:
            mapper = FunctionMapper()
            # ora restituisce anche 'duplicates'
            function_map, _, duplicates = mapper.map_functions(parsed_nodes, mode="full")
            # assegna metadata filesystem a ogni funzione
            file_info = {cf["path"]: cf for cf in code_files}
            for fn in function_map:
                info = file_info.get(fn["file"], {})
                fn["language"] = info.get("language", fn.get("language"))
                fn["created"] = info.get("created", fn.get("created", datetime.min))
                fn["last_modified"] = info.get("last_modified", fn.get("last_modified", datetime.min))
            statuses.append(("Map", "OK", f"{len(function_map)} funzioni mappate"))
        except Exception as e:
            statuses.append(("Map", "ERROR", str(e)))
            logger.error("Errore in Map", exc_info=True)
            raise
        pbar.update(1)

        # 4) Build call graph & inline
        try:
            builder = CallGraphBuilder()
            call_graph, unmatched = builder.build_call_graph(
                parsed_nodes,
                function_map,
                match_strategy="exact_name"
            )
            inline_map = builder.map_inline_def_calls(function_map, call_graph)
            statuses.append(
                ("CallGraph", "OK", f"{len(call_graph)} definizioni, {len(unmatched)} non matchate")
            )
        except Exception as e:
            statuses.append(("CallGraph", "ERROR", str(e)))
            logger.error("Errore in CallGraph", exc_info=True)
            raise
        pbar.update(1)

        # 5) Check congruenza parametri
        try:
            unused_defs, mismatches = check_parameter_congruence(function_map, call_graph)
            statuses.append(
                ("Check", "OK", f"{len(unused_defs)} unused, {len(mismatches)} mismatches")
            )
        except Exception as e:
            statuses.append(("Check", "ERROR", str(e)))
            logger.error("Errore in Check", exc_info=True)
            raise
        pbar.update(1)

        # 6) Format report
        try:
            formatter = OutputFormatter()
            # passa anche i duplicati per la tabella finale
            report = formatter.format(
                inline_map=inline_map,
                style=style,
                unused_defs=unused_defs,
                mismatches=mismatches,
                duplicates=duplicates
            )
            statuses.append(("Report", "OK", "Report generato"))
        except Exception as e:
            statuses.append(("Report", "ERROR", str(e)))
            logger.error("Errore in Report", exc_info=True)
            raise
        pbar.update(1)

    # Log tabellare degli stati
    lines = ["+------------+---------+--------------------------------+"]
    lines.append("| Fase       | Stato   | Dettaglio                       |")
    lines.append("+------------+---------+--------------------------------+")
    for phase, status, detail in statuses:
        lines.append(f"| {phase:<10} | {status:<7} | {detail:<30} |")
    lines.append("+------------+---------+--------------------------------+")
    logger.info("\n" + "\n".join(lines))

    return report
