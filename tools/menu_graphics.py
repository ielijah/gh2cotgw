"""Native-size caption tiles; preserves indexed palettes and resource dimensions."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WIDE=(0xed,0xee)
def address(index,resource):
    if resource in WIDE: return 0x110000+WIDE.index(resource)*0x400
    return 0x108000+index*0x200 if index<32 else 0x111000+(index-32)*0x200

def render(raw,resource,caption,font,src):
    tiles=len(raw)//64; width=tiles*8
    assert len(raw) in (256,384,512)
    attribute=0x9a<=resource<=0x9f
    background,foreground=(10,8) if attribute else (9,14)
    px=[[0]*width for _ in range(16)]
    for y in range(16):
        for x in range(width):
            v=raw[(y//8*tiles+x//8)*32+y%8*4+x%8//2]
            px[y][x]=(v>>(4 if x%2==0 else 0))&15
            if x>0 and y<15:px[y][x]=background
    menu=json.loads((ROOT/'translation/menu-font.json').read_text(encoding='utf-8'))
    def columns(text):
        out=[]
        for ch in text:
            if resource in (0xb9,0xba):
                glyph=font[ch] if ch in font else src[0x46244+(ord(ch)-32)*16:0x46254+(ord(ch)-32)*16]
                occupied=[x for x in range(8) if any(row&(128>>x) for row in glyph[:15])]
                out += [[bool(row&(128>>x)) for row in glyph[:15]] for x in range(min(occupied),max(occupied)+1)]
            else:
                rows=menu[ch];top=3 if ch.isupper() else 5
                assert all(len(row)==len(rows[0]) for row in rows)
                out += [[top<=y<top+len(rows) and rows[y-top][x]=='1' for y in range(15)] for x in range(len(rows[0]))]
            out.append([False]*15)
        return out[:-1]
    ink=[]
    parts=caption.split('|'); cell=width//len(parts)
    for index,part in enumerate(parts):
        cols=columns(part);assert len(cols)<=cell-1,(caption,len(cols),cell)
        left=index*cell+max(1,(cell-len(cols))//2)
        ink += [(left+x,y) for x in range(len(cols)) for y in range(15) if cols[x][y]]
    for x,y in ink:
        if not attribute and 0<x-1<width-1 and y+1<15:px[y+1][x-1]=15
    for x,y in ink:px[y][x]=foreground
    changed=bytearray(raw)
    for y in range(16):
        for x in range(0,width,2):changed[(y//8*tiles+x//8)*32+y%8*4+x%8//2]=(px[y][x]<<4)|px[y][x+1]
    return changed
