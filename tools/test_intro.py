"""Check real intro pixels: repaired descenders, connected strokes, alignment."""
from pathlib import Path
import subprocess,sys,shutil,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from find_title import read_png
from import_font import extract
from graphics_codec import decode
from intro_captions import KOEI_BANK,LICENSE_MAP,lettering
ROOT=Path(__file__).resolve().parents[1]
rom=(ROOT/'build/genghis2-ru-experimental.gen').read_bytes()
src=(ROOT/'rom/original.gen').read_bytes()
original,_=decode(src[int.from_bytes(src[0x6146a:0x6146e],'big'):])
new,_=decode(rom[KOEI_BANK:])
assert new[:len(original)]==original,'Original publisher logo tiles changed'
assert int.from_bytes(rom[0x37cbc:0x37cc0],'big')==LICENSE_MAP
font=extract(next((ROOT/'rom/reference').glob('*.md')).read_bytes(),1)
frames={}
for n in (600,850,1150,1800,2900,6100,9000):
    subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(ROOT/'build/genghis2-ru-experimental.gen'),str(n)],check=True,capture_output=True)
    path=ROOT/f'analysis/intro-057-{n}.png'
    shutil.copyfile(ROOT/'analysis/screen-genghis2-ru-experimental.png',path)
    w,h,rgb=read_png(path);assert (w,h)==(256,224)
    frames[n]=rgb
expected=lettering('ПО ЛИЦЕНЗИИ SEGA ENTERPRISES, LTD.',224,16)
for y in range(16):
    for x in range(224):
        offset=((168+y)*256+16+x)*3
        assert bool(any(frames[9000][offset:offset+3]))==bool(expected[y][x]),('License pixels corrupted',x,y)
def glyph(frame,x,y):
    rgb=frames[frame]
    return bytes(sum(128>>dx for dx in range(8) if any(rgb[((y+dy)*256+x+dx)*3:((y+dy)*256+x+dx)*3+3])) for dy in range(16))
assert glyph(2900,88,96)==font['р'],'Descender clipped'
assert glyph(2900,104,96)==font['д'],'Descender clipped'
assert glyph(1800,112,96)==font['ю'],'Broken yu stroke'
assert glyph(6100,144,24)==font['ы']
assert glyph(6100,128,48)==font['ы']
assert glyph(6100,152,24)==font['м']
assert glyph(6100,136,48)==font['м']
for y in (24,48,72):
    assert any(glyph(6100,80,y)), 'Missing aligned first letter'
    assert not any(glyph(6100,72,y)), 'Unexpected leading pixels'
(ROOT/'analysis/intro-test.json').write_text(json.dumps({'frames':list(frames),'full_descenders':True,'repaired_strokes':True,'aligned_column':80,'publisher_original_tiles_preserved':True},indent=2))
print('PASS: intro descenders, yi/yu strokes, aligned column, publisher originals')
