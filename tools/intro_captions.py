"""Native tile lettering for the publisher cards and licensing caption."""
from pathlib import Path
import json
from graphics_codec import decode, encode_literals
ROOT=Path(__file__).resolve().parents[1]
KOEI_BANK=0x122000
LICENSE_MAP=0x117600
PRESENTS_MAP=0x117800
CAPTIONS=((0x60302,28,2,'ПРОДЮСЕР КО СИБУСАВА'),
          (0x60372,14,2,'KOEI ПРЕДСТАВЛЯЕТ'),
          (0x603aa,8,3,'ИЗ СЕРИИ'),
          (0x603da,28,2,'ИСТОРИЧЕСКИХ СТРАТЕГИЙ'))

def lettering(text,width,height,ink=15):
    font=json.loads((ROOT/'translation/intro-italic-font.json').read_text(encoding='utf-8'))
    length=sum(len(font[c][0])+2 for c in text)-2+3
    assert length<=width,(text,length,width)
    px=[[0]*length for _ in range(7)]
    left=0; top=0
    for ch in text:
        for y,row in enumerate(font[ch]):
            for x,bit in enumerate(row):
                if bit=='1':
                    pos=left+x+(6-y)//3
                    px[top+y][pos]=ink
        left+=len(font[ch][0])+2
    scaled_width=min(width,round(length*1.35))
    out=[[0]*width for _ in range(height)]
    left=(width-scaled_width)//2; top=(height-11)//2
    for y in range(11):
        for x in range(scaled_width):
            out[top+y][left+x]=px[y*7//11][x*length//scaled_width]
    return out

def tiles(px):
    for y in range(0,len(px),8):
        for x in range(0,len(px[0]),8):
            yield bytes((px[y+dy][x+dx]<<4)|px[y+dy][x+dx+1] for dy in range(8) for dx in range(0,8,2))

def apply(rom,src):
    ptr=int.from_bytes(src[0x6146a:0x6146e],'big')
    old,_=decode(src[ptr:]);bank=bytearray(old)
    known={old[i:i+32]:0x200+i//32 for i in range(0,len(old),32)}
    def append(raw):
        if raw not in known:
            known[raw]=0x200+len(bank)//32;bank.extend(raw)
        return known[raw]
    for address,w,h,text in CAPTIONS:
        target=address
        if address==0x60372:
            w=20;target=PRESENTS_MAP
        for i,raw in enumerate(tiles(lettering(text,w*8,h*8))):
            flags=int.from_bytes(src[address:address+2],'big')&0xe000
            rom[target+i*2:target+i*2+2]=(flags|append(raw)).to_bytes(2,'big')
    assert src[0x37320:0x37324]==(0x60372).to_bytes(4,'big')
    rom[0x37320:0x37324]=PRESENTS_MAP.to_bytes(4,'big')
    rom[0x3732a:0x3732c]=(20).to_bytes(2,'big')
    rom[0x37332:0x37334]=(6).to_bytes(2,'big')
    assert len(bank)//32+0x200<0x700
    packed=encode_literals(bank)
    assert KOEI_BANK+len(packed)<=len(rom)
    rom[KOEI_BANK:KOEI_BANK+len(packed)]=packed
    rom[0x6146a:0x6146e]=KOEI_BANK.to_bytes(4,'big')
    # Preserve the copyright line exactly; replace only the licensing line.
    from title_logo import BANK,TILES
    count=int.from_bytes(rom[0x3747c:0x3747e],'big')
    address=0xcecf0; px=[[0]*224 for _ in range(32)]
    for i in range(112):
        t=int.from_bytes(src[address+i*2:address+i*2+2],'big')
        raw=src[0xcf962+((t&2047)-512)*32:0xcf962+((t&2047)-511)*32]
        for y in range(8):
            for x in range(8):px[i//28*8+y][i%28*8+x]=(raw[y*4+x//2]>>(4 if x%2==0 else 0))&15
    # Original white index is 15; retain the caption's original palette flags.
    px[16:]=lettering('ПО ЛИЦЕНЗИИ SEGA ENTERPRISES, LTD.',224,16)
    existing={bytes(rom[BANK+i*32:BANK+(i+1)*32]):0x200+i for i in range(count)}
    # D800 contains the horizontal-scroll table: tiles 6C0+ are NOT safe.
    # Reuse old logo tiles referenced by no other original intro map.
    logo={int.from_bytes(src[p:p+2],'big')&2047 for p in range(0xce9f0,0xcec00,2)}
    other={int.from_bytes(src[p:p+2],'big')&2047 for p in range(0xcec00,0xcf962,2)}
    reusable=logo-other
    existing={raw:tile for raw,tile in existing.items() if tile not in reusable}
    free=iter(sorted(reusable))
    for i,raw in enumerate(tiles(px)):
        if raw not in existing:
            tile=next(free)
            assert 0x200<=tile<0x6c0
            existing[raw]=tile
            offset=(tile-0x200)*32
            rom[BANK+offset:BANK+offset+32]=raw
            rom[TILES+offset:TILES+offset+32]=raw
        flags=int.from_bytes(src[address+i*2:address+i*2+2],'big')&0xe000
        rom[LICENSE_MAP+i*2:LICENSE_MAP+i*2+2]=(flags|existing[raw]).to_bytes(2,'big')
    assert count<=0x4c0
    assert BANK+count*32<=KOEI_BANK
    rom[0x3747c:0x3747e]=count.to_bytes(2,'big')
    assert src[0x37cbc:0x37cc0]==address.to_bytes(4,'big')
    rom[0x37cbc:0x37cc0]=LICENSE_MAP.to_bytes(4,'big')
