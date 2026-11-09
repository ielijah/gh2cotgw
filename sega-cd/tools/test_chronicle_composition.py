"""Validate expanded chronicle tables, dynamic placeholders and birth-message composition."""
from pathlib import Path
import json,sys,re
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'tools'))
from text_encoding import encode,encode_stream
m=json.loads((r/'build/manifest.json').read_text('utf8'));pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()};reverse={v:k for k,v in pairs.items()}
def decode(data):
 out='';i=0
 while i<len(data):
  if data[i]==27:i+=3;continue
  if data[i]>=0xf0:out+=reverse[data[i:i+2]];i+=2
  else:out+=chr(data[i]);i+=1
 return out
es={int(e['offset'],16):e for e in m['applied']+m['text_compositor']['relocated_texts'] if e['file']=='SMAIN.PRG;1'}
inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));image=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();base=next(f['lba']*2048 for f in inv['files'] if f['path']=='SMAIN.PRG;1')
for bank in m['text_compositor']['chronicle_tables']['banks']:
 for i,ru in enumerate(bank['ru']):
  raw=encode(ru,pairs)+b'\0';a=base+bank['offset']+i*bank['stride'];assert len(raw)<=bank['stride'];assert image[a:a+len(raw)]==raw
for season in ('Весна','Лето','Осень','Зима'):
 ruler=encode('Александр Длин',pairs);nation=encode('Империя монголов',pairs)
 a=encode_stream(es[0x4c260]['ru'],pairs)%(1184,encode(season,pairs),nation,ruler)
 b=encode_stream(es[0x4c2c2]['ru'],pairs)%(1184,encode(season,pairs),ruler,encode('Хираидзуми',pairs))
 for data in (a,b):
  lines=decode(data).split('\n');assert len(lines)<=6 and max(map(len,lines))<=30,lines
for female in (False,True):
 for name in ('Бортэ','Тьеу Тхань','Александр Длин'):
  normal=b''.join(encode(es[o]['ru'],pairs) for o in (0x277fc,0x277f8 if female else 0x277f4,0x277ee))+encode(name,pairs)+encode(es[0x277e0]['ru'],pairs)
  dead=b''.join(encode(es[o]['ru'],pairs) for o in (0x277dc if female else 0x277d8,0x277ce))+encode(name,pairs)+encode(es[0x277c0]['ru'],pairs)
  for data in (normal,dead):
   lines=decode(data).split('\n');assert len(lines)<=4 and max(map(len,lines))<=22,lines
  assert ('Родилась дочь.' if female else 'Родился сын.') in decode(normal)
  assert 'Мать: '+name in decode(normal)
  assert 'Скончалась.' in decode(dead)
print('PASS: expanded city/season/shogunate banks, all chronicle seasons with maximum names, boy/girl birth and maternal-death message composition')
