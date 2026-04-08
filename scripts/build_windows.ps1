param(
  [string]$Version = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\\.venv\\Scripts\\python.exe")) {
  throw "No se encontro el venv. Crea uno con: python -m venv .venv"
}

if ($Version -ne "") {
  .\\.venv\\Scripts\\python.exe scripts\\ci\\apply_version.py $Version
}

.\\.venv\\Scripts\\python.exe -m pip install -U pip wheel setuptools
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt

.\\.venv\\Scripts\\python.exe -m pytest -q
.\\.venv\\Scripts\\python.exe -m PyInstaller --clean --noconfirm Yagua.spec

Write-Host "PyInstaller OK. Ahora corre Inno Setup manualmente si lo tenes instalado:"
Write-Host "  iscc Yagua.iss"

