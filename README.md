# SiftingPro
CLI tool for static analysis of Python &amp; PHP codebases. Scans functions, builds call graphs, checks parameter consistency, detects duplicate definitions, and shows file/line metadata with creation &amp; modification dates. Outputs colorized, wrapped ASCII tables for fast, actionable insights.


Here’s a **quickstart guide** for using the tool from your terminal:

---

## 1) Launch from Terminal

```bash
python cli_runner.py <project_directory> [-f FORMAT]...
```

* **`<project_directory>`**
  The root folder you want to analyze (must contain `.py` and `.php` files).

* **`-f` / `--format` option**
  Specify the output format. You can repeat it to generate multiple formats in one go. Defaults to `-f table` if omitted.

---

## 2) Available Formats

| Code          | Description                                                            |
| ------------- | ---------------------------------------------------------------------- |
| `table`       | Aligned ASCII table with all definitions, calls, and a “Status” column |
| `plain`/`txt` | Simple text report (one line per call)                                 |
| `csv`         | Standard CSV file (with header and one row per call)                   |
| `json`        | Full JSON object including definitions, calls, and mismatches          |
| `tree`        | ASCII tree diagram representing the call graph                         |

**Example combination:**

```bash
python cli_runner.py ./my_project -f table -f csv -f json
```

---

## 3) What You Get

1. **`table`** (stdout)
   Console output like:

   ```
   +----+------------+---------------------------+-------+----------------------+----------------------+--------+----------------------+------+-----------+
   | #  | Function   | Def. file (path)          | D.line| Params (declared)    | Call file            | C.line | Call args            | Lang | Status    |
   +----+------------+---------------------------+-------+----------------------+----------------------+--------+----------------------+------+-----------+
   | 1  | process_data | src/utils/processor.py  | 58    | (data, verbose=False)| tests/test_main.py   | 23     | (["a","b"],True)     | py   | OK        |
   | 2  | calculateTotal | src/cart.php          | 120   | (items)              | src/views/checkout.php| 45     | (order.items)        | php  | [31mMISMATCH[0m 🚨 |
   …
   +----+------------+---------------------------+-------+----------------------+----------------------+--------+----------------------+------+-----------+
   ```

2. **`plain`/`txt`** (`report.txt` in your project dir)
   Lines like:

   ```
   processor.py:58 → process_data(data, verbose=False)
   processor.py:23 → process_data(["a","b"], True)
   cart.php:45    → calculateTotal(order.items)
   …
   ―――――――――――――――――――――――――――――――――
   ⚠ Parameter mismatches:
     calculateTotal @ checkout.php:45 → 1 positional, expected 2
   🔥 Unused functions (3):
     foo, bar, baz
   ―――――――――――――――――――――――――――――――――
   ```

3. **`csv`** (`report.csv`)

   ```csv
   #,Function,Def. file,D.line,Params (declared),Call file,C.line,Call args,Lang,Status
   1,process_data,src/utils/processor.py,58,"data, verbose=False",tests/test_main.py,23,"[""a"",""b""];True",py,OK
   2,calculateTotal,src/cart.php,120,items,src/views/checkout.php,45,order.items,php,"MISMATCH 🚨"
   …
   ```

4. **`json`** (`report.json`)

   ```json
   {
     "report": [
       {
         "function_name": "process_data",
         "definition": { "file": "src/utils/processor.py", "lineno": 58, … },
         "total_calls": 2,
         "calls": [ { "caller_file":"tests/test_main.py", … } ]
       },
       {
         "function_name": "calculateTotal",
         "definition": { "file": "src/cart.php", "lineno":120, … },
         "total_calls": 1,
         "calls": [ { "caller_file":"src/views/checkout.php", … } ]
       }
     ],
     "unused_definitions": [ … ],
     "param_mismatches": [ … ]
   }
   ```

5. **`tree`** (stdout)
   An ASCII-tree view of the call graph:

   ```
   process_data
   ├─ helper
   └─ save_results

   calculateTotal
   └─ validate_items

   …
   ```

---

**In summary**:

* **Run**

  ```bash
  python cli_runner.py <path> -f <format>
  ```
* **Use** one or more `-f` flags (`table`, `txt`, `csv`, `json`, `tree`)
* **Receive**:

  * Aligned ASCII table in console (`table`)
  * `report.txt` file (`plain`/`txt`)
  * `report.csv` file (`csv`)
  * `report.json` file (`json`)
  * ASCII tree in console (`tree`)

