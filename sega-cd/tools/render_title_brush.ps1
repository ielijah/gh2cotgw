# Convert the imagegen brush master to the game's indexed, tile-aligned palette.
Add-Type -AssemblyName System.Drawing
$project = Split-Path $PSScriptRoot -Parent
$bitmap = [System.Drawing.Bitmap]::new((Join-Path $project 'assets/title-brush-source.png'))
$pixels = [System.IO.File]::ReadAllBytes((Join-Path $project 'assets/title-russian-pixels.bin'))
# Keep the approved subtitle and its olive strip, rows 70..87.
[Array]::Clear($pixels, 0, 192 * 70)
$ink = [bool[]]::new(192 * 70)
for ($y=2; $y -lt 62; $y++) {
    for ($x=8; $x -lt 184; $x++) {
        $hits=0
        for ($sy=0; $sy -lt 3; $sy++) {
            for ($sx=0; $sx -lt 3; $sx++) {
                $px=[int][Math]::Floor(($x-8+($sx+0.5)/3)*$bitmap.Width/176)
                $py=[int][Math]::Floor(($y-2+($sy+0.5)/3)*$bitmap.Height/60)
                $c=$bitmap.GetPixel($px,$py)
                if ($c.R -gt 160 -and $c.G -gt 160 -and $c.B -gt 160) { $hits++ }
            }
        }
        $ink[$y*192+$x]=$hits -ge 4
    }
}
$bitmap.Dispose()
for ($y=1; $y -lt 69; $y++) {
    for ($x=1; $x -lt 191; $x++) {
        if ($ink[$y*192+$x]) {
            for ($dy=-1; $dy -le 1; $dy++) {
                for ($dx=-1; $dx -le 1; $dx++) { $pixels[($y+$dy)*192+$x+$dx]=3 }
            }
        }
    }
}
for ($i=0; $i -lt $ink.Length; $i++) { if ($ink[$i]) { $pixels[$i]=4 } }
[System.IO.File]::WriteAllBytes((Join-Path $project 'assets/title-russian-pixels.bin'),$pixels)
