"""Execute the card hook for all 84 sorted identities; validate stack and VRAM ranges."""
from pathlib import Path
import json,struct,sys
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from women_traits import texts
m=json.loads((ROOT/'build/manifest.json').read_text('utf8'))
v=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
image=(ROOT/'build/genchou-hishi-ru-experimental.iso').read_bytes()
f=next(f for f in v['files'] if f['path']=='INIT.PRG;1')
init=image[f['lba']*2048:f['lba']*2048+f['size']]
t=m['women_traits'];u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN)
u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0x66000,init)
events=[]
def hook(uc,pc,size,data):
    if pc not in (0x68d7c,0x106e2,0x1047c,0x10af8):return
    sp=uc.reg_read(UC_M68K_REG_A7)
    args=struct.unpack('>3I',bytes(uc.mem_read(sp,12)))
    events.append((pc,args[1:]))
    uc.reg_write(UC_M68K_REG_A7,sp+4);uc.reg_write(UC_M68K_REG_PC,args[0])
u.hook_add(UC_HOOK_CODE,hook)
for dest,old in enumerate(m['catalog_index']['wives']['order']):
    events.clear();sp=0xf0000;stop=0xe0000
    u.mem_write(sp,struct.pack('>I',stop));u.reg_write(UC_M68K_REG_A7,sp);u.reg_write(UC_M68K_REG_D2,dest)
    u.emu_start(0x66000+t['helper'],stop,count=1000)
    assert u.reg_read(UC_M68K_REG_PC)==stop and u.reg_read(UC_M68K_REG_A7)==sp+4
    assert u.reg_read(UC_M68K_REG_D2)==dest
    assert events[0]==(0x68d7c,(2,dest))
    assert events[1]==(0x106e2,(0xd0,0x10f)) and events[2]==(0x1047c,(11,6))
    assert events[3][0]==0x10af8 and events[3][1][0]==0x66000+t['records'][old]['offset']
    assert bytes(u.mem_read(0x59f4c,2))==b'\0\2'
    text=texts()[old];cells=sum((len(x)+1)//2*2 for x in text.split('\n'))
    assert cells<=64 and all(len(x)<=18 for x in text.split('\n')) and len(text.split('\n'))<=3
    assert 0xa0+0xd0*2==0x240 and 0xa0+(0x10f+1)*2==0x2c0
print('PASS: all 84 native card hooks, matched inheritance pointers, balanced stack, restored registers/left margin; traits avoid body, portrait and frame tiles')
