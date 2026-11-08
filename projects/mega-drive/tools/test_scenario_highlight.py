"""Regression for the last Cyrillic letter outside the old highlight width."""
from pathlib import Path
import sys,subprocess,json,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from find_title import read_png
inputs=[[1900,1910,3],[3000,3010,3],[4100,4110,8]]
frames=[]
for name,frame,buttons in [('scenario-highlight',4500,inputs),('scenario-highlight-return',5000,inputs+[[4600,4605,5],[4800,4805,4]])]:
    subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(ROOT/'build/genghis2-ru-experimental.gen'),str(frame),json.dumps(buttons)],check=True,capture_output=True)
    target=ROOT/f'analysis/{name}.png'
    shutil.copyfile(ROOT/'analysis/screen-genghis2-ru-experimental.png',target)
    w,h,data=read_png(target);frames.append(data)
    def green(left):
        return {(x,y) for y in range(16) for x in range(8) if data[((128+y)*w+left+x)*3:((128+y)*w+left+x)*3+3]==bytes((32,238,98))}
    assert green(224)==green(232) and len(green(232))==36,'Last и is not fully highlighted'
assert all(frames[0][(y*w+x)*3:(y*w+x)*3+3]==frames[1][(y*w+x)*3:(y*w+x)*3+3] for y in range(120,200) for x in range(80,240))
print('PASS: both final и glyphs green; scenario redraw unchanged after down/up')
