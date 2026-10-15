# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.

# For the CI build, install NSIS. A download already present, such as from
# the cache, is verified the same way as a fresh one.

$ErrorActionPreference = 'Stop'

if (-not (Test-Path nsis-3.13-setup.exe)) {
    Invoke-WebRequest -Uri "https://download.bleachbit.org/dependency/nsis-3.13-setup.exe" -OutFile nsis-3.13-setup.exe
}
$hash = (Get-FileHash nsis-3.13-setup.exe -Algorithm SHA256).Hash
if ($hash -ne 'db9a1038bbc0e53fef24f423fd609979bd578e942f1be1198db186d1c42652a3') {
    throw "SHA256 mismatch=$hash"
}
$proc = Start-Process -FilePath .\nsis-3.13-setup.exe -ArgumentList '/S' -Wait -PassThru
if ($proc.ExitCode -ne 0) { throw "NSIS setup failed with exit code $($proc.ExitCode)" }
