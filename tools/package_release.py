"""Package the user-approved 0.5.22 binary as release 1.0.0."""
from pathlib import Path
import json,hashlib,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1]
VERSION='1.0.0'
STEM='Genghis-Khan-II-Rus-'+VERSION
out=ROOT/'release'/VERSION;out.mkdir(parents=True,exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads((ROOT/'build/manifest.json').read_text(encoding='utf8'))
previous=json.loads((ROOT/'build/archive/manifest-0.5.22.json').read_text(encoding='utf8'))
assert manifest['version']==VERSION
for ext,key in [('gen','rom_sha256'),('ips','ips_sha256')]:
 raw=(ROOT/f'build/genghis2-ru-experimental.{ext}').read_bytes()
 assert sha(raw)==manifest[key]==previous[key],('Release differs from approved binary',ext)
 (out/f'{STEM}.{ext}').write_bytes(raw)
manifest.update(release_date='2026-11-08',channel='release',promoted_from='0.5.22',playthrough_confirmation={'source':'user report','campaigns':['за монголов','за Чингисхана'],'date':'2026-11-08'},files={'rom':STEM+'.gen','patch':STEM+'.ips'})
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
readme=f'''Genghis Khan II: Clan of the Gray Wolf — русский перевод
Релиз {VERSION}, 8 ноября 2026 года
Платформа: Sega Mega Drive / Genesis. Основа: американская версия (USA).

ЗАПУСК
В полном архиве откройте {STEM}.gen в эмуляторе Mega Drive / Genesis.
В архиве с патчем готовый ROM отсутствует: примените {STEM}.ips
любым средством применения IPS к чистому американскому ROM в формате BIN/GEN,
без дополнительного заголовка и без ранее установленных патчей.
Патч расширяет ROM; итоговый размер — {manifest['rom_size']} байт.

SHA-256 исходного ROM:
{manifest['source_sha256']}
SHA-256 русского ROM:
{manifest['rom_sha256']}

СОХРАНЕНИЯ
Сохраните резервную копию своих файлов сохранений перед заменой сборки.
Релизный ROM побайтно совпадает с 0.5.22. Формат внутриигровых сохранений
не изменён. При смене имени ROM эмулятор может ожидать соответствующее имя
файла SRAM (.srm/.sav); используйте его функцию импорта или прежнее имя ROM.
Совместимость быстрых состояний эмулятора зависит от самого эмулятора.

ЧТО ВОШЛО
Русские диалоги, меню, боевые команды, имена и названия, экранная клавиатура,
вступительные титры, название игры и финальная надпись КОНЕЦ.
Исправления шрифтов, палитр, склонений, составных реплик, пробелов и рамок.
1793 применённых текстовых замен — это количество записей, а не процент перевода.

ПРОВЕРКИ
Пользователь сообщил о завершении основных кампаний за монголов и за Чингисхана
и одобрил выпуск. Автоматически проверены сборка, контрольные суммы, применение
IPS, текстовые построители, кириллица, клавиатура, меню и отрисовка ряда событий.
Остальные сценарии и все редкие события сплошным прохождением не подтверждены.
При сообщении об ошибке укажите версию, сценарий, действие и приложите снимок.

БЛАГОДАРНОСТИ
Участникам обсуждения Chief-Net за наработки по терминологии, именам и названиям:
http://chief-net.ru/forum/topic.php?forum=4&topic=35
Автору предоставленной пользователем версии перевода — за основу кириллических
шрифтов. Имя автора этой версии в материалах проекта не установлено.
Пользователю — за тестирование, прохождение кампаний и редакторские правки.
Оригинальная игра: KOEI; исходные обозначения разработчика сохранены.

ПАКЕТЫ
Полный ZIP содержит ROM, IPS и документацию.
ZIP с суффиксом -patch содержит IPS и документацию, без ROM.
SHA256SUMS.txt позволяет проверить целостность файлов внутри каждого архива.
'''
(out/'README-RU.txt').write_text(readme,encoding='utf-8-sig')
(out/'RELEASE-NOTES.txt').write_text('1.0.0 — первый релиз.\nЗакреплена сборка 0.5.22 без изменения ROM и IPS.\nОснование выпуска: подтверждённое пользователем прохождение двух основных кампаний.\n',encoding='utf-8-sig')
common=[STEM+'.ips','README-RU.txt','RELEASE-NOTES.txt','manifest.json']
for suffix,names in [('',[STEM+'.gen']+common),('-patch',common)]:
 entries={name:(out/name).read_bytes() for name in names}
 entries['SHA256SUMS.txt']=(''.join(sha(data)+'  '+name+'\n' for name,data in entries.items())).encode()
 path=ROOT/'release'/f'{STEM}{suffix}.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in entries.items():
   info=zipfile.ZipInfo(name,date_time=(2026,11,8,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  assert set(z.namelist())==set(entries)
  for name,data in entries.items():assert z.read(name)==data
 print(path.name, path.stat().st_size, sha(path.read_bytes()))
(out/'SHA256SUMS.txt').write_text(''.join(sha((out/n).read_bytes())+'  '+n+'\n' for n in [STEM+'.gen']+common),encoding='utf8')
(ROOT/'release/SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted((ROOT/'release').glob(STEM+'*.zip'))),encoding='utf8')
print('PASS: approved ROM/IPS unchanged; both release archives verified')
