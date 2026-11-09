"""QA-only image: open the real name editor at the initial menu.

Never modifies playable packages. The caller is deliberately replaced by a
loop after the editor returns; this image is not suitable for a playthrough.
"""
from pathlib import Path
import json,re,hashlib
r=Path(__file__).resolve().parents[1];v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));original=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();img=bytearray(original);f=next(x for x in v['files'] if x['path']=='INIT.PRG;1');off=f['lba']*2048+0x1dc6;patch=bytes.fromhex('4eb90001d1f64eb90001da5c60f8');assert img[off:off+2]==bytes.fromhex('4879');before=img[off:off+len(patch)].hex();img[off:off+len(patch)]=patch
q=r/'build/qa-keyboard';q.mkdir(exist_ok=True);(q/'keyboard.iso').write_bytes(img);cue=(r/'build/playable-dub/game.cue').read_text('ascii')
for i,n in enumerate(re.findall(r'FILE "([^"]+)"',cue)):cue=cue.replace('FILE "'+n+'"','FILE "'+('keyboard.iso' if i==0 else '../playable-dub/'+n)+'"')
(q/'keyboard.cue').write_text(cue,'ascii');(q/'qa-only.json').write_text(json.dumps(dict(production_sha256=hashlib.sha256(original).hexdigest(),file='INIT.PRG;1',offset='1DC6',before=before,after=patch.hex(),warning='QA only; never distribute this image'),indent=2),'utf8')
