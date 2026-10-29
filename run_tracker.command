#!/bin/bash
# Double-click: collect the catalog, compare with the last run, open the Excel report.
cd "$(dirname "$0")"
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv run inventory-tracker "$@"
read -p "Done. Press Enter to close"
