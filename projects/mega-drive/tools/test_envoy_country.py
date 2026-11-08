"""Run full envoy announcement and threat fragments on the emulated 68000."""
from pathlib import Path
import sys,json,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
rom=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
forms=json.loads((ROOT/'translation/envoy-country-forms.json').read_text(encoding='utf-8'))
forms['Неизвестные']='Неизвестные'
code=bytearray.fromhex('46fc2700')
def write(address,data):
    data+=bytes((-len(data))%4)
    for i in range(0,len(data),4):
        code.extend(bytes.fromhex('23fc')+data[i:i+4]+struct.pack('>I',address+i))
def snapshot(index):
    for j in range(0,64,4):
        code.extend(bytes.fromhex('23f9')+struct.pack('>II',0xff2ce8+j,0xff8000+index*64+j))
for i,(nom,gen) in enumerate(forms.items()):
    write(0xff2ce8,b'U'*64)
    write(0xfff000,encode(nom)+b'\0')
    write(0xff1a8c,(0xfff000).to_bytes(4,'big'))
    code.extend(bytes.fromhex('4eb90002f9fc'))
    snapshot(i)
write(0xff2ce8,b'U'*64)
write(0xfff000,encode('Тохтоа-беки')+b'\0')
suffix=bytes(rom).find(encode(', владыке степей'))
assert suffix>=0
code.extend(bytes.fromhex('48790003c9704eb900006c22588f487900fff0004eb900006c3a588f4879')+struct.pack('>I',suffix)+bytes.fromhex('4eb900006c3a588f'))
snapshot(len(forms))
code.extend(bytes.fromhex('33fca55a00ffdffe60fe'))
rom.extend(bytes(0x128000+len(code)-len(rom)));rom[0x128000:]=code
rom[4:8]=(0x128000).to_bytes(4,'big');rom[0x1a4:0x1a8]=(len(rom)-1).to_bytes(4,'big')
p=ROOT/'build/diagnostics/envoy-country.gen';p.write_bytes(rom)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'120'],check=True,capture_output=True)
ram=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());ram[::2],ram[1::2]=ram[1::2],ram[::2]
assert ram[0xdffe:0xe000].hex()=='a55a','CPU harness did not finish'
for i,(nom,gen) in enumerate(forms.items()):
    slot=ram[0x8000+i*64:0x8000+(i+1)*64]
    expected=encode('Прибыл посол от '+gen)
    assert slot.split(b'\0')[0]==expected,(nom,slot.hex())
    assert slot[len(expected)+1:]==b'U'*(63-len(expected)),nom
slot=ram[0x8000+len(forms)*64:0x8000+(len(forms)+1)*64]
assert slot.split(b'\0')[0].rstrip()==encode('Покорись Тохтоа-беки, владыке степей'),slot.hex()
print('PASS: 55 envoy announcements, single spaces, genitives, buffer canaries and threat fragments')
