"""Exercise original 68000 name generators with translated pointer tables."""
from pathlib import Path
import sys,subprocess,struct,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
rom=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
functions=[]
for base in (0x49f9a,0x4a0be):
 functions += [int.from_bytes(rom[base+i*4:base+i*4+4],'big') for i in range(8)]
code=bytearray.fromhex('46fc2700');records=[]
for function in functions:
 for seed in range(32):
  out=0xff8000+len(records)*16
  for off in range(0,16,4):code+=bytes.fromhex('23fc55555555')+struct.pack('>I',out+off)
  code+=bytes.fromhex('23fc')+struct.pack('>I',seed*1009+17)+bytes.fromhex('00ffc9a4')
  code+=bytes.fromhex('4879')+struct.pack('>I',out)+bytes.fromhex('4eb9')+struct.pack('>I',function)+bytes.fromhex('588f')
  records.append((function,seed,out))
code+=bytes.fromhex('33fca55a00ffdffe60fe')
rom.extend(bytes(max(0,0x110000+len(code)-len(rom))))
rom[0x110000:0x110000+len(code)]=code;rom[4:8]=struct.pack('>I',0x110000)
rom[0x1a4:0x1a8]=struct.pack('>I',len(rom)-1)
p=ROOT/'build/diagnostics/name-generators.gen';p.write_bytes(rom)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'60'],cwd=ROOT,check=True,capture_output=True)
ram=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());ram[::2],ram[1::2]=ram[1::2],ram[::2]
assert ram[0xdffe:0xe000].hex()=='a55a','Harness did not finish'
allowed=set(encode('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя -'))
longest=0
for fn,seed,out in records:
 slot=ram[out&65535:(out&65535)+16]
 assert 0 in slot[:13],(hex(fn),seed,'Name exceeds 12 bytes',slot.hex())
 assert slot[13:]==b'UUU',(hex(fn),seed,'Canary changed')
 name=slot.split(b'\0')[0];assert name and set(name)<=allowed,(hex(fn),seed,name.hex())
 longest=max(longest,len(name))
print(f'PASS: {len(records)} native generated names, all Cyrillic, longest {longest} bytes, canaries intact')
(ROOT/'analysis/name-generators-test.json').write_text(json.dumps(dict(cases=len(records),max_name_bytes=longest,status='PASS'),indent=2))
