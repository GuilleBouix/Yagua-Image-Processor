param(
  [string]$OutputRoot = (Join-Path $env:TEMP ('yagua-build-' + [guid]::NewGuid().ToString('N')))
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (Test-Path -LiteralPath $OutputRoot) { throw 'Usa una carpeta de salida nueva.' }
New-Item -ItemType Directory -Path $OutputRoot | Out-Null
$OutputRoot = (Resolve-Path -LiteralPath $OutputRoot).Path

function Invoke-Checked {
  param([string]$Executable, [string[]]$Arguments)
  & $Executable @Arguments
  if ($LASTEXITCODE -ne 0) { throw "Fallo: $Executable $Arguments" }
}

# Separate environments: developer/testing tools cannot enter the frozen app.
Invoke-Checked python @('-m', 'venv', "$OutputRoot/test-env")
$testPython = "$OutputRoot/test-env/Scripts/python.exe"
Invoke-Checked $testPython @('-m', 'pip', 'install', '-r', 'requirements.txt', '-r', 'requirements-dev.txt')
Invoke-Checked $testPython @('-m', 'pip', 'check')
Invoke-Checked $testPython @('-m', 'ruff', 'check', 'app', 'tests', 'scripts')
Invoke-Checked $testPython @('-m', 'pyright', '--pythonpath', $testPython, 'app')
$env:YAGUA_REQUIRE_UI = '1'
Invoke-Checked $testPython @('scripts/verify.py', '-q')

Invoke-Checked python @('-m', 'venv', "$OutputRoot/build-env")
$buildPython = "$OutputRoot/build-env/Scripts/python.exe"
Invoke-Checked $buildPython @('-m', 'pip', 'install', '-r', 'requirements.txt', '-r', 'requirements-build.txt')
Invoke-Checked $buildPython @('-m', 'pip', 'check')
Invoke-Checked $buildPython @('-m', 'PyInstaller', '--clean', '--noconfirm', '--distpath', "$OutputRoot/dist", '--workpath', "$OutputRoot/work", 'Yagua.spec')
Invoke-Checked python @('scripts/ci/probe_package.py', "$OutputRoot/dist/Yagua/Yagua.exe", "$OutputRoot/preflight", '--preflight')
Write-Host "Build: $OutputRoot/dist/Yagua"
Write-Host 'Faltan las pruebas reales online/offline y el limite total antes de distribuir.'
