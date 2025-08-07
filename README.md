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
  * 


  OUTPUT:
```bash
(venv) (base) ➜ toolkit python cli_runner.py /path/to/project -f table
Processing: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 6/6 [00:34<00:00,  5.80s/step]
2025-08-07 12:13:07,104 INFO:
+------------+---------+--------------------------------+
| Phase      | Status  | Details                        |
+------------+---------+--------------------------------+
| Crawl      | OK      | 93 files found                 |
| Parse      | OK      | 37149 nodes extracted          |
| Map        | OK      | 1561 functions mapped          |
| CallGraph  | OK      | 10 definitions, 17501 unmatched|
| Check      | OK      | 1285 unused, 39 mismatches     |
| Report     | OK      | Report generated               |
+------------+---------+--------------------------------+


| #  | Type       | Function         | Def. File                             | File Dates                       | Def. Line | Signature | Call File | Call Line | Call Args | Lang | Status    |
|    |            |                  |                                        |                                   |           |           |           |           |           |      |           |
| Row index | Definition or Call | Function name  | Path to definition file               | Modified & Created               | Def. line | Declared signature | Call file | Call line | Arguments passed | Language (py/php) | OK or MISMATCH |
+____________+____________________+__________________+________________________________________+___________________________________+___________+____________________+___________+___________+__________________+________________+____________+
| 1  | definition | default_config   | /path/to/project/utils/db/Example.py  | Mod: 29-10-2024; Cr: 25-07-2025  | 8         | (self)    |           |           |                  | py   | OK         |
|    |            |                  |                                        |                                   |           |           |           |           |           |      |            |
|    |            |                  | /path/to/project/utils/db/ExampleAid.py|                                   |           |           |           |           |           |      |            |
| 2  | definition | config_filename  | /path/to/project/config/Settings.py    | Mod: 29-10-2024; Cr: 25-07-2025  | 18        | (self)    |           |           |                  | py   | OK         |
|    |            |                  |                                        |                                   |           |           |           |           |           |      |            |
|    |            |                  | /path/to/project/config/SettingsExtra.py|                                  |           |           |           |           |           |      |            |
+------------+------------+------------------+----------------------------------------+-----------------------------------+-----------+--------------------+-----------+-----------+------------------+------+-----------+
```

## 📦 Requirements

This project relies on the following Python packages, pinned in `requirements.txt`:

```text
chardet==5.2.0
exceptiongroup==1.3.0
iniconfig==2.1.0
packaging==25.0
pluggy==1.6.0
Pygments==2.19.2
pytest==8.4.1
tabulate==0.9.0
tomli==2.2.1
tqdm==4.67.1
typing_extensions==4.14.1
```

---

### Installation

1. **Create (or activate) a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Save the list above** into a file named `requirements.txt`.

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**

   ```bash
   pip list
   ```

You’re now ready to run the tool!


