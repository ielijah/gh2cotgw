"""Check prompt blink erasure and unchanged START pixels in the emulator."""
from pathlib import Path
import sys,subprocess,shutil,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from find_title import read_png
inputs=json.dumps([[1900,1910,3]])
def capture(rom,frame,name):
    subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(rom),str(frame),inputs],check=True,capture_output=True)
    source=ROOT/'analysis'/('screen-'+rom.stem+'.png')
    target=ROOT/'analysis'/name
    shutil.copyfile(source,target)
    return read_png(target)
rom=ROOT/'build/genghis2-ru-experimental.gen'
w,h,on=capture(rom,2500,'title-prompt-on.png')
_,_,off=capture(rom,2530,'title-prompt-off.png')
_,_,original=capture(ROOT/'rom/original.gen',2500,'title-prompt-original.png')
def pixel(data,x,y):return data[(y*w+x)*3:(y*w+x)*3+3]
assert any(pixel(on,x,y)!=b'\0\0\0' for y in range(192,208) for x in range(56,200))
assert all(pixel(off,x,y)==b'\0\0\0' for y in range(192,208) for x in range(56,200)),'Prompt leaves pixels when hidden'
assert all(pixel(on,x,y)==pixel(off,x,y) for y in range(h) for x in range(w) if not(56<=x<200 and 192<=y<208)),'Blink changes outside prompt'
assert all(pixel(on,152+x,y)==pixel(original,128+x,y) for y in range(192,208) for x in range(48)),'Original START changed'
def white_strokes(left):
    return {(x,y) for y in range(16) for x in range(11) if pixel(on,left+x,192+y)==bytes((172,206,238))}
assert white_strokes(123)==white_strokes(189) and white_strokes(123),'Cyrillic Т must match original Latin T'
(ROOT/'analysis/title-prompt-test.json').write_text(json.dumps(dict(status='PASS',blink_off_clean=True,start_pixels_unchanged=True,outside_prompt_unchanged=True),indent=2))
print('PASS: blinking prompt fully erased; original START pixels and outside area unchanged')
