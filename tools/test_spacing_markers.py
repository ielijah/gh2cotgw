"""Execute padding fixes and relationship-marker lookup on the 68000."""
from pathlib import Path
import sys,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
from orders_name import CODE
r=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
src=(ROOT/'rom/original.gen').read_bytes()
# Check both original relationship bitmaps, not merely their character codes.
for ch in (42,35):
 p=0x105800+(ch-32)*4
 glyph=[]
 for off in (0,2):
  tile=int.from_bytes(r[p+off:p+off+2],'big')
  raw=r[0x104000+(tile-64)*32:0x104000+(tile-63)*32]
  for y in range(8):
   glyph.append(sum((128>>x) for x in range(8) if (raw[y*4+x//2]>>(4 if x%2==0 else 0))&15))
 assert bytes(glyph)==src[0x46244+(ch-32)*16:0x46254+(ch-32)*16]
# Keep original concatenation; bypass only UI rendering and its wait in this test.
r[0xdb04:0xdb06]=bytes.fromhex('4e75');r[0x7caa:0x7cac]=bytes.fromhex('4e75')
base=len(r);data=base+0x2000;c=bytearray.fromhex('46fc2700');expected=[]
for i,name in enumerate(['Чингисхан   ','Чингисхан','Темучин','Дай Сечен  ','АБВГДЕЖЗИЙКЛ']):
 addr=data+i*64
 r.extend(bytes(max(0,addr+64-len(r))));r[addr:addr+len(encode(name))+1]=encode(name)+b'\0'
 c+=bytes.fromhex('487900049c084879')+struct.pack('>I',addr)+bytes.fromhex('4eb9')+struct.pack('>I',CODE)+bytes.fromhex('508f')
 for j in range(0,64,4):c+=bytes.fromhex('23f9')+struct.pack('>II',0xff2ce8+j,0xff9000+i*64+j)
 expected.append(encode(name.rstrip()+', каковы ваши приказы?'))
# Native status-to-marker lookup (person status is byte 13).
for status in range(4):
 c+=bytes.fromhex('13fc')+struct.pack('>H',status)+bytes.fromhex('00ffa013487900ffa0004eb90000873c588f13c0')+struct.pack('>I',0xff9200+status)
c+=bytes.fromhex('48790003d2244eb900006c22588f')
c+=bytes.fromhex('33fca55a00ffdffe60fe')
r[base:base+len(c)]=c;r[4:8]=struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
p=ROOT/'build/diagnostics/spacing-markers.gen';p.write_bytes(r)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'120'],check=True,capture_output=True)
m=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());m[::2],m[1::2]=m[1::2],m[::2]
assert m[0xdffe:0xe000].hex()=='a55a'
for i,wanted in enumerate(expected):assert m[0x9000+i*64:0x9040+i*64].split(b'\0')[0]==wanted,(i,m[0x9000+i*64:0x9040+i*64],wanted)
assert m[0x9200:0x9204]==b'  *#'
assert m[0x2ce8:0x2d20].split(b'\0')[0]==encode('Кого назначить главой ')
print('PASS: 5 names including legacy padding, governor prefix, 4 native relationship states and original marker pixels')
