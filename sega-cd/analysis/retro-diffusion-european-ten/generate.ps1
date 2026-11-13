$ErrorActionPreference='Stop'
$out=$PSScriptRoot
$template=Join-Path (Split-Path $out) 'retro-diffusion-trial/request.json'
$key=[Environment]::GetEnvironmentVariable('RD_API_KEY','User')
if(-not $key){$key=$env:RD_API_KEY}
if(-not $key){throw 'RD_API_KEY missing'}
$headers=@{'X-RD-Token'=$key}
$api='https://api.retrodiffusion.ai/v2/inferences'
$subjects=@(
 'A mature adult European woman aged 32, fair skin, long golden-blonde braid, oval face, pale flower. Seated three-quarter, hands resting together on her lap, ivory and lilac drapery, muted blue backdrop.',
 'A mature adult European woman aged 34, copper-red wavy bob, freckles, round face, warm smile. Seated sideways, one hand resting lightly on opposite shoulder, rose drapery, olive backdrop.',
 'A mature adult European woman aged 31, pale skin, long chestnut curls, narrow face, arched eyebrows. Upright seated profile looking back over shoulder, lavender drapery, muted rose backdrop.',
 'A mature adult European woman aged 36, olive skin, black loosely braided hair, strong cheekbones, pearl earrings. Facing three-quarter, one hand by her cheek, other on lap, ivory drapery, slate blue backdrop.',
 'A mature adult European woman aged 30, fair skin, auburn hair arranged in a braided crown, broad face, calm smile. Seated upright with hands clasped at one shoulder holding shawl, lilac drapery, plum backdrop.',
 'A mature adult European woman aged 33, warm fair skin, dark-blonde shoulder-length curls, square jaw and expressive brows. Seated diagonally, one arm bent with hand touching hair, other resting on knee, pink drapery, teal backdrop.',
 'A mature adult European woman aged 35, pale skin, long straight dark brown hair with one pale ribbon, heart-shaped face. Seated side view with head turned gently toward viewer, hands on folded drapery in lap, ivory cloth, muted green backdrop.',
 'A mature adult European woman aged 32, light olive skin, short black curly hair, rounded cheeks, small gold earrings. Seated front three-quarter, hand resting on collarbone, lavender drapery, dusty pink backdrop.',
 'A mature adult European woman aged 37, fair skin, long reddish-brown braid, angular face, aquiline nose and composed expression. Upright side pose looking over shoulder, one hand gathering shawl at waist, pink and ivory drapery, blue backdrop.',
 'A mature adult European woman aged 31, fair skin, honey-blonde hair in a loose bun, oval face and soft smile. Seated three-quarter, chin resting lightly on knuckles, other hand on lap, lavender drapery, muted olive backdrop.'
)
$common='One new original portrait card for an early 1990s Sega CD historical strategy game. Match the reference cards coarse pixel scale, mature face drawing, restrained simple shading, checkerboard dithering and 16-color palette. Tasteful non-explicit classical draped adult portrait, no nudity, no sexual activity. Single narrow head-to-knees composition, thin white pixel border. Distinct face and pose, not a copy of the references. EXACT native 80x160 pixel art, solid pixel clusters, no smooth gradients, no antialiasing, no text, no collage. '
for($batch=0;$batch -lt 5;$batch++){
 $jobs=@()
 for($j=0;$j -lt 2;$j++){
  $n=$batch*2+$j+1
  $prefix=Join-Path $out ('card-{0:00}' -f $n)
  if(Test-Path "$prefix.png"){Write-Output "Card $n already saved";continue}
  $payload=Get-Content -LiteralPath $template -Raw|ConvertFrom-Json
    $payload.seed=198700+$n; $payload.reference_images=@()
  $payload.prompt='Create ONE NEW early 1990s Sega CD pixel-art card of a clearly mature adult European woman. References are ONLY for pixel technique, palette and cloth rendering, NOT for framing or identity. CRITICAL COMPOSITION: whole head and ENTIRE hairstyle must fit comfortably inside image with 12 pixels of colored background ABOVE the highest hair pixel and 5 pixels on both sides. Show a FULL seated figure from the entire head down to FEET, with ALL of her silhouette inside the central 64x130 pixel area; background surrounds her on ALL FOUR sides. NEVER crop head. Opaque classical drapery covers breasts, pelvis and upper thighs, bare shoulders and arms. Tasteful non-explicit character portrait in a relaxed neutral pose. Natural adult proportions, distinct mature face. Flat colored geometric backdrop fills every edge, NO white stripes, NO border, NO frame, NO blank margins. Exact native 80x160 pixels, original limited palette, restrained coarse face details, hard pixel clusters, sparse checkerboard dithering. No smooth shading, antialiasing, text, numbers or collage. '+$subjects[$n-1]
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
for($n=1;$n -le 10;$n++){
 $file=Join-Path $out ('card-{0:00}.png' -f $n);$b=[Drawing.Bitmap]::new($file)
 $colors=[Collections.Generic.HashSet[int]]::new();$outside=0
 for($y=0;$y -lt $b.Height;$y++){for($x=0;$x -lt $b.Width;$x++){$c=$b.GetPixel($x,$y).ToArgb();[void]$colors.Add($c);if(-not $allowed.Contains($c)){$outside++}}}
 $report+=[pscustomobject]@{card=$n;width=$b.Width;height=$b.Height;colors=$colors.Count;pixels_outside_palette=$outside};$b.Dispose()
}
$report|ConvertTo-Json|Set-Content (Join-Path $out 'validation.json') -Encoding utf8
$report|ConvertTo-Json
