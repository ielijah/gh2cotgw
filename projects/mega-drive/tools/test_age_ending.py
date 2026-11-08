"""Render the original daughter selector and ending sequence with controlled data."""
from pathlib import Path
import struct,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build import encode
from graphics_codec import decode
from ending_caption import MAP,artwork
rom=(ROOT/'build/genghis2-ru-experimental.gen').read_bytes();src=(ROOT/'rom/original.gen').read_bytes()
raw,_=decode(rom[int.from_bytes(rom[0xce9ec:0xce9f0],'big'):]);old,px=artwork(src);assert raw[:len(old)]==old
for i in range(20):
 t=int.from_bytes(rom[MAP+i*2:MAP+i*2+2],'big')&2047
 want=bytes((px[i//10*8+y][i%10*8+x]<<4)|px[i//10*8+y][i%10*8+x+1] for y in range(8) for x in range(0,8,2))
 assert raw[(t-640)*32:(t-639)*32]==want and t<0x6c0
inputs=[[1900,1910,3],[3000,3010,3],[4100,4110,8],[5100,5110,8],[5500,5510,8],[6400,6410,8],[7200,7210,8]]+[[t,t+10,8] for t in range(8100,10501,600)]
def pea(p):return bytes.fromhex('4879')+struct.pack('>I',p)
for label in ['daughter-age','ending-russian']:
 r=bytearray(rom);base=len(r);data=base+0x1000;r.extend(bytes(0x2000))
 if label=='daughter-age':
  r[data:data+4]=struct.pack('>I',data+64);r[data+64:data+72]=encode('Татьяна')+b'\0';r[data+64+13]=15
  c=bytes.fromhex('4eb900009c00')+pea(0x3b7b2)+pea(data)+bytes.fromhex('487800014eb90002a41e4fef000c60fe')
 else:c=bytes.fromhex('4eb900038f044eb900038c1860fe')
 r[base:base+len(c)]=c;r[0xa436:0xa43c]=bytes.fromhex('4eb9')+struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
 p=ROOT/f'build/diagnostics/{label}.gen';p.write_bytes(r)
 subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),str(12000 if label=='daughter-age' else 16000),json.dumps(inputs)],check=True,capture_output=True)
 print('Rendered',label,flush=True)
print('PASS: ending bank preserves original tiles; all new caption pixels and VRAM bounds match')
