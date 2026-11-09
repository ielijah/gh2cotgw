"""Locate raw title tiles by matching indexed-colour patterns to a capture."""
from pathlib import Path
import struct,zlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def read_png(p):
    data=p.read_bytes(); pos=8; compressed=b''
    while pos<len(data):
        n=int.from_bytes(data[pos:pos+4],'big'); t=data[pos+4:pos+8]; d=data[pos+8:pos+8+n];pos+=12+n
        if t==b'IHDR': w,h=struct.unpack('>II',d[:8])
        if t==b'IDAT': compressed+=d
    raw=zlib.decompress(compressed);assert all(raw[y*(w*3+1)]==0 for y in range(h))
    return w,h,b''.join(raw[y*(w*3+1)+1:(y+1)*(w*3+1)] for y in range(h))
def canon(values):
    ids={}; out=bytearray()
    for v in values:
        if v not in ids: ids[v]=len(ids)
        out.append(ids[v])
    return bytes(out)
if __name__=='__main__':
    target=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'analysis/screen-original.png'
    x1,y1,x2,y2=map(int,sys.argv[2:6]) if len(sys.argv)>1 else (72,128,192,136)
    w,h,rgb=read_png(target)
    wanted={}
    for y in range(y1,y2,8):
        for x in range(x1,x2,8):
            pixels=[rgb[((y+dy)*w+x+dx)*3:((y+dy)*w+x+dx)*3+3] for dy in range(8) for dx in range(8)]
            signature=canon(pixels)
            if len(set(pixels))>1: wanted.setdefault(signature,[]).append((x,y))
    rom=(ROOT/'rom/original.gen').read_bytes(); hits=[]
    for off in range(0,len(rom)-32,2):
        raw=rom[off:off+32]; vals=[v for b in raw for v in (b>>4,b&15)]
        signature=canon(vals)
        if signature in wanted: hits.append(dict(offset=f'{off:06X}',screen=wanted[signature]))
    name='title-tiles.json' if len(sys.argv)==1 else 'button-tiles.json'
    (ROOT/'analysis'/name).write_text(json.dumps(hits,indent=2))
    print(hits)
