$ErrorActionPreference='Stop'
$out=$PSScriptRoot
$template=Join-Path (Split-Path $out) 'retro-diffusion-trial/request.json'
$key=[Environment]::GetEnvironmentVariable('RD_API_KEY','User')
if(-not $key){$key=$env:RD_API_KEY}
if(-not $key){throw 'RD_API_KEY missing'}
$headers=@{'X-RD-Token'=$key}
$api='https://api.retrodiffusion.ai/v2/inferences'
$subjects=@(
 'A mature adult woman aged 32 with an angular face, high cheekbones, long black hair tied loosely with a pale flower. Seated sideways looking back over her bare shoulder, bare upper back, one hand gathering lavender cloth at her side. Opaque drapery covers chest and pelvis, one bare leg visible to mid-thigh. Slate blue geometric background.',
 'A mature adult woman aged 35 with a round face, copper-red shoulder-length curls, freckles and confident smile. Seated front three-quarter, one arm raised to adjust her hair, other hand on knee. Bare shoulders, arms and midriff, opaque pale pink cloth covering breasts and a separate draped cloth securely covering pelvis, visible knees and lower thighs. Muted olive geometric background.',
 'A mature adult woman aged 30 with warm brown skin, oval face, dark almond-shaped eyes, long dark side braid and small gold earrings. Sitting upright in side profile, head gently turned toward viewer, hands resting together on one bent knee. Bare shoulders and arms, ivory drapery securely covers breasts and pelvis, exposed side waist and one leg. Muted plum geometric background.',
 'A mature adult woman aged 34 with a square jaw, short wavy black bob, defined eyebrows and slight smile. Seated diagonally with one knee raised, one hand resting on the far shoulder and other holding the wrap at her hip. Bare shoulders, arms and upper back, opaque lilac drapery securely covers breasts and pelvis, bare thigh and knee visible. Dusty rose geometric background.'
)
$common='One new original portrait card for an early 1990s Sega CD historical strategy game. Match the reference cards coarse pixel scale, mature face drawing, restrained simple shading, checkerboard dithering and 16-color palette. Tasteful non-explicit classical draped adult portrait, no nudity, no sexual activity. Single narrow head-to-knees composition, thin white pixel border. Distinct face and pose, not a copy of the references. EXACT native 80x160 pixel art, solid pixel clusters, no smooth gradients, no antialiasing, no text, no collage. '
for($batch=0;$batch -lt 1;$batch++){
 $jobs=@()
 for($j=0;$j -lt 1;$j++){
  $n=4
  $prefix=Join-Path $out ('card-{0:00}' -f $n)
  if(Test-Path "$prefix.png"){Write-Output "Card $n already saved";continue}
  $payload=Get-Content -LiteralPath $template -Raw|ConvertFrom-Json
    $payload.seed=198560+$n; $payload.reference_images=@()
  $payload.prompt='COMPOSITION IS THE HIGHEST PRIORITY. Create a new 80x160 pixel art card with a SMALLER seated adult figure completely framed from the FULL TOP OF HAIR through knees. The top 16 rows of the image are ONLY a solid colored background, with NO head or hair in them. Place the top of her hairstyle at y=18, face centered around y=35, shoulders near y=60. All hair and hair ornaments are completely visible, with generous colored background above and on both sides. Do not imitate the close-up cropping of reference images. NO cropped head, NO hair touching an edge. Full-bleed colored geometric background all the way to every edge; NO frame, NO white border, NO vertical white stripe, NO blank white margin anywhere. The reference images are ONLY for coarse 1990s Sega CD pixel-art technique, palette and drapery, NOT for framing. Use original 16-color palette and exact native 80x160 canvas, clean pixel clusters and simple restrained dithering. Tasteful non-explicit classical draped adult portrait. Preserve the entire head even if legs must be cropped. No text. '+$subjects[$n-1]
  $payload.prompt='A small FULL BODY seated adult woman, COMPLETE FIGURE visible from TOP OF HAIR to FEET, surrounded on ALL FOUR sides by a generous colored background margin. Entire silhouette fits inside central 64x130 region of an 80x160 canvas. A clearly adult woman aged 32 with short wavy black bob, square jaw and slight smile, seated diagonally with one knee raised, lavender opaque classical drapery securely covers chest and pelvis, bare shoulders and back. Graceful neutral pose. Full top of head and complete hair are essential. NO CLOSEUP. NO CROPPING. NO ZOOMED PORTRAIT. Early 1990s Sega CD native low resolution pixel art, coarse restrained facial detail, 16-color original palette, simple pixel clusters and checkerboard dithering. Muted slate blue geometric background fills all edges. NO white border, NO frame, NO white stripes. Tasteful non-explicit illustration. Exact 80x160.'
  $body=$payload|ConvertTo-Json -Depth 10
  if(Test-Path "$prefix-admission.json"){
   $admission=Get-Content "$prefix-admission.json" -Raw|ConvertFrom-Json
  }else{
   $body|Set-Content "$prefix-request.json" -Encoding utf8
   $estimate=$body|ConvertFrom-Json
   $estimate|Add-Member check_cost $true
   $cost=Invoke-RestMethod -Method Post -Uri $api -Headers $headers -ContentType 'application/json' -Body ($estimate|ConvertTo-Json -Depth 10)
   if($cost.balance_cost -gt 0.18){throw 'Unexpected cost above $0.18'}
   $idfile="$prefix-idempotency.txt"
   if(Test-Path $idfile){$id=(Get-Content $idfile -Raw).Trim()}else{$id=[guid]::NewGuid().ToString();$id|Set-Content $idfile}
   $admission=Invoke-RestMethod -Method Post -Uri $api -Headers @{'X-RD-Token'=$key;'Idempotency-Key'=$id} -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 90
   $admission|ConvertTo-Json -Depth 10|Set-Content "$prefix-admission.json" -Encoding utf8
  }
  $jobs+=@{n=$n;prefix=$prefix;task=$admission.task_id;done=$false}
  Write-Output "Card $n accepted"
 }
 while(@($jobs|Where-Object {-not $_.done}).Count){
  foreach($job in $jobs){
   if($job.done){continue}
   $r=Invoke-RestMethod -Uri "$api/tasks/$($job.task)" -Headers $headers -TimeoutSec 60
   if($r.status -eq 'succeeded'){
    [IO.File]::WriteAllBytes(($job.prefix+'.png'),[Convert]::FromBase64String($r.result.base64_images[0]))
    $r.result.base64_images=@();$r|ConvertTo-Json -Depth 15|Set-Content ($job.prefix+'-result.json') -Encoding utf8
    $job.done=$true;Write-Output "Card $($job.n) saved; billing=$($r.result.billing.source)"
   }elseif($r.status -in @('failed','cancelled')){
    $r|ConvertTo-Json -Depth 15|Set-Content ($job.prefix+'-result.json') -Encoding utf8
    throw "Card $($job.n) failed: $($r.error|ConvertTo-Json -Compress)"
   }
  }
  if(@($jobs|Where-Object {-not $_.done}).Count){Start-Sleep -Seconds 4}
 }
}
Add-Type -AssemblyName System.Drawing
$pal=[Drawing.Bitmap]::new((Join-Path (Split-Path $out) 'retro-diffusion-trial/palette.png'))
$allowed=[Collections.Generic.HashSet[int]]::new()
for($x=0;$x -lt $pal.Width;$x++){[void]$allowed.Add($pal.GetPixel($x,0).ToArgb())}
$pal.Dispose();$report=@()
for($n=4;$n -le 4;$n++){
 $file=Join-Path $out ('card-{0:00}.png' -f $n);$b=[Drawing.Bitmap]::new($file)
 $colors=[Collections.Generic.HashSet[int]]::new();$outside=0
 for($y=0;$y -lt $b.Height;$y++){for($x=0;$x -lt $b.Width;$x++){$c=$b.GetPixel($x,$y).ToArgb();[void]$colors.Add($c);if(-not $allowed.Contains($c)){$outside++}}}
 $report+=[pscustomobject]@{card=$n;width=$b.Width;height=$b.Height;colors=$colors.Count;pixels_outside_palette=$outside};$b.Dispose()
}
$report|ConvertTo-Json|Set-Content (Join-Path $out 'validation.json') -Encoding utf8
$report|ConvertTo-Json
