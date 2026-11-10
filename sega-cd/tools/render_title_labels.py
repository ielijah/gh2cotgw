"""Native pixel glyphs for the title subtitle and START-compatible prompt."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from emulate import png
ROOT=Path(__file__).resolve().parents[1]

# Thirteen-pixel capitals, two-pixel stems and slab serifs like native START.
PROMPT={
'Н':['###..###','.##..##.','.##..##.','.##..##.','.##..##.','.##..##.','.######.','.##..##.','.##..##.','.##..##.','.##..##.','.##..##.','###..###'],
'А':['....##..','....##..','....##..','...#.##.','...#.##.','...#.##.','...#.##.','...####.','..#...##','..#...##','..#...##','..#...##','.###.###'],
'Ж':['###.##.###','.##.##.##.','..#.##.#..','..#.##.#..','...####...','...####...','....##....','...####...','..#.##.#..','..#.##.#..','.##.##.##.','.##.##.##.','###.##.###'],
'М':['###....###','.##....##.','.###..###.','.###..###.','.##.##.##.','.##.##.##.','.##.##.##.','.##....##.','.##....##.','.##....##.','.##....##.','.##....##.','###....###'],
'И':['###..###','.##..##.','.##..##.','.##.###.','.##.###.','.######.','.#####..','.#####..','.###.##.','.###.##.','.##..##.','.##..##.','###..###'],
}
def render():
    prompt=bytearray(144*16)
    original=(ROOT/'assets/title-start-original-pixels.bin').read_bytes()
    colors=[next((v for v in original[y*40:y*40+40] if v),0) for y in range(16)]
    widths=[len(PROMPT[c][0]) for c in 'НАЖМИ']
    x=(144-(sum(widths)+4+7+40))//2
    for c in 'НАЖМИ':
        for y,row in enumerate(PROMPT[c]):
            for dx,p in enumerate(row):
                if p=='#':prompt[y*144+x+dx]=colors[y]
        x+=len(PROMPT[c][0])+1
    x+=6
    for y in range(16):prompt[y*144+x:y*144+x+40]=original[y*40:y*40+40]
    (ROOT/'assets/title-prompt-russian-pixels.bin').write_bytes(prompt)
    title=bytearray((ROOT/'assets/title-russian-pixels.bin').read_bytes())
    (ROOT/'assets/title-russian-pixels.bin').write_bytes(title)
    palette={0:(0,0,0),1:(224,208,0),2:(103,103,0),3:(48,0,208),4:(239,239,239),13:(0,66,158),14:(0,128,192)}
    for name,p,w,h in [('title-russian-preview',title,192,88),('title-prompt-russian-preview',prompt,144,16)]:
        scale=4
        rgb=bytes(v for y in range(h*scale) for x in range(w*scale) for v in palette[p[(y//scale)*w+x//scale]])
        png(ROOT/'analysis'/f'{name}.png',w*scale,h*scale,rgb)

if __name__=='__main__':render()
