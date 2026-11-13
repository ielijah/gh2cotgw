$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$out=$PSScriptRoot
$items=Get-Content (Join-Path $out 'prompts.json') -Raw|ConvertFrom-Json
$pal=[Drawing.Bitmap]::new((Join-Path (Split-Path $out) 'retro-diffusion-trial/palette.png'))
$allowed=[Collections.Generic.HashSet[int]]::new();for($x=0;$x -lt $pal.Width;$x++){[void]$allowed.Add($pal.GetPixel($x,0).ToArgb())};$pal.Dispose()
$report=@()
foreach($group in ($items|Group-Object group)){
 $dir=Join-Path $out $group.Name;$title=$group.Group[0].title
 $last=($group.Group.card|Measure-Object -Maximum).Maximum;$height=[int](18+176*[Math]::Ceiling($last/5))
 $sheet=[Drawing.Bitmap]::new(450,$height);$g=[Drawing.Graphics]::FromImage($sheet);$g.Clear([Drawing.Color]::FromArgb(24,24,32))
 $font=[Drawing.Font]::new('Arial',10,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)
 $g.DrawString($title,$font,[Drawing.Brushes]::White,5,2)
 for($n=1;$n -le $last;$n++){
  $file=Join-Path $dir ('card-{0:00}.png' -f $n);if(-not(Test-Path $file)){continue}
  $b=[Drawing.Bitmap]::new($file);$x=(($n-1)%5)*90+5;$y=18+[Math]::Floor(($n-1)/5)*176
  $g.DrawString([string]$n,$font,[Drawing.Brushes]::White,$x,$y);$g.DrawImageUnscaled($b,$x,($y+13))
  $colors=[Collections.Generic.HashSet[int]]::new();$outside=0
  for($yy=0;$yy -lt $b.Height;$yy++){for($xx=0;$xx -lt $b.Width;$xx++){$v=$b.GetPixel($xx,$yy).ToArgb();[void]$colors.Add($v);if(-not $allowed.Contains($v)){$outside++}}}
  $report+=[pscustomobject]@{group=$group.Name;card=$n;width=$b.Width;height=$b.Height;colors=$colors.Count;outside_palette=$outside}
  if($b.Width -ne 80 -or $b.Height -ne 160 -or $colors.Count -gt 16 -or $outside -gt 0){throw "Invalid image $file"}
  $b.Dispose()
 }
 $g.Dispose();$font.Dispose();$sheet.Save((Join-Path $dir 'all-native.png'),[Drawing.Imaging.ImageFormat]::Png)
 $big=[Drawing.Bitmap]::new(1350,($height*3));$g=[Drawing.Graphics]::FromImage($big);$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::NearestNeighbor;$g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::Half
 $g.DrawImage($sheet,[Drawing.Rectangle]::new(0,0,1350,($height*3)),0,0,450,$height,[Drawing.GraphicsUnit]::Pixel);$g.Dispose();$sheet.Dispose();$big.Save((Join-Path $dir 'all-preview-3x.png'),[Drawing.Imaging.ImageFormat]::Png);$big.Dispose()
}
$report|ConvertTo-Json|Set-Content (Join-Path $out 'validation.json') -Encoding utf8
Write-Output ('Validated '+$report.Count+' cards; generated eight group sheets')
