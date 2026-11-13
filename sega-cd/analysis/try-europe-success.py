from pathlib import Path
import json,struct,os,subprocess
r=Path('.');i=json.loads((r/'analysis/disc-inventory.json').read_text());image=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();f=next(f for f in i['files'] if f['path']=='XXX.PRG;1');st=bytearray((r/'analysis/europe-harem-cold.state').read_bytes());pbase=229614
raw=bytearray(image[f['lba']*2048:f['lba']*2048+0x5000]);helper=0x4e10;off=raw.index(bytes.fromhex('4eb900011dd6'),helper);raw[off:off+6]=bytes.fromhex('70004e714e71');raw[0x361e:0x3622]=bytes.fromhex('60000006');raw[0x362c:0x3630]=bytes.fromhex('60000044');raw[0x4ff0:0x4ff8]=bytes.fromhex('4eb90006600060fe')
def write(addr,data):
 b=bytearray(data);assert len(b)%2==0;b[::2],b[1::2]=data[1::2],data[::2];st[pbase+addr:pbase+addr+len(b)]=b
write(0x66000,raw);write(0x5ef7c,struct.pack('>I',0x6af00));wife=bytearray(26);wife[16]=4<<2;wife[20:22]=struct.pack('>H',4);write(0x6af00,wife)
struct.pack_into('<I',st,1016136,0x6aff0)
(r/'analysis/europe-success-fixture.state').write_bytes(st)
env=os.environ.copy();env['CORE_OPTIONS']='{"genesis_plus_gx_cart_size":"none"}';env['STATE_IN']='analysis/europe-success-fixture.state';env['STATE_OUT']='analysis/europe-success-result.state'
subprocess.run(['../.runtime/python/python.exe','tools/emulate.py','build/qa-generated/trial.cue','500','[]'],env=env,check=True)
