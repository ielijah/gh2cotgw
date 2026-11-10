"""Russian title and blinking prompt in the existing opening resource allocation."""
from pathlib import Path
import struct, hashlib
ROOT=Path(__file__).resolve().parents[1]
BLOCK=0x3800

def patches(source,files):
    gf=files['G2GRPOE.DAT;1'];base=gf['lba']*2048
    g=source[base+BLOCK:base+BLOCK+0x24800]
    assert g[0x24304:0x24800]==bytes(0x4fc)
    assert g[0x242fc:0x24304]==bytes.fromhex('000ad05c000b2a3c')
    unique={};bank=bytearray();maps=[]
    for asset,w,h in [('title-russian-pixels.bin',192,88),('title-prompt-russian-pixels.bin',144,16)]:
        px=(ROOT/'assets'/asset).read_bytes();assert len(px)==w*h and max(px)<16
        cells=[]
        for ty in range(h//8):
            for tx in range(w//8):
                raw=bytes(px[(ty*8+y)*w+tx*8+x]<<4|px[(ty*8+y)*w+tx*8+x+1]
                          for y in range(8) for x in range(0,8,2))
                if raw not in unique:unique[raw]=0x200+len(unique);bank.extend(raw)
                cells.append(0xa000|unique[raw])
        maps.append(struct.pack('>'+str(len(cells))+'H',*cells))
    assert 0x22a3c+len(bank)<=0x247b0 and max(unique.values())<0x6c0
    yield 'G2GRPOE.DAT;1',BLOCK+0x3314,maps[0]
    yield 'G2GRPOE.DAT;1',BLOCK+0x22a3c,bytes(bank)+bytes(0x247b0-0x22a3c-len(bank))
    yield 'G2GRPOE.DAT;1',BLOCK+0x247b0,g[0x242fc:0x24304]
    yield 'G2GRPOE.DAT;1',BLOCK+0x247b8,maps[1]
    op=files['OPENING.PRG;1'];ob=op['lba']*2048
    edits=[(0x740,'000b42fc','000b47b0'),(0x750,'000b4300','000b47b4'),
           (0x748,'00c6',struct.pack('>H',len(unique)).hex()),
           (0x1d1a,'00093524','000b47b8')]
    for off in (0x1d26,0x1d6e,0x1d98,0x1dce,0x1df6):edits.append((off,'000a','0012'))
    for off in (0x1d2e,0x1d76,0x1da0,0x1dd6,0x1dfe):edits.append((off,'000b','0007'))
    for off,old,new in edits:
        raw=bytes.fromhex(new);assert source[ob+off:ob+off+len(raw)]==bytes.fromhex(old),(hex(off),old)
        yield 'OPENING.PRG;1',off,raw

def apply(image,source,files):
    ranges=[]
    for file,off,raw in patches(source,files):
        a=files[file]['lba']*2048+off;image[a:a+len(raw)]=raw
        ranges.append(dict(file=file,offset=off,length=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    return dict(title='Серый волк и белая лань',subtitle='Тайная история Юань',prompt='НАЖМИ START',ranges=ranges)
