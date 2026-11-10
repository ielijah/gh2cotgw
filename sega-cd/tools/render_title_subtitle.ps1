# Quantize the imagegen subtitle master into the native yellow/olive palette.
Add-Type -AssemblyName System.Drawing
$project=Split-Path $PSScriptRoot -Parent
$bitmap=[System.Drawing.Bitmap]::new((Join-Path $project 'assets/title-subtitle-source.png'))
$left=$bitmap.Width; $right=0; $top=$bitmap.Height; $bottom=0
for ($y=0; $y -lt $bitmap.Height; $y++) {
    for ($x=0; $x -lt $bitmap.Width; $x++) {
        $c=$bitmap.GetPixel($x,$y)
        if ($c.R -gt 160 -and $c.G -gt 160) {
            $left=[Math]::Min($left,$x);$right=[Math]::Max($right,$x)
            $top=[Math]::Min($top,$y);$bottom=[Math]::Max($bottom,$y)
        }
    }
}
$pixels=[System.IO.File]::ReadAllBytes((Join-Path $project 'assets/title-russian-pixels.bin'))
for ($i=192*70; $i -lt $pixels.Length; $i++) { $pixels[$i]=2 }
for ($y=0; $y -lt 14; $y++) {
    for ($x=0; $x -lt 168; $x++) {
        $hits=0
        for ($sy=0; $sy -lt 3; $sy++) {
            for ($sx=0; $sx -lt 3; $sx++) {
                $px=$left+[int][Math]::Floor(($x+($sx+0.5)/3)*($right-$left+1)/168)
                $py=$top+[int][Math]::Floor(($y+($sy+0.5)/3)*($bottom-$top+1)/14)
                $c=$bitmap.GetPixel($px,$py)
                if ($c.R -gt 160 -and $c.G -gt 160) { $hits++ }
            }
        }
        if ($hits -ge 4) { $pixels[($y+72)*192+$x+12]=1 }
    }
}
$bitmap.Dispose()
[System.IO.File]::WriteAllBytes((Join-Path $project 'assets/title-russian-pixels.bin'),$pixels)
