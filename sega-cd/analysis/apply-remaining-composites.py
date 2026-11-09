from pathlib import Path
import json,struct,sys,re
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'tools'))
from text_encoding import pieces
inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));iso=(r/'disc'/inv['image']).read_bytes();f=next(f for f in inv['files'] if f['path']=='SMAIN.PRG;1');b=iso[f['lba']*2048:][:f['size']]
texts=json.loads((r/'analysis/remaining-composites-plan.json').read_text('utf-8-sig'))
labels={}
p=r/'translation/relocated-text.json';rel=json.loads(p.read_text('utf8'));g=r/'translation/gameplay-dialogue.json';es=json.loads(g.read_text('utf8'));added=[];used={(e['file'],int(e['offset'],16)) for e in rel+es+json.loads((r/'translation/interface.json').read_text('utf8'))}
for offstr,ru in {**labels,**texts}.items():
 off=int(offstr,16);assert ('SMAIN.PRG;1',off) not in used,(offstr,ru)
 ja=b[off:b.index(0,off)].decode('shift_jis');assert all(c in 'KH' for c in re.findall('\x1b(.)',ja)),(offstr,ja)
 size=sum(len(v) if k=='raw' else 2 for k,v in pieces(ru));kind='interface_label' if offstr in labels else 'dialogue_fragment';e=dict(file='SMAIN.PRG;1',offset=offstr,ja=ja,ru=ru,kind=kind,max_columns=10 if kind=='interface_label' else 22,max_lines=1 if kind=='interface_label' else 4)
 assert all((len(x)+1)//2*2<=e['max_columns'] for x in ru.split('\n')),(offstr,ru)
 if size<=len(ja.encode('shift_jis')):es.append(e)
 else:
  key=struct.pack('>I',off+0xc000);refs=[x for x in range(0,len(b)-3,2) if b[x:x+4]==key]
  if not refs or any(not (0x4b000<=x<0x4da00 or x<0x264fe and b[x-2:x]==bytes.fromhex('4879')) for x in refs):print('DEFER',offstr,ru,refs);continue
  e['references']=[dict(file='SMAIN.PRG;1',offset=f'{x:X}',before=key.hex()) for x in refs];rel.append(e)
 added.append(e)
p.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+'\n','utf8');g.write_text(json.dumps(es,ensure_ascii=False,indent=2)+'\n','utf8');(r/'analysis/remaining-composites-wave.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n','utf8');print('Added',len(added))
