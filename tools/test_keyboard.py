"""Exercise the real name-entry screen using controller inputs in a diagnostic ROM."""
from pathlib import Path
import sys, json, subprocess, shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
from name_keyboard import KEYS

rom=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
# After normal startup, replace scenario selection with the original name UI.
rom[0x263d4:0x263da]=bytes.fromhex('4ef900117000')
code=bytes.fromhex('42a74eb900022872588f4eb900022af233fca55a00ffdffe60fe')
rom[0x117000:0x117000+len(code)]=code
path=ROOT/'build/diagnostics/keyboard.gen'
path.write_bytes(rom)
inputs=[[1900,1910,3],[3000,3010,3],[4100,4110,8]]
frame=4600
position=0
def press(button):
    global frame
    inputs.append([frame,frame+5,button]);frame+=35
def select(char):
    global position
    target=KEYS.index(char)
    row,col=divmod(position,10);tr,tc=divmod(target,10)
    while row!=tr:
        press(5 if row<tr else 4);row+=1 if row<tr else -1
    while col!=tc:
        press(7 if col<tc else 6);col+=1 if col<tc else -1
    press(8);position=target
def capture(label, expected, done=False):
    subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(path),str(frame+100),json.dumps(inputs)],cwd=ROOT,check=True,capture_output=True)
    ram=bytearray((ROOT/'analysis/memory-2.bin').read_bytes())
    ram[::2],ram[1::2]=ram[1::2],ram[::2]
    actual=ram[0x7970:0x797b].split(b'\0')[0]
    assert actual==encode(expected),(label,actual.hex(),encode(expected).hex())
    if done: assert ram[0xdffe:0xe000].hex()=='a55a','Start did not finish input'
    shutil.copyfile(ROOT/'analysis/screen-keyboard.png',ROOT/f'analysis/keyboard-{label}.png')
    print('PASS:',label,repr(expected),flush=True)

for ch in 'АЁаёюя':select(ch)
capture('mixed','АЁаёюя')
press(0)
capture('delete','АЁаёю')
select('я')
for ch in 'я-яя':select(ch)
select('Б') # eleventh character must be rejected
capture('limit','АЁаёюяя-яя')
press(3)
capture('complete','АЁаёюяя-яя',True)
(ROOT/'analysis/keyboard-test.json').write_text(json.dumps(dict(status='PASS',cases=['mixed case and Yo','delete','ten-character limit','Start completion']),indent=2))
