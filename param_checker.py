# param_checker.py

import logging
import re
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

def check_params(
    function_map: List[Dict],
    call_graph: Dict[str, List[Dict]]
) -> Tuple[List[str], List[Dict]]:
    """
    Analizza la coerenza fra parametri definiti e argomenti passati,
    e rileva le funzioni definite ma mai utilizzate.

    Args:
        function_map: lista di dict con chiavi 'func_name' e 'args' (lista parametri)
        call_graph: dict {nome_funzione: lista chiamate} con info chiamata (file, riga, arg_count, kw_names)

    Returns:
        unused_defs: List[str]  – nomi di funzioni mai richiamate, ordinati
        mismatches:  List[Dict] – entry uniche per ogni richiamo incoerente:
            {
              "function": str,
              "file":     str,
              "line":     int,
              "issue":    str
            }
    """
    unused_defs = []
    raw_mismatches = []

    # Mappa funzione->lista parametri definiti
    defined_params = {
        fn["func_name"]: fn.get("args", []) or []
        for fn in function_map
        if "func_name" in fn
    }

    # Verifica ogni funzione
    for func_name, params in defined_params.items():
        calls = call_graph.get(func_name, [])

        # 1) Funzioni mai richiamate
        if not calls:
            unused_defs.append(func_name)
            continue

        pos_expected = len(params)
        kw_allowed  = set(params)

        # 2) Verifica coerenza per ogni richiamo
        for c in calls:
            file_ = c.get("caller_file", "")
            line  = c.get("caller_lineno", 0)

            # a) Posizionali
            arg_count = c.get("arg_count", 0)
            if arg_count != pos_expected:
                raw_mismatches.append({
                    "function": func_name,
                    "file":     file_,
                    "line":     line,
                    "issue":    f"{arg_count} arg posiz., attesi {pos_expected}"
                })

            # b) Keyword sconosciute
            bad_kw = [kw for kw in c.get("kw_names", []) if kw not in kw_allowed]
            if bad_kw:
                raw_mismatches.append({
                    "function": func_name,
                    "file":     file_,
                    "line":     line,
                    "issue":    "keyword sconosciute: " + ", ".join(bad_kw)
                })

    # Rimuovi duplicati e ordina mismatches
    seen = set()
    mismatches: List[Dict] = []
    for m in raw_mismatches:
        key = (m["function"], m["file"], m["line"], m["issue"])
        if key not in seen:
            seen.add(key)
            mismatches.append(m)
    mismatches.sort(key=lambda x: (x["file"], x["line"], x["function"]))

    unused_defs = sorted(set(unused_defs))

    logger.debug(f"param_checker: {len(unused_defs)} unused, {len(mismatches)} mismatches")
    return unused_defs, mismatches


def check_param_discrepancies(calls_file_path: str, func_param_map: dict) -> list:
    """
    Controlla discrepanze nel numero di parametri passati alle funzioni rispetto a quelli definiti.

    Args:
        calls_file_path (str): percorso file txt con chiamate funzione.
            Ogni riga attesa contenere chiamata tipo: funzione(param1,param2,...)
        func_param_map (dict): dizionario {nome_funzione: numero_parametri_attesi}

    Returns:
        list: lista di dizionari con i dettagli delle discrepanze trovate.
              Ogni dizionario ha chiavi: 'line_num', 'func_name', 'expected', 'passed', 'line_text'
    """
    discrepancies = []
    pattern = re.compile(r"(\w+)\s*\((.*)\)")

    with open(calls_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if not match:
                # Riga non conforme, ignorata
                continue

            func_name, param_str = match.groups()
            if param_str.strip() == '':
                passed_params_count = 0
            else:
                # Split semplice su virgola
                params = [p.strip() for p in param_str.split(',')]
                passed_params_count = len(params)

            expected_params_count = func_param_map.get(func_name)
            if expected_params_count is None:
                # Funzione sconosciuta, ignora
                continue

            if passed_params_count != expected_params_count:
                discrepancies.append({
                    'line_num': line_num,
                    'func_name': func_name,
                    'expected': expected_params_count,
                    'passed': passed_params_count,
                    'line_text': line
                })

    return discrepancies


def print_discrepancies(discrepancies: list):
    if not discrepancies:
        print("Nessuna discrepanza nel numero di parametri trovata.")
        return

    print(f"Trovate {len(discrepancies)} discrepanze di parametri:")
    for d in discrepancies:
        print(f"Linea {d['line_num']}: funzione '{d['func_name']}' - attesi {d['expected']} parametri, "
              f"passati {d['passed']}. Riga: {d['line_text']}")

def build_func_param_map(function_map: List[Dict] = None) -> Dict[str, int]:
    """
    Costruisce una mappa {nome_funzione: numero_parametri_attesi} a partire
    da una lista di definizioni funzione.

    Args:
        function_map (List[Dict], opzionale): lista di dict con chiavi:
            - 'func_name': str
            - 'args': List[str] (lista dei nomi parametri)

    Returns:
        Dict[str, int]: mappa nome funzione -> numero parametri attesi
    """
    if function_map is None:
        return {}

    param_map = {}
    for fn in function_map:
        name = fn.get("func_name")
        args = fn.get("args", [])
        if name:
            param_map[name] = len(args) if args else 0

    return param_map

# Alias per compatibilità con orchestrator.py
check_parameter_congruence = check_params