$ErrorActionPreference='Stop'
$items=Get-Content "$PSScriptRoot/prompts.json" -Raw|ConvertFrom-Json
$review=@(Get-Content "$PSScriptRoot/visual-review.json" -Raw|ConvertFrom-Json)
$html=[Text.StringBuilder]::new()
[void]$html.Append(@'
<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Карточки женщин — предварительный просмотр</title>
<style>body{background:#181820;color:#eee;font:18px/1.5 system-ui;margin:24px}h1{font-size:28px}h2{font-size:22px}section{margin:36px 0}.cards{display:flex;flex-wrap:wrap;gap:20px}figure{margin:0;width:240px}img{width:240px;height:480px;image-rendering:pixelated;display:block}figcaption{padding:8px 0}.missing{height:480px;display:grid;place-items:center;background:#252531;color:#aaa}.issue{color:#ffcb78}a{color:#aaccff}</style>
<h1>Карточки женщин — предварительный просмотр</h1>
<p>Восемь групп. Запланировано по десять новых вариантов, генерация ограничена доступным лимитом Retro Diffusion. Дополнительная монгольская карточка №11 предоставлена пользователем. Оригиналы: 80×160 пикселей, палитра игры, не более 16 цветов. Здесь показаны с увеличением ×3. В игру не добавлены.</p>
'@)
foreach($group in ($items|Group-Object group)){
 [void]$html.Append('<section><h2>'+[Net.WebUtility]::HtmlEncode($group.Group[0].title)+'</h2><div class="cards">')
 foreach($item in $group.Group){
  $rel=$item.group+('/card-{0:00}.png' -f $item.card)
  $issue=@($review|Where-Object {$_.group -eq $item.group -and $_.card -eq $item.card})
  [void]$html.Append('<figure>')
  if(Test-Path (Join-Path $PSScriptRoot $rel)){[void]$html.Append('<a href="'+$rel+'"><img src="'+$rel+'" alt="Вариант '+$item.card+'" loading="lazy"></a>')}else{[void]$html.Append('<div class="missing">Ещё не готово</div>')}
  [void]$html.Append('<figcaption>Вариант '+$item.card)
  if($item.source -eq 'user'){[void]$html.Append(' — предоставлен пользователем')}
  if($issue.Count){[void]$html.Append('<br><span class="issue">'+[Net.WebUtility]::HtmlEncode($issue[0].issue)+'</span>')}
  [void]$html.Append('</figcaption></figure>')
 }
 [void]$html.Append('</div></section>')
}
[void]$html.Append('</html>')
$html.ToString()|Set-Content "$PSScriptRoot/index.html" -Encoding utf8
