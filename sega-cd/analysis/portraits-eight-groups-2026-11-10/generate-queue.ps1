$ErrorActionPreference='Stop'
$out=$PSScriptRoot
$key=[Environment]::GetEnvironmentVariable('RD_API_KEY','User');if(-not $key){$key=$env:RD_API_KEY};if(-not $key){throw 'RD_API_KEY missing'}
$api='https://api.retrodiffusion.ai/v2/inferences';$headers=@{'X-RD-Token'=$key}
$template=Get-Content (Join-Path (Split-Path $out) 'retro-diffusion-european-ten/card-10-request.json') -Raw|ConvertFrom-Json
$items=@(Get-Content (Join-Path $out 'prompts.json') -Raw|ConvertFrom-Json|Where-Object {-not(Test-Path (Join-Path (Join-Path $out $_.group) ('card-{0:00}.png' -f $_.card)))}|Sort-Object @{Expression={if(Test-Path (Join-Path (Join-Path $out $_.group) ('card-{0:00}-admission.json' -f $_.card))){0}else{1}}},card,group)
$cursor=0;$jobs=@();$blocked=$false
while($cursor -lt $items.Count -or @($jobs|Where-Object {-not $_.done}).Count){
 while(-not $blocked -and $cursor -lt $items.Count -and @($jobs|Where-Object {-not $_.done}).Count -lt 2){
  $item=$items[$cursor];$prefix=Join-Path (Join-Path $out $item.group) ('card-{0:00}' -f $item.card)
  $payload=$template|ConvertTo-Json -Depth 12|ConvertFrom-Json;$payload.prompt=$item.prompt;$payload.seed=$item.seed;$payload.reference_images=@();$body=$payload|ConvertTo-Json -Depth 12
  try{
   if(Test-Path "$prefix-admission.json"){$admission=Get-Content "$prefix-admission.json" -Raw|ConvertFrom-Json}else{
    $body|Set-Content "$prefix-request.json" -Encoding utf8
    $estimate=$body|ConvertFrom-Json;$estimate|Add-Member check_cost $true
    $cost=Invoke-RestMethod -Method Post -Uri $api -Headers $headers -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes(($estimate|ConvertTo-Json -Depth 12))) -TimeoutSec 45
    $cost|ConvertTo-Json -Depth 12|Set-Content "$prefix-cost.json" -Encoding utf8
    if($cost.would_use -ne 'plan'){throw ('Plan generation unavailable: '+$cost.would_use)}
    if($cost.balance_cost -gt 0.18){throw 'Unexpected cost above $0.18'}
    $idfile="$prefix-idempotency.txt";if(Test-Path $idfile){$id=(Get-Content $idfile -Raw).Trim()}else{$id=[guid]::NewGuid().ToString();$id|Set-Content $idfile}
    $admission=Invoke-RestMethod -Method Post -Uri $api -Headers @{'X-RD-Token'=$key;'Idempotency-Key'=$id} -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 90
    $admission|ConvertTo-Json -Depth 12|Set-Content "$prefix-admission.json" -Encoding utf8
   }
   $jobs+=@{prefix=$prefix;task=$admission.task_id;done=$false;label=($item.group+'/'+$item.card)};$cursor++
   Write-Output ('ACCEPTED '+$item.group+'/'+$item.card)
  }catch{
   $blocked=$true;$cursor=$items.Count
   [pscustomobject]@{card=$prefix;message=$_.Exception.Message;details=$_.ErrorDetails.Message}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $out 'blocked.json') -Encoding utf8
   Write-Output ('SUBMISSION STOPPED: '+$_.Exception.Message)
  }
 }
 foreach($job in @($jobs|Where-Object {-not $_.done})){
  try{$r=Invoke-RestMethod -Uri "$api/tasks/$($job.task)" -Headers $headers -TimeoutSec 45}catch{continue}
  if($r.status -eq 'succeeded'){
   [IO.File]::WriteAllBytes(($job.prefix+'.png'),[Convert]::FromBase64String($r.result.base64_images[0]));$r.result.base64_images=@();$r|ConvertTo-Json -Depth 15|Set-Content ($job.prefix+'-result.json') -Encoding utf8
   $job.done=$true;Write-Output ('SAVED '+$job.label+' billing='+$r.result.billing.source+' plan_remaining='+$r.billing.plan_usage_left_pct+'%')
  }elseif($r.status -in @('failed','cancelled')){
   $r|ConvertTo-Json -Depth 15|Set-Content ($job.prefix+'-result.json') -Encoding utf8;$job.done=$true;Write-Output ('FAILED '+$job.label)
  }
 }
 if(@($jobs|Where-Object {-not $_.done}).Count){Start-Sleep -Seconds 3}
}
if($blocked){exit 2};Write-Output 'QUEUE COMPLETE'
