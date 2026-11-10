"""Replace END in all five ending banks, retaining the 14 native caption tiles."""
from pathlib import Path
import struct, hashlib

ROOT = Path(__file__).resolve().parents[1]
# Map, raw caption tiles, first native tile. No loader or VRAM changes.
FIELDS = [(0x291b8,0x35460,0x4e7), (0x37a34,0x4a4dc,0x4c9),
          (0x4c368,0x61410,0x4c0), (0x64808,0x76770,0x4c9),
          (0x79130,0x8bc98,0x46d)]

def patches(source, base):
    pixels = (ROOT/'assets/ending-caption-pixels.bin').read_bytes()
    assert len(pixels) == 80*16 and set(pixels) == {0,1,7}
    assert all(pixels[y*80+x] == 0 for y in range(16)
               for x in list(range(8))+list(range(64,80)))
    raw = b''.join(bytes(pixels[(row*8+y)*80+col*8+x]<<4 |
                         pixels[(row*8+y)*80+col*8+x+1]
                         for y in range(8) for x in range(0,8,2))
                   for row in range(2) for col in range(1,8))
    assert len(raw) == 14*32
    reference = source[base+FIELDS[0][1]:base+FIELDS[0][1]+448]
    for mp, tiles, first in FIELDS:
        expected = [0xc248,0xc248]+[0xc000+first+i for i in range(6)]+[0xc248]*2
        expected += [0xc000+first+i for i in (6,7,8,9,10,11,8,12,6,13)]
        assert source[base+mp:base+mp+40] == struct.pack('>20H',*expected)
        assert source[base+tiles:base+tiles+448] == reference
        cells = []
        for row in range(2):
            cells += [0xc248]+[0xc000+first+row*7+i for i in range(7)]+[0xc248]*2
        yield mp, struct.pack('>20H',*cells)
        yield tiles, raw

def apply(image, source, files):
    base = files['G2GRPOE.DAT;1']['lba']*2048
    records = []
    for off, raw in patches(source,base):
        image[base+off:base+off+len(raw)] = raw
        records.append(dict(offset=off,length=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    return dict(file='G2GRPOE.DAT;1',caption='КОНЕЦ',variants=5,ranges=records,
                font_origin='Adapted serif artwork from mega-drive/tools/ending_caption.py; original E, palette and shadow retained')
