$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
New-Item -ItemType Directory -Path 'tools' -Force | Out-Null
$archivePath = Join-Path $PSScriptRoot 'tools\scrcpy-v4.1.zip'
Invoke-WebRequest 'https://github.com/Genymobile/scrcpy/releases/download/v4.1/scrcpy-win64-v4.1.zip' -OutFile $archivePath
$expectedHash = '5b12172b3264b2889f4583ee64752ce832e29bc8b1089dca81093459697165db'
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLower() -ne $expectedHash) { throw 'SHA256 do scrcpy incorreto' }
Expand-Archive -LiteralPath $archivePath -DestinationPath 'tools' -Force
python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar PyInstaller' }
python -m PyInstaller --noconfirm --windowed --onedir --name Conecta --add-data 'tools\scrcpy-win64-v4.1;tools\scrcpy-win64-v4.1' --add-data 'LEIA-ME.txt;.' app.py
if ($LASTEXITCODE -ne 0) { throw 'Falha na compilação' }
Copy-Item README.md,THIRD-PARTY.md -Destination 'dist\Conecta'
