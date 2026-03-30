# JalNirikshan easy start script
# Usage: Open powershell, cd to project root, then:
#    .\start.ps1

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# Activate venv
$venv = Join-Path $projectRoot '.venv\Scripts\Activate.ps1'
if (-Not (Test-Path $venv)) {
    Write-Host "Virtual environment not found. Creating .venv..."
    python -m venv .venv
}

Write-Host "Activating virtual environment..."
. .venv\Scripts\Activate.ps1

Write-Host "Installing dependencies (if needed)..."
pip install -r requirements.txt

Start-Process powershell -ArgumentList ('-NoExit', '-Command', 'cd "{0}"; .venv\Scripts\Activate.ps1; uvicorn backend:app --host 0.0.0.0 --port 8000 --reload' -f $projectRoot) -WorkingDirectory $projectRoot
Start-Process powershell -ArgumentList ('-NoExit', '-Command', 'cd "{0}"; .venv\Scripts\Activate.ps1; streamlit run dashboard.py' -f $projectRoot) -WorkingDirectory $projectRoot

Write-Host "Started backend and dashboard in separate windows."
Write-Host "- Backend: http://127.0.0.1:8000/health"
Write-Host "- Streamlit: http://localhost:8501"