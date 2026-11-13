from pathlib import Path
import json,struct,os,subprocess,sys,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from harem_cards import HELPER
O=R/'analysis/qa-card-options';O.mkdir(exist_ok=True)
i=json.loads((R/'analysis/disc-inventory.json').read_text('utf8'));files={f['path']:f for f in i['files']};image=(R/'build/genchou-hishi-ru-experimental.iso').read_bytes();pbase=229614
shutil.copyfile(R/'build/genchou-hishi-ru-experimental.iso',R/'build/qa-generated/trial.iso')
kind=sys.argv[1]
st=bytearray((O/'cold-map.state').read_bytes())
def write(addr,data):
 assert len(data)%2==0
 swap=bytearray(data);swap[::2],swap[1::2]=data[1::2],data[::2];st[pbase+addr:pbase+addr+len(data)]=swap
main=files['SMAIN.PRG;1'];write(0xc000,image[main['lba']*2048:][:main['size']])
if kind=='menu':
 write(0x6afc0,bytes.fromhex('4eb90003238460fe'))
 struct.pack_into('<I',st,1016136,0x6afc0)
else:
 f=files['XXX.PRG;1'];raw=bytearray(image[f['lba']*2048:][:0x5000])
 off=raw.index(bytes.fromhex('4eb900011dd6'),HELPER);raw[off:off+6]=bytes.fromhex('70004e714e71')
 raw[0x361e:0x3622]=bytes.fromhex('60000006');raw[0x362c:0x3630]=bytes.fromhex('60000044')
 raw[0x4050:0x4054]=bytes.fromhex('4878003c')
 raw[0x4ff0:0x4ff8]=bytes.fromhex('4eb90006600060fe');write(0x66000,raw)
 write(0x5ef7c,struct.pack('>I',0x6af00));wife=bytearray(26);wife[20:22]=struct.pack('>H',4);write(0x6af00,wife)
 write(0x7fd58,b'\0\0');struct.pack_into('<I',st,1016136,0x6aff0)
(O/'fixture.state').write_bytes(st)
env=os.environ.copy();env.update(STATE_IN=str(O/'fixture.state'),STATE_OUT=str(O/(kind+'.state')),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
subprocess.run([sys.executable,str(R/'tools/emulate.py'),str(R/'build/qa-cards/game.cue'),'1000' if kind=='card' else '500','[]'],env=env,check=True)
shutil.copyfile(R/'analysis/screen-latest.png',O/(kind+'.png'))
