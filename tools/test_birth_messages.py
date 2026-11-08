"""Native childbirth text composition, including legacy padded names."""
from pathlib import Path
import struct,sys,subprocess,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
from birth_spacing import LORD,MOTHER
r=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes());base=len(r);data=base+0x1000;r.extend(bytes(0x2000))
def pea(a):return bytes.fromhex('4879')+struct.pack('>I',a)
c=bytearray.fromhex('46fc2700');expected=[]
for name,hook,parts in [('Чингисхан   ',LORD,[0x3ae22]),('Бортэ   ',MOTHER,[0x3ae0a,0x3ae04,0x3adfe]),('Бортэ',MOTHER,[0x3ae0a,0x12aa00,0x3adfe])]:
 i=len(expected);addr=data+i*64;raw=encode(name)+b'\0';r[addr:addr+len(raw)]=raw
 c+=pea(addr)+bytes.fromhex('4eb9')+struct.pack('>I',hook)+bytes.fromhex('588f')
 for p in parts:c+=pea(p)+bytes.fromhex('4eb900006c3a588f')
 for j in range(0,64,4):c+=bytes.fromhex('23f9')+struct.pack('>II',0xff2ce8+j,0xff9000+i*64+j)
 expected.append(['Лорд Чингисхан, поздравляю!','Бортэ родила дочь!','Бортэ родила сына!'][i])
c+=bytes.fromhex('33fca55a00ffdffe60fe');r[base:base+len(c)]=c;r[4:8]=struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
p=ROOT/'build/diagnostics/birth-messages.gen';p.write_bytes(r)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'120'],check=True,capture_output=True)
m=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());m[::2],m[1::2]=m[1::2],m[::2]
assert m[0xdffe:0xe000].hex()=='a55a'
for i,s in enumerate(expected):
 got=m[0x9000+i*64:0x9040+i*64].split(b'\0')[0];assert got==encode(s),(got,encode(s))
print('PASS: congratulations and both childbirth messages with exact spacing')
# Show the same production builders after normal map initialization.
inputs=[[1900,1910,3],[3000,3010,3],[4100,4110,8],[5100,5110,8],[5500,5510,8],[6400,6410,8],[7200,7210,8]]+[[t,t+10,8] for t in range(8100,10501,600)]
for i,(label,name,hook,parts) in enumerate([('congratulations','Чингисхан   ',LORD,[0x3ae22]),('birth-daughter','Бортэ   ',MOTHER,[0x3ae0a,0x3ae04,0x3adfe])]):
 r=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes());base=len(r);data=base+0x1000;r.extend(bytes(0x2000));raw=encode(name)+b'\0';r[data:data+len(raw)]=raw
 c=bytearray.fromhex('4eb900009c00')+pea(data)+bytes.fromhex('4eb9')+struct.pack('>I',hook)+bytes.fromhex('588f')
 for p in parts:c+=pea(p)+bytes.fromhex('4eb900006c3a588f')
 c+=pea(0xff2ce8)+bytes.fromhex('4eb900007df0588f60fe');r[base:base+len(c)]=c;r[0xa436:0xa43c]=bytes.fromhex('4eb9')+struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
 p=ROOT/f'build/diagnostics/{label}.gen';p.write_bytes(r)
 subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'12000',json.dumps(inputs)],check=True,capture_output=True)
 print('Rendered',label,flush=True)
