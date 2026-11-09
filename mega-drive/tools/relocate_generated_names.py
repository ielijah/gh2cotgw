from pathlib import Path
import json,re
b=Path('rom/original.gen').read_bytes();mapping={}
for line in Path('translation/generated-parts.txt').read_text(encoding='utf-8-sig').splitlines():
 for pair in line.split('|'):
  en,ru=pair.split('=');mapping[en]=ru
p=Path('translation/relocations.json');a=json.loads(p.read_text(encoding='utf-8'));a=[r for r in a if not 0x39544<=int(r['source_offset'],16)<=0x39a06]
items=[]
for m in re.finditer(rb'[A-Za-z][A-Za-z -]*\x00',b[0x39544:0x39a0a]):
 off=0x39544+m.start();en=m.group()[:-1].decode();ru=mapping[en]
 refs=[f'{i:06X}' for i in range(0,0x4ce00,2) if b[i:i+4]==off.to_bytes(4,'big')];assert refs,(en,off)
 items.append(dict(source_offset=f'{off:06X}',source=en,ru=ru,target=f'{0x10c000+len(items)*32:06X}',references=refs))
a.extend(items);p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Relocated name parts:',len(items))
