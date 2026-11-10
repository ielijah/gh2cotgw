"""Extract all eleven native success cards, without modifying the game image.

XXX.PRG CPU 69E98 draws the success scene. At 69FAC it selects special
wife IDs 0/1/7 -> cards 0/1/2, otherwise phenotype (13B2A) + 3.
SMAIN CPU 15706 loads GH2GRP sectors 16B + index*4, four sectors each.
The next resource begins at sector 197: exactly eleven slots.
CPU 6A012 uploads 200 sequential tiles; 6A034 draws a 10x20 tile map.
Palette bank 1 comes from XXX.PRG CPU 6ADE8.
"""
from pathlib import Path
import json, struct, hashlib, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from opening_text import png, tile_pixels

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/harem-success'
OUT.mkdir(exist_ok=True)
inventory=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
source=(ROOT/'disc'/inventory['image']).read_bytes()
assert hashlib.sha256(source).hexdigest()==inventory['sha256']
files={f['path']:f for f in inventory['files']}
def payload(name):
    f=files[name]
    return source[f['lba']*2048:f['lba']*2048+f['size']]
graphics=payload('GH2GRP.DAT;1')
overlay=payload('XXX.PRG;1')
palette=[tuple(((v>>shift)&14)*255//14 for shift in (0,4,8))
         for v in struct.unpack_from('>16H',overlay,0x4de8)]
digits=['111101101101111','010110010010111','111001111100111',
        '111001111001111','101101111001001','111100111001111',
        '111100111101111','111001001001001','111101111101111',
        '111101111001111']
sheet=[[0]*528 for _ in range(356)]
records=[]
for index in range(11):
    offset=(0x16b+index*4)*2048
    raw=graphics[offset:offset+6400]
    pixels=[[0]*80 for _ in range(160)]
    for n in range(200):
        tile=tile_pixels(raw,n)
        for y in range(8):
            pixels[n//10*8+y][n%10*8:n%10*8+8]=tile[y]
    filename=f'girl-{index+1:02}.png'
    png(OUT/filename,pixels,palette,3)
    left=index%6*88+4;top=index//6*178+14
    for y,row in enumerate(pixels):sheet[top+y][left:left+80]=row
    label=str(index+1);x=left+(80-(len(label)*4-1))//2
    for ch in label:
        glyph=digits[int(ch)]
        for y in range(5):
            for dx in range(3):
                if glyph[y*3+dx]=='1':sheet[top-10+y][x+dx]=7
        x+=4
    records.append(dict(index=index,filename=filename,offset=hex(offset),
                        raw_sha256=hashlib.sha256(raw).hexdigest()))
png(OUT/'all-girls.png',sheet,palette,3)
(OUT/'manifest.json').write_text(json.dumps(dict(
    source_sha256=inventory['sha256'],count=11,width=80,height=160,
    scale=3,graphics_file='GH2GRP.DAT;1',palette_file='XXX.PRG;1',
    palette_offset='0x4de8',records=records),ensure_ascii=False,indent=2)+'\n','utf8')
print(f'Extracted {len(records)} success cards: {OUT}')
