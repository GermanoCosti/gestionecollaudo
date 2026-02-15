$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

python -m pip install -r .\requirements-build.txt

pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "GestioneCollaudo" `
  .\gestione_collaudo\gui.py

Write-Host "OK: EXE creato in $here\\dist\\GestioneCollaudo.exe"

