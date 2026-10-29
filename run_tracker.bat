@echo off
rem Double-click: collect the catalog, compare with the last run, open the Excel report.
cd /d "%~dp0"
where uv >nul 2>nul || powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
uv run inventory-tracker %*
pause
