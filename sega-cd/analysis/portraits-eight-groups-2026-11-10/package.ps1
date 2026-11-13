$ErrorActionPreference='Stop'
& "$PSScriptRoot/preview.ps1"
& "$PSScriptRoot/gallery.ps1"
$rows=@(Get-Content "$PSScriptRoot/validation.json" -Raw|ConvertFrom-Json)
$groups=@($rows|Group-Object group|ForEach-Object {[pscustomobject]@{group=$_.Name;cards=$_.Count}})
[pscustomobject]@{total=$rows.Count;retro_diffusion=($rows.Count-1);user_supplied=1;built_in_included=0;game_modified=$false;stop_reason='Retro Diffusion plan exhausted; remaining requests failed with insufficient_balance';groups=$groups}|ConvertTo-Json -Depth 8|Set-Content "$PSScriptRoot/summary.json" -Encoding utf8
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipPath=Join-Path $PSScriptRoot 'portraits-preview.zip'
$zip=[IO.Compression.ZipFile]::Open($zipPath,[IO.Compression.ZipArchiveMode]::Create)
try {
 foreach($name in @('index.html','validation.json','summary.json','prompts.json')){[void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,(Join-Path $PSScriptRoot $name),$name)}
 foreach($group in $groups){
  $dir=Join-Path $PSScriptRoot $group.group
  foreach($file in (Get-ChildItem -LiteralPath $dir -File|Where-Object {$_.Name -match '^card-\d\d\.png$|^all-(native|preview-3x)\.png$'})){
   [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$file.FullName,($group.group+'/'+$file.Name))
  }
 }
} finally {$zip.Dispose()}
$check=[IO.Compression.ZipFile]::OpenRead($zipPath)
try {
 $count=@($check.Entries|Where-Object {$_.FullName -match '/card-\d\d\.png$'}).Count
 if($count -ne $rows.Count){throw 'Archive card count mismatch'}
 Write-Output ('Archive verified: '+$count+' cards')
} finally {$check.Dispose()}
