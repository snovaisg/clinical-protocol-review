#!/usr/bin/env bash
set -euo pipefail

# Install uv if not on PATH
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source env so current shell can find uv
    [ -f "$HOME/.local/bin/env" ] && . "$HOME/.local/bin/env"
    [ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
    if ! command -v uv &> /dev/null; then
        echo "ERROR: uv installed but not found on PATH. Add ~/.local/bin to PATH and re-run."
        exit 1
    fi
    echo "uv installed: $(uv --version)"
else
    echo "uv already installed: $(uv --version)"
fi

# Sync project (creates .venv/ and installs dependencies)
echo "Syncing project dependencies..."
uv sync

echo ""
echo "Setup complete! Run the app with:"
echo "  uv run streamlit run streamlit_app.py"
