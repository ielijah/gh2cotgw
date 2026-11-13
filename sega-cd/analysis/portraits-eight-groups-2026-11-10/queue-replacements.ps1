$ErrorActionPreference='Stop'
Stop-Process -Id 408284
$root=$PSScriptRoot
$review=@(Get-Content "$root/visual-review.json" -Raw|ConvertFrom-Json)
$items=@(Get-Content "$root/prompts.json" -Raw|ConvertFrom-Json)
foreach($r in $review){
 $dir=Join-Path $root $r.group
 $reject=Join-Path $dir 'rejected-framing'
 New-Item -ItemType Directory -Path $reject -Force|Out-Null
 $stem='card-{0:00}' -f $r.card
 Get-ChildItem -LiteralPath $dir -File -Filter "$stem*" | ForEach-Object {Move-Item -LiteralPath $_.FullName -Destination (Join-Path $reject $_.Name)}
 $i=$items|Where-Object {$_.group -eq $r.group -and $_.card -eq $r.card}
 $i.seed+=20000
 $i.prompt='ZOOMED OUT, FULL BODY SEATED PORTRAIT. Leave ample empty background above the entire hairstyle. The entire head must be visible with a generous margin. ' + ($i.prompt -replace 'COMPOSITION: head-to-knees portrait.*?Emphasize a beautiful youthful adult face, not an elderly or severe-looking face\.', 'Show the complete seated or standing adult figure within the frame, including her entire hair and head. Keep the full figure small enough to fit, with empty background above and below.')
}
$items|ConvertTo-Json -Depth 10|Set-Content "$root/prompts.json" -Encoding utf8
Write-Output 'Five cropped cards preserved separately; replacements queued'
