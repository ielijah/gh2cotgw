"""Pack the localized raster logo into an extended copy of the intro tile bank."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAP=0xce9f0
TILES=0xcf962
BANK=0x118000
ORIGINAL_COUNT=0x3e3
FIRST_TILE=0x200+ORIGINAL_COUNT
WIDTH,HEIGHT=192,88

def artwork():
    data=(ROOT/'assets/title-logo-indexed.bin').read_bytes()
    assert len(data)==WIDTH*HEIGHT and max(data)<15
    return [list(data[y*WIDTH:(y+1)*WIDTH]) for y in range(HEIGHT)]

def apply(rom,src):
    px=artwork();encoded={};indices=[]
    # Preserve every original intro tile, including tiles shared with other scenes.
    end=BANK+ORIGINAL_COUNT*32
    # Include the already localized subtitle from the working ROM.
    rom[BANK:end]=rom[TILES:TILES+ORIGINAL_COUNT*32]
    for ty in range(11):
        for tx in range(24):
            raw=bytes((px[ty*8+y][tx*8+x]<<4)|px[ty*8+y][tx*8+x+1] for y in range(8) for x in range(0,8,2))
            if raw not in encoded:
                tile=FIRST_TILE+len(encoded)
                assert tile<0x6c0,'Title graphics would reach the horizontal-scroll table in VRAM'
                encoded[raw]=tile
                address=BANK+(tile-0x200)*32
                assert address+32<=len(rom)
                rom[address:address+32]=raw
            indices.append(encoded[raw])
    for i,tile in enumerate(indices):rom[MAP+i*2:MAP+i*2+2]=(0xa000|tile).to_bytes(2,'big')
    assert src[0x3747c:0x3747e]==ORIGINAL_COUNT.to_bytes(2,'big')
    assert src[0x37484:0x37488]==TILES.to_bytes(4,'big')
    rom[0x3747c:0x3747e]=(ORIGINAL_COUNT+len(encoded)).to_bytes(2,'big')
    rom[0x37484:0x37488]=BANK.to_bytes(4,'big')
    return len(encoded)
