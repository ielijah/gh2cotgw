"""Execute ending-name and country lookups on the 68000."""
from pathlib import Path
import sys,json,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
from unification import LOOKUP,NAMES,COUNTRIES
rom=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
code=bytearray.fromhex('46fc2700');cases=[]
for filename,table in [('unification-names.json',NAMES),('envoy-country-forms.json',COUNTRIES)]:
    forms=json.loads((ROOT/'translation'/filename).read_text(encoding='utf8'))
    forms['Неизвестный']='Неизвестный'
    for nom,case in forms.items():
        raw=(encode(nom)+b'\0').ljust(32,b'\0')
        for off in range(0,32,4):code+=bytes.fromhex('23fc')+raw[off:off+4]+struct.pack('>I',0xfff000+off)
        code+=bytes.fromhex('207c00fff000247c')+struct.pack('>I',table)+bytes.fromhex('4eb9')+struct.pack('>I',LOOKUP)+bytes.fromhex('23c8')+struct.pack('>I',0xff8000+len(cases)*4)
        cases.append((nom,case))
code+=bytes.fromhex('33fca55a00ffdffe60fe')
base=len(rom);rom.extend(code);rom[4:8]=struct.pack('>I',base);rom[0x1a4:0x1a8]=struct.pack('>I',len(rom)-1)
p=ROOT/'build/diagnostics/unification-lookup.gen';p.write_bytes(rom)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'120'],check=True,capture_output=True)
ram=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());ram[::2],ram[1::2]=ram[1::2],ram[::2]
assert ram[0xdffe:0xe000].hex()=='a55a'
for i,(nom,case) in enumerate(cases):
    ptr=int.from_bytes(ram[0x8000+i*4:0x8004+i*4],'big')
    data=ram[ptr&65535:] if ptr>=0xff0000 else rom[ptr:]
    assert data.split(b'\0')[0]==encode(case),(nom,case)
print(f'PASS: {len(cases)} instrumental/genitive lookups and unknown-name fallback')
