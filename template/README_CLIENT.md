# How to run your scraper

You get a ready Excel file with the data. You only need these steps if you want to **re-run** the scraper yourself (for example, every week).

## 1. Install once

**Windows**
1. Install Python from https://www.python.org/downloads/ (tick **"Add python.exe to PATH"** during setup).
2. Open the **PowerShell** app and run:
   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
3. Close and reopen PowerShell.

**macOS**
1. Open the **Terminal** app and run:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Close and reopen Terminal.

## 2. Run

1. Unzip the folder you received, e.g. to your Desktop.
2. In PowerShell / Terminal go to that folder:
   ```
   cd Desktop/scraper
   ```
3. Start the scraper:
   ```
   uv run python template/scraper.py
   ```
   The first run takes a minute to install everything. You will see progress messages like `Page 3: 20 rows`.

## 3. Get the result

The file appears in the `out` folder: `out/result.xlsx` (Excel) and `out/result.csv`.
The **Summary** sheet shows how many rows were collected.

## Problems?

Send me the file from the `logs` folder and a screenshot of the window. Small fixes after delivery are free for 14 days.

---

**Кратко по-русски:** установите Python и uv (шаг 1), откройте папку в PowerShell/Терминале и выполните `uv run python template/scraper.py`. Результат — в папке `out`. Если что-то не так, пришлите файл из папки `logs`.
