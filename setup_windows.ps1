$ErrorActionPreference = "Stop"

# Install uv if not on PATH
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing..."
    irm https://astral.sh/uv/install.ps1 | iex

    # Refresh PATH so the current session can find uv
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: uv installed but not found on PATH. Restart your terminal and re-run." -ForegroundColor Red
        exit 1
    }
    Write-Host "uv installed: $(uv --version)"
} else {
    Write-Host "uv already installed: $(uv --version)"
}

# Sync project (creates .venv/ and installs dependencies)
Write-Host "Syncing project dependencies..."
uv sync

Write-Host ""
Write-Host "Setup complete! Run the app with:"
Write-Host "  uv run streamlit run streamlit_app.py"
