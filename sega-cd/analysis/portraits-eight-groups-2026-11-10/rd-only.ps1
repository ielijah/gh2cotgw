$ErrorActionPreference='Stop'
Stop-Process -Id 409640
$dir=Join-Path $PSScriptRoot '06-eastern-european'
Move-Item -LiteralPath (Join-Path $dir 'card-07.png') -Destination (Join-Path $dir 'builtin-originals/card-07-normalized-unused.png')
Move-Item -LiteralPath (Join-Path $dir 'card-07-builtin.json') -Destination (Join-Path $dir 'builtin-originals/card-07-builtin.json')
$items=@(Get-Content "$PSScriptRoot/prompts.json" -Raw|ConvertFrom-Json)
$i=$items|Where-Object {$_.group -eq '06-eastern-european' -and $_.card -eq 7}
$i.seed+=30000
$i.prompt='ZOOMED OUT, FULL BODY SEATED PORTRAIT. Leave ample empty background above the entire hairstyle. The entire head must be visible with a generous margin. ' + ($i.prompt -replace 'COMPOSITION: head-to-knees portrait.*?Emphasize a beautiful youthful adult face, not an elderly or severe-looking face\.', 'Show the complete seated adult figure within the frame, including her entire hair and head. Keep the full figure small enough to fit, with empty background above and below.')
$items|ConvertTo-Json -Depth 10|Set-Content "$PSScriptRoot/prompts.json" -Encoding utf8
Write-Output 'Built-in variant excluded; RD replacement queued'
