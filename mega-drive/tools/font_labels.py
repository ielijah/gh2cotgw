from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from emulate import png
b=(ROOT/'rom/original.gen').read_bytes();r=next((ROOT/'rom/reference').glob('*.md')).read_bytes()
w,h=576,1152;p=bytearray(w*h*3)
def draw(glyph,x,y,scale,colour):
    for row,value in enumerate(glyph):
        for col in range(8):
            if value&(128>>col):
                for dy in range(scale):
                    for dx in range(scale):
                        off=((y+row*scale+dy)*w+x+col*scale+dx)*3;p[off:off+3]=bytes(colour)
for i in range(96):
    x=(i%8)*72;y=(i//8)*96
    for j,ch in enumerate(f'{i+32:02X}'):
        draw(b[0x46244+(ord(ch)-32)*16:0x46254+(ord(ch)-32)*16],x+20+j*9,y,1,(0,255,0))
    draw(r[0x46244+i*16:0x46254+i*16],x+20,y+24,4,(255,255,255))
png(ROOT/'analysis/font-reference-labelled.png',w,h,p)
