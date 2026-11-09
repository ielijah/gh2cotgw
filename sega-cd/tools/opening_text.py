"""Translate native opening tilemaps without changing bank sizes or timing."""
from pathlib import Path
import json,struct,hashlib,sys,zlib
ROOT=Path(__file__).resolve().parents[1]
MAPS=((0xf0,14,2,'ПРЕДСТАВЛЯЕТ'),(0x128,24,3,'ИСТОРИЧЕСКАЯ СТРАТЕГИЯ'),(0x1b8,28,2,'ПРОДЮСЕР КО СИБУСАВА'))
QUOTE=['Был серый волк,','рождённый по воле Неба.','Со своей женой, белой ланью,','он переплыл великое озеро','и пришёл сюда.','Из Тайной истории','монголов']

def png(path,pixels,palette,scale=3):
    rows=[]
    for row in pixels:
        line=b''.join(bytes(palette[v])*scale for v in row)
        rows.extend([b'\0'+line]*scale)
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',len(pixels[0])*scale,len(pixels)*scale,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))

def tile_pixels(bank,tile):
    raw=bank[tile*32:(tile+1)*32]
    assert len(raw)==32
    return [[(raw[y*4+x//2]>>(4 if x%2==0 else 0))&15 for x in range(8)] for y in range(8)]

def tile_bytes(pixels):
    return bytes((row[x]<<4)|row[x+1] for row in pixels for x in range(0,8,2))

def canvas(data,map_offset,w,h,tiles,first):
    out=[[0]*(w*8) for _ in range(h*8)]
    for n in range(w*h):
        cell=struct.unpack_from('>H',data,map_offset+n*2)[0]
        px=tile_pixels(tiles,(cell&0x7ff)-first)
        for y in range(8):
            for x in range(8):
                out[n//w*8+y][n%w*8+x]=px[7-y if cell&0x1000 else y][7-x if cell&0x800 else x]
    return out

def apply(image,source,files):
    entry=files['G2GRPOE.DAT;1'];base=entry['lba']*2048
    original=source[base:base+entry['size']];data=bytearray(original)
    # Publisher bank: raw tiles at 356, loaded at VRAM tile 2C0.
    start=0x356;count=0x17e
    bank=bytearray(original[start:start+count*32])
    target_positions={p for off,w,h,_ in MAPS for p in range(off,off+w*h*2,2)}
    protected={struct.unpack_from('>H',original,p)[0]&0x7ff for p in range(0,0x356,2) if p not in target_positions}
    available=[i for i in range(count) if i+0x2c0 not in protected]
    sys.path.insert(0,str(ROOT.parent/'mega-drive/tools'))
    from intro_captions import lettering,tiles
    generated={};cursor=0;previews=[]
    for off,w,h,text in MAPS:
        px=lettering(text,w*8,h*8)
        previews.append((f'opening-{off:04x}-ru.png',px))
        for n,raw in enumerate(tiles(px)):
            if raw not in generated:
                assert cursor<len(available),'Publisher tile allocation exhausted'
                i=available[cursor];cursor+=1;generated[raw]=i
                bank[i*32:(i+1)*32]=raw
            flags=struct.unpack_from('>H',original,off+n*2)[0]&0xe000
            struct.pack_into('>H',data,off+n*2,flags|0x2c0+generated[raw])
    data[start:start+len(bank)]=bank
    # The next loaded block begins at sector 7. First card is a 28x22 map,
    # with 611 raw tiles and a palette-animated text ink at index 3.
    block=7*2048;mp=block;ts=block+0x354c;size=0x263*32
    old=canvas(original,mp,28,22,original[ts:ts+size],0x200)
    px=[[6 if v==3 else v for v in row] for row in old]
    font=(ROOT/'assets/cyrillic-8x16.bin').read_bytes()
    alphabet=''.join(chr(ord('А')+i) for i in range(64))+'Ёё'
    glyphs={ch:list(font[n*16:n*16+16]) for n,ch in enumerate(alphabet)}
    main_entry=files['SMAIN.PRG;1'];mb=main_entry['lba']*2048
    for ch,idx in {',':0xe8,'.':6}.items():glyphs[ch]=list(source[mb+0x36490+idx*16:mb+0x36490+(idx+1)*16])
    glyphs[' ']=[0]*16
    def shape(ch):
        rows=glyphs[ch];columns=[x for x in range(8) if any(v&(128>>x) for v in rows)]
        return rows,(min(columns),max(columns)+1) if columns else (0,3)
    for text,top in zip(QUOTE,(25,43,61,79,97,137,155)):
        parts=[shape(ch) for ch in text];width=sum(b-a+1 for _,(a,b) in parts)-1
        assert width<=204,(text,width)
        left=(224-width)//2
        for rows,(a,b) in parts:
            for y,bits in enumerate(rows):
                for x in range(a,b):
                    if bits&(128>>x):px[top+y][left+x-a]=3
            left+=b-a+1
    # Re-deduplicate this isolated card; keep the 611-tile allocation and
    # the palette/priority bits. Other map/tile banks stay byte-identical.
    unique={};packed=bytearray()
    for n in range(28*22):
        raw=tile_bytes([row[n%28*8:n%28*8+8] for row in px[n//28*8:n//28*8+8]])
        if raw not in unique:unique[raw]=len(unique);packed.extend(raw)
        flags=struct.unpack_from('>H',original,mp+n*2)[0]&0xe000
        struct.pack_into('>H',data,mp+n*2,flags|0x200+unique[raw])
    assert len(packed)<=size,('Parchment tile allocation exhausted',len(packed),size)
    data[ts:ts+size]=packed+bytes(size-len(packed))
    op=files['OPENING.PRG;1'];ob=op['lba']*2048
    words=struct.unpack_from('>16H',source,ob+0x200a)
    pal=[tuple(((v>>s)&14)*255//14 for s in (0,4,8)) for v in words]
    out=ROOT/'analysis';png(out/'opening-parchment-ru.png',px,pal)
    for name,pixels in previews:png(out/name,pixels,[(v*17,)*3 for v in range(16)])
    # Only map words and the two existing raw tile banks may differ.
    ranges=[(off,w*h*2) for off,w,h,_ in MAPS]+[(start,count*32),(mp,28*22*2),(ts,size)]
    allowed=bytearray(len(original))
    for off,length in ranges:allowed[off:off+length]=b'\1'*length
    assert all(a==b or yes for a,b,yes in zip(original,data,allowed))
    for i in protected:
        if 0x2c0<=i<0x2c0+count:
            off=start+(i-0x2c0)*32;assert data[off:off+32]==original[off:off+32]
    image[base:base+len(data)]=data
    asset=ROOT/'assets/opening';asset.mkdir(exist_ok=True)
    records=[]
    for off,length in ranges:
        path=asset/f'{off:06x}.bin';raw=bytes(data[off:off+length]);path.write_bytes(raw)
        records.append(dict(offset=off,length=length,asset=str(path.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),source_sha256=hashlib.sha256(original[off:off+length]).hexdigest()))
    return dict(file=entry['path'],ranges=records,publisher_captions=[t for _,_,_,t in MAPS],quote=QUOTE,
                publisher_tiles_used=cursor,parchment_tiles_used=len(unique),emulator_run=False)
