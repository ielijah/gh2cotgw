"""Render the localized battle resources directly from the built ROM."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from graphics_codec import decode
from emulate import png

ROOT = Path(__file__).resolve().parents[1]
rom = (ROOT / 'build/genghis2-ru-experimental.gen').read_bytes()
groups = [(0xc4,0xc5,0xc6,0xc7), (0xc8,0xc9,0xca),
          (0xcb,0xcc,0xcd,0xce,0xcf), (0xd0,0xd3,0xd4,0xfa),
          (0xd7,0xd8,0xd9,0xda,0xdb), (0xf7,0xf9),
          (0xe8,0xe9,0xea,0xeb,0xec)]
scale = 4
w, h = 192, len(groups)*24+8
pixels = bytearray(bytes((32,32,32))*w*h)
palette = {9:(132,65,65), 14:(238,238,238), 15:(0,0,0)}
for row, group in enumerate(groups):
    for col, resource in enumerate(group):
        ptr = 0xa663c+resource*4
        raw, _ = decode(rom[int.from_bytes(rom[ptr:ptr+4], 'big'):])
        tiles = len(raw)//64
        for y in range(16):
            for x in range(tiles*8):
                value = raw[(y//8*tiles+x//8)*32+y%8*4+x%8//2]
                index = (value >> (4 if x%2==0 else 0)) & 15
                offset = ((row*24+4+y)*w+col*36+4+x)*3
                pixels[offset:offset+3] = bytes(palette.get(index,(80,80,80)))
large = bytearray()
for y in range(h):
    line = b''.join(pixels[(y*w+x)*3:(y*w+x)*3+3]*scale for x in range(w))
    large.extend(line*scale)
png(ROOT/'analysis/battle-042-preview.png',w*scale,h*scale,large)
