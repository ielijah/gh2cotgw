"""Localized blinking title prompt, with the original START pixels intact."""
from title_logo import BANK,TILES
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
WIDTH=144
START_X=96
MAP=0x117400

def original_pixels(src):
    px=[[0]*96 for _ in range(16)]
    for i in range(24):
        entry=int.from_bytes(src[0xcecc0+i*2:0xcecc2+i*2],'big')
        address=TILES+((entry&2047)-0x200)*32
        for y in range(8):
            for x in range(8):
                b=src[address+y*4+x//2]
                px[i//12*8+y][i%12*8+x]=(b>>(4 if x%2==0 else 0))&15
    return px

def artwork(src,font):
    px=[[0]*WIDTH for _ in range(16)]
    shapes=json.loads((ROOT/'translation/title-prompt-font.json').read_text(encoding='utf-8'))
    ink=[];left=4
    for ch in 'НАЖМИТЕ':
        if ch=='Е':left-=3  # Tighten the wide side bearing after the original T.
        rows=shapes[ch]
        for y,row in enumerate(rows):
            for x,bit in enumerate(row):
                if bit=='1':ink.append((left+x,y))
        left+=len(rows[0])+1
    for x,y in ink:
        if y+1<16:
            px[y+1][x-1]=3;px[y+1][x+1]=4
    for x,y in ink:px[y][x]=14
    old=original_pixels(src)
    for y in range(16):px[y][START_X:WIDTH]=old[y][48:96]
    return px

def apply(rom,src,font):
    px=artwork(src,font)
    count=int.from_bytes(rom[0x3747c:0x3747e],'big')
    first=0x200+count
    for i in range(36):
        tile=first+i;assert tile<0x700
        raw=bytes((px[i//18*8+y][i%18*8+x]<<4)|px[i//18*8+y][i%18*8+x+1] for y in range(8) for x in range(0,8,2))
        address=BANK+(tile-0x200)*32
        rom[address:address+32]=raw
        rom[MAP+i*2:MAP+i*2+2]=(0xe000|tile).to_bytes(2,'big')
    rom[0x3747c:0x3747e]=(count+36).to_bytes(2,'big')
    for address in (0x3852c,0x3858e):
        assert src[address:address+4]==bytes.fromhex('000cecc0')
        rom[address:address+4]=MAP.to_bytes(4,'big')
    for address in (0x38536,0x3856a,0x38598):
        assert src[address:address+2]==b'\x00\x0c'
        rom[address:address+2]=b'\x00\x12'
    for address in (0x3853e,0x38572,0x385a0):
        assert src[address:address+2]==b'\x00\x0a'
        rom[address:address+2]=b'\x00\x07'
