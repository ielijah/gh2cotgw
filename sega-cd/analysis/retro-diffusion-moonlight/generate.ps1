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
  $n=$batch*2+$j+1
  $prefix=Join-Path $out ('card-{0:00}' -f $n)
  if(Test-Path "$prefix.png"){Write-Output "Card $n already saved";continue}
  $payload=Get-Content -LiteralPath $template -Raw|ConvertFrom-Json
    $payload.seed=198601
  $payload.reference_images=@()
  $payload.prompt='One native 80x160 pixel portrait card for an early 1990s Sega CD historical game, limited strictly to the supplied palette. A clearly mature adult woman aged 32 with long dark hair loosely braided and a small ivory flower, standing sideways beside a stone wall under soft moonlight from an arched window. Calm self-possessed expression, looking back over her bare shoulder, one hand resting gently against the wall. Relaxed upright natural stance. Opaque lavender drapery securely covers breasts, hips and pelvis, with bare upper back and arms. Tasteful non-explicit romantic atmosphere, no sexual activity, no coercion, no restraints. Frame from COMPLETE TOP OF HAIR to below knees. The entire head and all hair ornaments must be visible, with 12 pixels of colored background above hair and visible margins on both sides. Keep head inside canvas, do not crop it. Coarse authentic 1990s Japanese game pixel art, restrained mature face detail, simple hard shadow clusters, sparse checkerboard dithering, blue and purple moonlight using supplied colors. Colored stone wall and night background extend to every edge, NO white stripes, NO white border, NO blank margins, NO text, NO collage. Exact 80x160, no smoothing or antialiasing.'
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
for($n=1;$n -le 1;$n++){
 $file=Join-Path $out ('card-{0:00}.png' -f $n);$b=[Drawing.Bitmap]::new($file)
 $colors=[Collections.Generic.HashSet[int]]::new();$outside=0
 for($y=0;$y -lt $b.Height;$y++){for($x=0;$x -lt $b.Width;$x++){$c=$b.GetPixel($x,$y).ToArgb();[void]$colors.Add($c);if(-not $allowed.Contains($c)){$outside++}}}
 $report+=[pscustomobject]@{card=$n;width=$b.Width;height=$b.Height;colors=$colors.Count;pixels_outside_palette=$outside};$b.Dispose()
}
$report|ConvertTo-Json|Set-Content (Join-Path $out 'validation.json') -Encoding utf8
$report|ConvertTo-Json
