Add-Type -AssemblyName System.Drawing
$out=$PSScriptRoot
$sheet=[Drawing.Bitmap]::new(450,352)
$g=[Drawing.Graphics]::FromImage($sheet);$g.Clear([Drawing.Color]::FromArgb(24,24,32))
$font=[Drawing.Font]::new('Arial',9,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)
for($n=1;$n -le 10;$n++){
 $file=Join-Path $out ('card-{0:00}.png' -f $n);if(-not(Test-Path $file)){continue}
 $b=[Drawing.Bitmap]::new($file);$x=(($n-1)%5)*90+5;$y=[Math]::Floor(($n-1)/5)*176
 $g.DrawString([string]$n,$font,[Drawing.Brushes]::White,$x,$y)
 $g.DrawImageUnscaled($b,$x,($y+13));$b.Dispose()
}
$g.Dispose();$font.Dispose()
$sheet.Save((Join-Path $out 'all-native.png'),[Drawing.Imaging.ImageFormat]::Png)
$big=[Drawing.Bitmap]::new(1350,1056);$g=[Drawing.Graphics]::FromImage($big)
$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::Half
$g.DrawImage($sheet,[Drawing.Rectangle]::new(0,0,1350,1056),0,0,450,352,[Drawing.GraphicsUnit]::Pixel)
$g.Dispose();$sheet.Dispose();$big.Save((Join-Path $out 'all-preview-3x.png'),[Drawing.Imaging.ImageFormat]::Png);$big.Dispose()
