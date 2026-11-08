"""Check Cyrillic widths and the unmodified name/age formatter on the 68000."""
from pathlib import Path
import struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build import encode
r=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes());base=len(r);data=base+0x2000;r.extend(bytes(0x3000))
def pea(p):return bytes.fromhex('4879')+struct.pack('>I',p)
c=bytearray.fromhex('46fc2700')
cases=[('Татьяна',7),('Юлия',4),('юяюяюяюяюя',10),('Ёё',2),('\x1bC1Татьяна',7),('Юлия\nТатьяна',7)]
for i,(text,width) in enumerate(cases):
 raw=encode(text)+b'\0';addr=data+i*64;r[addr:addr+len(raw)]=raw
 c+=pea(addr)+bytes.fromhex('4eb9000053ac588f33c0')+struct.pack('>I',0xff9000+i*2)
# Original formatter sends fragments to the original append routine.
args=data+0x400;r[args:args+8]=struct.pack('>II',data,15)
c+=pea(0x3b7b2)+bytes.fromhex('4eb900006c22588f')+pea(0x6c3a)+pea(args)+pea(0x3baca)+bytes.fromhex('4eb9000056644fef000c33fca55a00ffdffe60fe')
r[base:base+len(c)]=c;r[4:8]=struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
p=ROOT/'build/diagnostics/cyrillic-width.gen';p.write_bytes(r)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'120'],check=True,capture_output=True)
m=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());m[::2],m[1::2]=m[1::2],m[::2]
assert m[0xdffe:0xe000].hex()=='a55a'
for i,(text,width) in enumerate(cases):assert int.from_bytes(m[0x9000+i*2:0x9002+i*2],'big')==width,text
assert m[0x2ce8:0x2d20].split(b'\0')[0]==encode('Татьяна    15\n'),m[0x2ce8:0x2d20]
print('PASS: Cyrillic widths, style escapes, line breaks, original 13-column name/age format')
