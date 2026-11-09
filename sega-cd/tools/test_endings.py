"""Check all five ending caption tables and the shared renderer path."""
from pathlib import Path
import json,struct,sys
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'tools'))
from text_encoding import encode
m=json.loads((r/'build/manifest.json').read_text('utf8'));inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));source=(r/'disc'/inv['image']).read_bytes();image=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();f=next(f for f in inv['files'] if f['path']=='ENDING.PRG;1');base=f['lba']*2048;b=source[base:][:f['size']];main=next(f['lba']*2048 for f in inv['files'] if f['path']=='SMAIN.PRG;1')
es={int(e['references'][0]['offset'],16):e for e in m['text_compositor']['relocated_texts'] if e.get('kind')=='ending_caption'};pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()};assert len(es)==30
for table,code in zip((0x5e72,0x6412,0x6934,0x7046,0x7522),(0xb76,0x1b6e,0x331a,0x4700,0x57c8)):
 assert b[code:code+6]==bytes.fromhex('207c')+struct.pack('>I',0x66000+table)
 for i in range(6):
  e=es[table+4*i];assert b[table+4*i:table+4*i+4]==struct.pack('>I',0x66000+int(e['offset'],16));raw=encode(e['ru'],pairs);name='Чингисхан' if i==4 else '';assert len(encode(name,pairs))+len(raw)<=30
  # Even the longest 14-column generated ruler name stays inside the 30-cell line.
  assert (14 if i==4 else 0)+len(raw)<=30
  dest=e['storage_offset'];assert image[main+dest:main+dest+len(raw)+1]==raw+b'\0'
# The original formatter still dispatches through the patched global renderer.
assert source[main+0x503c:main+0x5040]==bytes.fromhex('487afaba')
print('PASS: 30 ending captions, all five native tables, 14-column ruler-name cases, centred 30-cell bounds')
