from pathlib import Path
import json
p=Path('translation/fields.json');d=json.loads(p.read_text(encoding='utf-8'))
for line in Path('translation/people-additions.txt').read_text(encoding='utf-8-sig').splitlines():
 en,ru=line.split('|');assert len(ru)<=12,(en,ru);d['people'][en]=ru
roman={'$':'I','\\':'II','^':'III','}~':'IV','@':'V','{|':'VIII','=':'X'}
bases={'Barrula':'Баллахала','Vsevolod':'Всеволод','Henri':'Генрих','Leszek':'Лешек','Andrew':'Андраш','Otto':'Оттон','Frederick':'Фридрих','John':'Иоанн','Philip':'Филипп','Alfonso':'Альфонс','Theodorus':'Феодор','Sancho':'Санчо','Louis':'Людовик','Yaroslav':'Ярослав','Michael':'Михаил','Boleslav':'Болеслав','Rudolf':'Рудольф','Charles':'Карл','Henry':'Генрих','Otakar':'Отакар','Pedro':'Педро','Isaacius':'Исаак','Kazimierz':'Казимир','Bela':'Бела','William':'Вильгельм','Richard':'Ричард','Birrama':'Биррама','Alexius':'Алексей'}
b=Path('rom/original.gen').read_bytes()
for en,ru in bases.items():
 for symbol,number in roman.items():
  old=en+' '+symbol
  if b.find(old.encode()+b'\0',0x3db1e,0x457c4)>=0:
   new=ru+' '+number
   if len(new)>12:new=ru  # Keep a complete name, never cut through a syllable.
   d['people'][old]=new
countries={'The Yuan Dynasty':'Династия Юань','The Ugudei Khanate':'Улус Угэдэя','The Golden Horde':'Золотая Орда','The Jagatai Khanate':'Чагатайский улус','Dai-Viet':'Дайвьет','Mameluke Sultanate':'Мамлюкский султанат','The Hafsids':'Хафсиды','The Delhi Sultanate':'Делийский султанат','The Il-Khan Empire':'Улус Хулагу'}
d['countries'].update(countries);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('People',len(d['people']))
p=Path('translation/menu-font.json');d=json.loads(p.read_text(encoding='utf-8'));d['е']=['0110','1001','1001','1111','1000','1000','0111'];p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
