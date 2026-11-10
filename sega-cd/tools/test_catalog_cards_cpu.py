"""Check all card names against the actual native cyclic VRAM allocator."""
from pathlib import Path
import json, struct, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from catalog_list import card_map, CARD_COLUMNS
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
from unicorn.m68k_const import *

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'build/manifest.json').read_text('utf8'))
inventory=json.loads((root/'analysis/disc-inventory.json').read_text('utf8'))
files={f['path']:f for f in inventory['files']}
image=(root/'build/genchou-hishi-ru-experimental.iso').read_bytes()
def payload(name):
    f=files[name];return image[f['lba']*2048:f['lba']*2048+f['size']]
main=payload('SMAIN.PRG;1');init=payload('INIT.PRG;1')
meta=manifest['text_compositor']['catalog_list']
assert main[meta['card_frame']:meta['card_frame']+144]==card_map(16)
assert 10+meta['card_width']<=30  # inside outer frame, not across the stats
assert struct.unpack_from('>H',init,0x2c54)[0]==15
assert struct.unpack_from('>H',init,0x2db0)[0]==16

u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN)
u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
u.mem_map(0,0x100000);u.mem_write(0xc000,main)
def word(address):return struct.unpack('>H',bytes(u.mem_read(address,2)))[0]
def call(address,*args):
    sp=0xf0000;stop=0xe0000
    u.mem_write(sp,struct.pack('>'+'I'*(1+len(args)),stop,*args))
    u.reg_write(UC_M68K_REG_A7,sp)
    u.emu_start(address,stop,count=1000)
    assert u.reg_read(UC_M68K_REG_A7)==sp+4
def cstring(address):
    data,base=(init,0x66000) if address>=0x66000 else (main,0xc000)
    start=address-base;end=data.index(0,start)
    return data[start:end]
names=[init[0x15232+i*20:0x15232+(i+1)*20].split(b'\0')[0] for i in range(342)]
for table,count in [(0x16cea,27),(0x16dc2,84)]:
    names.extend(cstring(struct.unpack_from('>I',init,table+4*i)[0]) for i in range(count))
assert len(names)==453

def check(raw):
    # All glyphs are treated as dynamic, including ASCII: this upper bound
    # also covers a future sixteen-cell all-Cyrillic header.
    cells=0;chunks=[];i=0
    while i<len(raw):
        if raw[i]>=0x80:
            assert i+1<len(raw)
            width=1 if raw[i]==0xfc else 2;i+=2
        else:width=1;i+=1
        chunks.append(width*2);cells+=width
    assert cells<=CARD_COLUMNS,(cells,raw.hex())
    u.mem_write(0x5c6b2,struct.pack('>H',0x400))
    call(0x106e2,0,15)
    used=set()
    for count in chunks:
        first=word(0x5a11e);tiles=set(range(first,first+count))
        assert not tiles & used and max(tiles)<0x420
        used|=tiles;call(0x107aa,count)
    call(0x106e2,16,0xaf)
    assert word(0x5a11e)==0x420 and min(used)<word(0x5a11e)
    return cells
maximum=max(check(raw) for raw in names)
check(bytes.fromhex('f040')*8)
print(f'PASS: 453 full card names (max {maximum} cells), 16-cell stress case, native VRAM allocation without wrap/overlap, frame fits')
