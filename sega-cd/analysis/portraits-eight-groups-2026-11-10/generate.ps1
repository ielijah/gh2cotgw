$ErrorActionPreference='Stop'
$out=$PSScriptRoot
$key=[Environment]::GetEnvironmentVariable('RD_API_KEY','User');if(-not $key){$key=$env:RD_API_KEY};if(-not $key){throw 'RD_API_KEY missing'}
$api='https://api.retrodiffusion.ai/v2/inferences';$headers=@{'X-RD-Token'=$key}
$template=Get-Content (Join-Path (Split-Path $out) 'retro-diffusion-european-ten/card-10-request.json') -Raw|ConvertFrom-Json
$items=@(Get-Content (Join-Path $out 'prompts.json') -Raw|ConvertFrom-Json)
for($offset=0;$offset -lt $items.Count;$offset+=2){
 $jobs=@()
 foreach($item in $items[$offset..([Math]::Min($offset+1,$items.Count-1))]){
  $prefix=Join-Path (Join-Path $out $item.group) ('card-{0:00}' -f $item.card)
  if(Test-Path "$prefix.png"){continue}
  $payload=$template|ConvertTo-Json -Depth 12|ConvertFrom-Json
  $payload.prompt=$item.prompt;$payload.seed=$item.seed;$payload.reference_images=@()
  $body=$payload|ConvertTo-Json -Depth 12
  if(Test-Path "$prefix-admission.json"){$admission=Get-Content "$prefix-admission.json" -Raw|ConvertFrom-Json}else{
   $body|Set-Content "$prefix-request.json" -Encoding utf8
   $estimate=$body|ConvertFrom-Json;$estimate|Add-Member check_cost $true
   $cost=Invoke-RestMethod -Method Post -Uri $api -Headers $headers -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes(($estimate|ConvertTo-Json -Depth 12))) -TimeoutSec 60
   $cost|ConvertTo-Json -Depth 12|Set-Content "$prefix-cost.json" -Encoding utf8
   if($cost.balance_cost -gt 0.18){throw 'Unexpected unit cost above prior approved workflow ceiling $0.18'}
   $idfile="$prefix-idempotency.txt";if(Test-Path $idfile){$id=(Get-Content $idfile -Raw).Trim()}else{$id=[guid]::NewGuid().ToString();$id|Set-Content $idfile}
   $admission=Invoke-RestMethod -Method Post -Uri $api -Headers @{'X-RD-Token'=$key;'Idempotency-Key'=$id} -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 90
   $admission|ConvertTo-Json -Depth 12|Set-Content "$prefix-admission.json" -Encoding utf8
  }
  $jobs+=@{prefix=$prefix;task=$admission.task_id;done=$false;label=($item.group+'/'+$item.card)}
  Write-Output ('ACCEPTED '+$item.group+'/'+$item.card)
 }
 while(@($jobs|Where-Object {-not $_.done}).Count){
  foreach($job in $jobs){
   if($job.done){continue}
   try{$r=Invoke-RestMethod -Uri "$api/tasks/$($job.task)" -Headers $headers -TimeoutSec 45}catch{Write-Output ('Polling retry '+$job.label);Start-Sleep -Seconds 4;continue}
   if($r.status -eq 'succeeded'){
    [IO.File]::WriteAllBytes(($job.prefix+'.png'),[Convert]::FromBase64String($r.result.base64_images[0]))
    $r.result.base64_images=@();$r|ConvertTo-Json -Depth 15|Set-Content ($job.prefix+'-result.json') -Encoding utf8
    $job.done=$true;Write-Output ('SAVED '+$job.label+' billing='+$r.result.billing.source)
   }elseif($r.status -in @('failed','cancelled')){
    $r|ConvertTo-Json -Depth 15|Set-Content ($job.prefix+'-result.json') -Encoding utf8
    throw ('Generation failed: '+$job.label+'; status='+$r.status)
   }
  }
  if(@($jobs|Where-Object {-not $_.done}).Count){Start-Sleep -Seconds 4}
 }
}
Write-Output 'COMPLETE: 80 cards'
