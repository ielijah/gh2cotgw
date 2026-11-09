from pathlib import Path
import json,sys
r=Path('sega-cd');sys.path.insert(0,str(r/'tools'));from text_encoding import pieces
v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));iso=(r/'disc'/v['image']).read_bytes();f=next(x for x in v['files'] if x['path']=='INIT.PRG;1');b=iso[f['lba']*2048:][:f['size']]
plan={'152FA':'Амир Хосров','1535E':'Ибн аль-Асир','1543A':'Альфонс VIII','15476':'Алексей III','15822':'Вильгельм II','158D6':'Худуха-беки','15A66':'Гори-Шимрен','15B06':'Сакьяпандит','15B6A':'Салах ад-Дин','15BE2':'Шиги-Хутуг','15CE6':'Ибн Джубайр','15E12':'Сорхан-Шира','160E2':'Тимур-Мелик','162FE':'Тогорил-хан','16326':'Тохтоа-беки','16416':'Наратихапате','1642A':'Нарапатиситу','164DE':'Генрих VI','165BA':'Баллахала II','1660A':'Бильгэ-беки','1666E':'Фогельвейде','16722':'Всеволод III','1674A':'Хубилай-хан','167D6':'Притхвирадж','167EA':'Вэнь Тяньсян','1697A':'Менгу-Тимур','169A2':'Михаил VIII','16A92':'Мухаммад Насир','16ABA':'аль-Мунтасир','16B82':'Ярослав III','16C36':'Людовик VIII','16CC2':'Вада Ёсимори','16CD6':'Ваньянь Фусин'}
p=r/'translation/gameplay-dialogue.json';es=json.loads(p.read_text('utf8'));added=[]
for key,ru in plan.items():
 off=int(key,16);ja=b[off:b.index(0,off)].decode('shift_jis');cap=len(ja.encode('shift_jis'));size=sum(len(v) if k=='raw' else 2 for k,v in pieces(ru));assert size<=14
 e=dict(file='INIT.PRG;1',offset=key,ja=ja,ru=ru,kind='person_name',max_columns=14,max_lines=1)
 if size>cap:
  assert b[off:off+15]==ja.encode('shift_jis')+bytes(15-cap),(key,b[off:off+16].hex())
  e['original_padding_bytes']=14-cap;e['name_capacity']=14
 assert not any(x['file']==e['file'] and x['offset']==key for x in es)
 es.append(e);added.append(e)
p.write_text(json.dumps(es,ensure_ascii=False,indent=2)+'\n','utf8');(r/'analysis/catalog-record-final-names.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n','utf8');print('Added',len(added))
for name in ('build.py','verify.py'):
 p=r/'tools'/name;s=p.read_text('utf8').replace('<0x16cc2','<0x16ce6')
 if name=='build.py':s=s.replace('assert padding==10-len(old)>0',"limit=entry.get('name_capacity',10);assert limit in (10,14)\n            assert padding==limit-len(old)>0\n            assert original[position:position+limit+1]==old+bytes(limit+1-len(old))")
 else:s=s.replace('assert padding==10-len(raw)>0',"limit=entry.get('name_capacity',10);assert limit in (10,14)\n                assert padding==limit-len(raw)>0\n                assert program[start:start+limit+1]==raw+bytes(limit+1-len(raw))")
 p.write_text(s,'utf8')
