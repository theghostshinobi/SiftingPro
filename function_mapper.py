import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)


class FunctionMapper:
    """
    Normalizza e raggruppa le informazioni sulle definizioni di funzione:
      - func_name, class_name, lineno, file, language, created, last_modified
      - signature, called_functions, imports_used, docstring
      - raccoglie duplicati in una lista separata

    Restituisce:
      - function_map: lista di dict con i campi delle funzioni
      - function_index: mapping func_name → indice in function_map
      - duplicates: lista di dict con chiavi 'func_name', 'file', 'lineno'
    """

    VALID_MODES = {"full", "light", "doc_only"}

    def map_functions(
            self,
            parsed_nodes: List[Dict[str, Any]],
            mode: str = "full"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[Dict[str, Any]]]:
        """
        Costruisce la mappa delle funzioni a partire dai nodi ASTParser o PHPParser.

        Args:
            parsed_nodes: lista di dict prodotti da ASTParser o PHPParser.
            mode: modalità di estrazione:
                - "full": include signature, called_functions, imports_used, docstring
                - "light": include solo signature e called_functions
                - "doc_only": include solo docstring

        Returns:
            function_map: lista di dict con campi:
              - func_name: str
              - class_name: Optional[str]
              - lineno: int
              - file: str
              - language: str ("py"|"php")
              - created: datetime di creazione file
              - last_modified: datetime di ultima modifica
              - signature: List[str]            (se mode in ["full","light"])
              - called_functions: List[str]     (se mode in ["full","light"])
              - imports_used: List[str]         (se mode == "full")
              - docstring: Optional[str]        (se mode in ["full","doc_only"])
            function_index: dict mapping func_name → indice in function_map
            duplicates: lista di dict con:
              - func_name: str
              - file: str
              - lineno: int
        """
        if mode not in self.VALID_MODES:
            raise ValueError(f"Mode non valido: {mode!r}. Deve essere uno di {self.VALID_MODES}")

        # Raggruppa tutti gli import per file
        imports_by_file: Dict[str, List[str]] = defaultdict(list)
        for node in parsed_nodes:
            if node.get("type") in ("Import", "ImportFrom"):
                imports_by_file[node["file"]].append(node["name"])

        function_map: List[Dict[str, Any]] = []
        seen_names = set()
        duplicates: List[Dict[str, Any]] = []

        for node in parsed_nodes:
            if node.get("type") not in ("FunctionDef", "AsyncFunctionDef"):
                continue

            name = node["name"]
            file = node.get("file")
            lineno = node.get("lineno")

            if name in seen_names:
                # anziché loggare, raccogliamo il duplicato
                duplicates.append({
                    "func_name": name,
                    "file": file,
                    "lineno": lineno
                })
            seen_names.add(name)

            entry: Dict[str, Any] = {
                "func_name": name,
                "class_name": node.get("class_name"),
                "lineno": lineno,
                "file": file,
                "language": node.get("language", "py"),
                "created": node.get("created", datetime.min),
                "last_modified": node.get("last_modified", datetime.min),
            }

            # Campi per mode "full" e "light"
            if mode in ("full", "light"):
                entry["signature"] = list(node.get("signature", []))
                entry["called_functions"] = list(node.get("calls", []))

            # Solo per mode "full": import utilizzati
            if mode == "full":
                entry["imports_used"] = list(imports_by_file.get(file, []))

            # Solo per mode "full" e "doc_only": docstring
            if mode in ("full", "doc_only"):
                entry["docstring"] = node.get("docstring")

            function_map.append(entry)

        # Indice per lookup rapido
        function_index = {fn["func_name"]: idx for idx, fn in enumerate(function_map)}

        logger.debug(f"FunctionMapper: mappate {len(function_map)} funzioni, {len(duplicates)} duplicati")
        return function_map, function_index, duplicates
