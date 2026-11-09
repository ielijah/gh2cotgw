"""Exercise the production prisoner menu rendering on an initialized game map."""
from pathlib import Path
import subprocess,sys,json,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from find_title import read_png
rom=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
# Use the exact production drawing and selection instructions, with three choices.
code=bytes.fromhex('4eb900009c007a03')+rom[0x35c9a:0x35d0e]+bytes.fromhex('60fe')
rom.extend(code);rom[0xa436:0xa43c]=bytes.fromhex('4eb900128000')
rom[0x1a4:0x1a8]=(len(rom)-1).to_bytes(4,'big')
p=ROOT/'build/diagnostics/prisoner-menu.gen';p.write_bytes(rom)
inputs=[[1900,1910,3],[3000,3010,3],[4100,4110,8],[5100,5110,8],[5500,5510,8],[6400,6410,8],[7200,7210,8]]+[[t,t+10,8] for t in range(8100,10501,600)]
frames=[]
for name,extra in [('first',[]),('last',[[12100,12105,5],[12300,12305,5]]),('return',[[12100,12105,5],[12300,12305,5],[12500,12505,4],[12700,12705,4]])]:
    subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'13000',json.dumps(inputs+extra)],check=True,capture_output=True)
    target=ROOT/f'analysis/prisoner-menu-{name}.png'
    shutil.copyfile(ROOT/'analysis/screen-prisoner-menu.png',target)
    w,h,rgb=read_png(target)
    frames.append(b''.join(rgb[(y*w+128)*3:(y*w+248)*3] for y in range(56,120)))
assert frames[0]==frames[2],'Menu fails to restore after down/down/up/up'
assert frames[0]!=frames[1],'Selection did not move'
print('PASS: widened prisoner menu, three options, selection return restores pixels')
