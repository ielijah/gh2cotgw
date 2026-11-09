$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimePath = Join-Path (Split-Path -Parent $projectRoot) '.runtime'
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
Invoke-WebRequest 'https://www.python.org/ftp/python/3.13.2/python-3.13.2-embed-amd64.zip' -OutFile (Join-Path $runtimePath 'python.zip')
Expand-Archive -LiteralPath (Join-Path $runtimePath 'python.zip') -DestinationPath (Join-Path $runtimePath 'python') -Force
$capstoneMetadata = Invoke-RestMethod 'https://pypi.org/pypi/capstone/5.0.6/json'
$capstoneWheel = $capstoneMetadata.urls | Where-Object { $_.filename -like '*win_amd64.whl' } | Select-Object -First 1
Invoke-WebRequest $capstoneWheel.url -OutFile (Join-Path $runtimePath 'capstone.zip')
Expand-Archive -LiteralPath (Join-Path $runtimePath 'capstone.zip') -DestinationPath (Join-Path $runtimePath 'python') -Force
Invoke-WebRequest 'https://buildbot.libretro.com/nightly/windows/x86_64/latest/genesis_plus_gx_libretro.dll.zip' -OutFile (Join-Path $runtimePath 'genesis.zip')
Expand-Archive -LiteralPath (Join-Path $runtimePath 'genesis.zip') -DestinationPath (Join-Path $runtimePath 'emulator') -Force
