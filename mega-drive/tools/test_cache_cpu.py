"""Execute the actual invalidation instructions on the emulated 68000.

An isolated test ROM returns before the original upload trampoline, allowing
tag invalidation to be tested without game/VDP initialization side effects.
"""
from pathlib import Path
import sys,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
DIAGNOSTICS=ROOT/'build/diagnostics';DIAGNOSTICS.mkdir(exist_ok=True)
rom=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
original=bytes.fromhex('4cdf01032f02242f00104ef900003e64')
pos=rom.find(original,0x100800,0x100900);assert pos>=0
rom[pos:pos+len(original)]=bytes.fromhex('4cdf01034e75')+bytes.fromhex('4e71')*((len(original)-6)//2)
code=bytearray.fromhex('46fc2700')
cases=[(0x200,2,'00002222'),(0x201,2,'00000000'),(0x201,1,'00002222'),(0x200,0,'11112222'),(0x200,3,'00000000')]
for i,(destination,count,expected) in enumerate(cases):
    code.extend(bytes.fromhex('33fc111100ffd20033fc222200ffd202'))
    code.extend(bytes.fromhex('4878')+struct.pack('>H',count))
    code.extend(bytes.fromhex('4878')+struct.pack('>H',destination))
    code.extend(bytes.fromhex('42a74eb9001008004fef000c23f900ffd200')+struct.pack('>I',0xffd900+i*4))
code.extend(bytes.fromhex('60fe'))
rom[4:8]=struct.pack('>I',0x102800);rom[0x102800:0x102800+len(code)]=code
dest=DIAGNOSTICS/'cache-invalidation-test.gen';dest.write_bytes(rom)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(dest),'2'],cwd=ROOT,check=True,capture_output=True)
ram=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());ram[::2],ram[1::2]=ram[1::2],ram[::2]
for i,(destination,count,expected) in enumerate(cases):
    got=ram[0xd900+i*4:0xd904+i*4].hex()
    assert got==expected,(hex(destination),count,expected,got)
print('PASS: native 68000 invalidation, even/odd destinations, zero/one/two/three-tile uploads')

# Cached hits execute the complete original function frame and return path,
# including case-sensitive lookup and tilemap palette construction.
rom=bytearray((ROOT/'build/genghis2-ru-experimental.gen').read_bytes())
code=bytearray.fromhex('46fc2700')
def permanent(glyph):
    address=0x105b00+(glyph-0xc0)*4 if glyph>=0xc0 else 0x105800+glyph*4
    top,bottom=struct.unpack('>HH',rom[address:address+4])
    return struct.pack('>HHH',top|0x4000,bottom|0x4000,0x202).hex()
glyph_cases=[(g,0,14,0,0,permanent(g)) for g in (0xc0,0xe0,0x100,0x101,ord('A')-32,ord('a')-32)]
glyph_cases += [(0xc0,1,14,0,0xf001,'020002010202'),(0xff,1,0,1,0x80c0,'020002010202'),(0xff,1,0,0,0x8040,'020002010202')]
def word(value,address): return bytes.fromhex('33fc')+struct.pack('>H',value)+struct.pack('>I',address)
def byte(value,address): return bytes.fromhex('13fc')+struct.pack('>H',value)+struct.pack('>I',address)
for i,(glyph,mode,fg,bg,key,expected) in enumerate(glyph_cases):
    code.extend(word(0x200,0xff57f0)+word(0x203,0xff3004)+word(0x202,0xff3252))
    code.extend(word(key,0xffd200)+word(0,0xffd202))
    code.extend(byte(mode,0xff7d13)+byte(fg,0xff5978)+byte(bg,0xff2d6e)+byte(2,0xff5804))
    output=0xffda00+i*8
    code.extend(bytes.fromhex('2f3c')+struct.pack('>I',output)+bytes.fromhex('4878')+struct.pack('>H',glyph))
    code.extend(bytes.fromhex('4eb900005cf8508f33f900ff3252')+struct.pack('>I',output+4))
code.extend(bytes.fromhex('60fe'));assert len(code)<0x800
rom[4:8]=struct.pack('>I',0x102800);rom[0x102800:0x102800+len(code)]=code
dest=DIAGNOSTICS/'cache-glyph-test.gen';dest.write_bytes(rom)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(dest),'2'],cwd=ROOT,check=True,capture_output=True)
ram=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());ram[::2],ram[1::2]=ram[1::2],ram[::2]
for i,(glyph,mode,fg,bg,key,expected) in enumerate(glyph_cases):
    got=ram[0xda00+i*8:0xda06+i*8].hex()
    assert got==expected,(hex(glyph),mode,hex(key),expected,got)
print('PASS: native 68000 permanent/cached glyphs, Cyrillic case and Yo, Latin grades, palettes, dynamic colours, stable allocation cursor')
