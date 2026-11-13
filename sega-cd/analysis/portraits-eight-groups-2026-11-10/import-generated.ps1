param([Parameter(Mandatory)][string]$Source,[Parameter(Mandatory)][string]$Group,[Parameter(Mandatory)][int]$Card,[string]$Provider='built-in image_gen',[string]$OriginalsFolder='builtin-originals')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$dir=Join-Path $PSScriptRoot $Group
$stem='card-{0:00}' -f $Card
$raw=Join-Path $dir $OriginalsFolder
New-Item -ItemType Directory -Path $raw -Force|Out-Null
Copy-Item -LiteralPath $Source -Destination (Join-Path $raw "$stem.png")
$target=Join-Path $dir "$stem.png"
if(Test-Path $target){
 $reject=Join-Path $dir 'rejected-framing'
 New-Item -ItemType Directory -Path $reject -Force|Out-Null
 Get-ChildItem -LiteralPath $dir -Filter "$stem*" -File|ForEach-Object {Move-Item -LiteralPath $_.FullName -Destination (Join-Path $reject $_.Name)}
}
$src=[Drawing.Bitmap]::new($Source)
$palette=[Drawing.Bitmap]::new((Join-Path (Split-Path $PSScriptRoot) 'retro-diffusion-trial/palette.png'))
$colors=@();for($x=0;$x -lt $palette.Width;$x++){$colors+=@($palette.GetPixel($x,0))}
$dst=[Drawing.Bitmap]::new(80,160)
for($y=0;$y -lt 160;$y++){
 for($x=0;$x -lt 80;$x++){
  $c=$src.GetPixel([Math]::Min($src.Width-1,[int][Math]::Floor(($x+0.5)*$src.Width/80)),[Math]::Min($src.Height-1,[int][Math]::Floor(($y+0.5)*$src.Height/160)))
  $best=$colors[0];$distance=[double]::MaxValue
  foreach($p in $colors){$d=2*[Math]::Pow($c.R-$p.R,2)+3*[Math]::Pow($c.G-$p.G,2)+[Math]::Pow($c.B-$p.B,2);if($d -lt $distance){$distance=$d;$best=$p}}
  $dst.SetPixel($x,$y,$best)
 }
}
$dst.Save($target,[Drawing.Imaging.ImageFormat]::Png)
[pscustomobject]@{generator=$Provider;original=(Join-Path $OriginalsFolder "$stem.png");width=80;height=160;normalization='Nearest-neighbor sampling and nearest original palette color; no dithering added'}|ConvertTo-Json|Set-Content (Join-Path $dir "$stem-import.json") -Encoding utf8
$dst.Dispose();$src.Dispose();$palette.Dispose()
Write-Output $target
