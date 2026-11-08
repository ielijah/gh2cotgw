"""Render exact production orders wrapper and roster with controlled fixtures."""
from pathlib import Path
import sys,struct,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
inputs=[[1900,1910,3],[3000,3010,3],[4100,4110,8],[5100,5110,8],[5500,5510,8],[6400,6410,8],[7200,7210,8]]+[[t,t+10,8] for t in range(8100,10501,600)]
for case in ['orders-spacing','governor-spacing','family-markers','appoint-governor']:
 r=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes());base=len(r);data=base+0x1000;r.extend(bytes(0x2000))
 def put(off,value):r[off:off+len(value)]=value
 def pea(addr):return bytes.fromhex('4879')+struct.pack('>I',addr)
 c=bytearray.fromhex('4eb900009c00')
 if case=='orders-spacing':
  r[0xdbb6:0xdbb8]=bytes.fromhex('60fe')
  put(data,encode('Чингисхан   ')+b'\0');c+=pea(0x49c08)+pea(data)+bytes.fromhex('4eb90012a700508f')
 elif case=='governor-spacing':
  put(data,encode('10: Корея?')+b'\0')
  c+=pea(0x3d224)+bytes.fromhex('4eb900006c22588f')+pea(data)+bytes.fromhex('4eb900006c3a588f')+pea(0xff2ce8)+bytes.fromhex('4eb900007df0588f')
 elif case=='appoint-governor':
  put(data,encode('7: Гачан?')+b'\0')
  c+=pea(0x3af08)+bytes.fromhex('4eb900006c22588f')
  for ptr in (0x12a860,0x3af02,data):c+=pea(ptr)+bytes.fromhex('4eb900006c3a588f')
  c+=pea(0xff2ce8)+bytes.fromhex('4eb900007df0588f')
 else:
  for i,(name,status) in enumerate([('Джучи',3),('Угэдэй',2)]):
   addr=data+0x100+i*64;put(addr,encode(name)+b'\0');r[addr+0x13]=status;put(data+i*4,struct.pack('>I',addr))
  c+=bytes.fromhex('4878000c4878001048780008487800104eb9000109b24fef0010')
  c+=pea(data)+bytes.fromhex('4878000142a74eb90000aa744fef000c')
 c+=bytes.fromhex('60fe');put(base,c)
 r[0xa436:0xa43c]=bytes.fromhex('4eb9')+struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
 p=ROOT/f'build/diagnostics/{case}.gen';p.write_bytes(r)
 subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'12000',json.dumps(inputs)],check=True,capture_output=True)
 print('Rendered',case,flush=True)
