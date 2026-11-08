"""Execute the inflection hook on 68000 for every country and an unknown name."""
from pathlib import Path
import sys,json,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
from play_country import CODE
rom=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
forms=json.loads((ROOT/'translation/play-country-forms.json').read_text(encoding='utf-8'))
forms['Неизвестные']='Неизвестные'
code=bytearray.fromhex('46fc2700')
def write(address,data):
    data+=bytes((-len(data))%4)
    for i in range(0,len(data),4):
        code.extend(bytes.fromhex('23fc')+data[i:i+4]+struct.pack('>I',address+i))
for i,(nom,acc) in enumerate(forms.items()):
    dest=0xff8000+i*48
    write(dest,b'U'*48)
    write(dest,encode('Играть за ')+b'\0')
    write(0xfff000,encode(nom)+b'\0')
    code.extend(bytes.fromhex('487900fff0004879')+struct.pack('>I',dest)+bytes.fromhex('4eb9')+struct.pack('>I',CODE)+bytes.fromhex('508f'))
    code.extend(bytes.fromhex('48790003b3104879')+struct.pack('>I',dest)+bytes.fromhex('4eb900005302508f'))
code.extend(bytes.fromhex('33fca55a00ffdffe60fe'))
rom.extend(bytes(0x128000+len(code)-len(rom)))
rom[0x128000:]=code;rom[4:8]=(0x128000).to_bytes(4,'big')
rom[0x1a4:0x1a8]=(len(rom)-1).to_bytes(4,'big')
p=ROOT/'build/diagnostics/play-country.gen';p.parent.mkdir(exist_ok=True)
p.write_bytes(rom)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'120'],check=True,capture_output=True)
ram=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());ram[::2],ram[1::2]=ram[1::2],ram[::2]
assert ram[0xdffe:0xe000].hex()=='a55a','CPU harness did not finish'
for i,(nom,acc) in enumerate(forms.items()):
    slot=ram[0x8000+i*48:0x8000+(i+1)*48]
    assert slot.split(b'\0')[0]==encode('Играть за '+acc+'?'),(nom,slot.hex())
    assert slot[36:]==b'U'*12,(nom,'Selection flags overwritten')
print(f'PASS: {len(forms)} native country confirmations, RAM inputs, fallback and buffer canaries')
