from pathlib import Path
import json,sys
r=Path('sega-cd');sys.path.insert(0,str(r/'tools'));from scenario_names import valid_offset
p=r/'analysis/scenario-names-final-plan.json';es=json.loads(p.read_text('utf8'))
for e in es:
 if e['offset']=='2CD26':e.update(offset='2CD24',ja='小侍従',ru='Кодзидзю')
for off,ja,ru in [('2CA64','和田義盛','Вада Ёсимори'),('308AA','和田義盛','Вада Ёсимори'),('34E40','和田義盛','Вада Ёсимори'),('2CD7C','小宰相','Кодзайсё'),('2F49A','\x1bKﾅﾗﾊﾟﾃｨｼﾄｩ\x1bH','Нарапатиситу'),('339E2','\x1bKﾅﾗﾊﾟﾃｨｼﾄｩ\x1bH','Нарапатиситу')]:es.append(dict(file='SMAIN.PRG;1',offset=off,ja=ja,ru=ru,kind='person_name'))
inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));f=next(f for f in inv['files'] if f['path']=='SMAIN.PRG;1');b=(r/'disc'/inv['image']).read_bytes()[f['lba']*2048:][:f['size']];extra=[]
for e in es:
 off=int(e['offset'],16);old=e['ja'].encode('shift_jis');assert b[off:off+len(old)+1]==old+b'\0';size=(len(e['ru'])+1)//2*2
 if size>len(old):
  assert len(old)<14 and size<=14 and b[off:off+15]==old+bytes(15-len(old)),e
  e['original_padding_bytes']=14-len(old)
  if not valid_offset(off):extra.append(off)
 e.update(max_columns=14,max_lines=1)
g=r/'translation/gameplay-dialogue.json';allrows=json.loads(g.read_text('utf8'));allrows+=es;g.write_text(json.dumps(allrows,ensure_ascii=False,indent=2)+'\n','utf8');p.write_text(json.dumps(es,ensure_ascii=False,indent=2)+'\n','utf8')
s=r/'tools/scenario_names.py';v=s.read_text('utf8');v=v.replace('    return any(start<=offset', '    return offset in EXTRA_NAME_SLOTS or any(start<=offset');v+='\n# Individually checked later scenario records: 14 name bytes plus NUL.\n# The next byte is a preserved flag, not available string padding.\nEXTRA_NAME_SLOTS = '+repr(tuple(extra))+'\n';s.write_text(v,'utf8');print('Added',len(es),'extra slots',list(map(hex,extra)))
