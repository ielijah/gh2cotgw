"""Check original question-building routine without invoking its UI wait."""
from pathlib import Path
import sys,json,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
r=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
items=json.loads((ROOT/'analysis/confirmation-audit.json').read_text(encoding='utf8'))
c=bytearray.fromhex('46fc2700')
for i,item in enumerate(items):
    c+=bytes.fromhex('4879')+struct.pack('>I',int(item['offset'],16))+bytes.fromhex('4eb90000aeca588f')
    for j in range(0,64,4):c+=bytes.fromhex('23f9')+struct.pack('>II',0xff2ce8+j,0xff8000+i*64+j)
c+=bytes.fromhex('33fca55a00ffdffe60fe')
base=len(r);r.extend(c);r[4:8]=struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
r[0xaea0:0xaea2]=bytes.fromhex('4e75')
p=ROOT/'build/diagnostics/confirmations.gen';p.write_bytes(r)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'120'],check=True,capture_output=True)
m=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());m[::2],m[1::2]=m[1::2],m[::2]
assert m[0xdffe:0xe000].hex()=='a55a'
for i,item in enumerate(items):
    text=m[0x8000+i*64:0x8040+i*64].split(b'\0')[0]
    assert text==encode(item['ru']),item
    assert text.count(b'?')==1 and b' ?' not in text,item
print(f'PASS: {len(items)} original confirmation builders, single question marks without padding')
