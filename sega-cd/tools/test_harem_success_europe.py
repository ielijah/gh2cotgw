"""Run the actual card-selector code for every culture, original slot and RNG result."""
from pathlib import Path
import sys,json,struct
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from harem_success_europe import code,LOAD,HELPER
regs=[UC_M68K_REG_D0,UC_M68K_REG_D1,UC_M68K_REG_D2,UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_D6,UC_M68K_REG_D7,UC_M68K_REG_A0,UC_M68K_REG_A1,UC_M68K_REG_A2,UC_M68K_REG_A3,UC_M68K_REG_A4,UC_M68K_REG_A5,UC_M68K_REG_A6]
cases=0
for culture in range(8):
 for original in range(11):
  for chosen in range(10):
   u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000)
   u.reg_write(UC_M68K_REG_SR,0x2700);u.mem_write(LOAD+HELPER,code());u.mem_write(0x5ef7c,struct.pack('>I',0x80000));u.mem_write(0x80010,bytes([(culture<<2)|0xe3]));u.reg_write(UC_M68K_REG_A7,0x90000);u.mem_write(0x90000,struct.pack('>II',0x81000,original))
   for n,reg in enumerate(regs):u.reg_write(reg,0x12340000+n)
   calls=[]
   def hook(uc,pc,size,data):
    if pc not in (0x11dd6,0x154a6,0x15706):return
    sp=uc.reg_read(UC_M68K_REG_A7);args=bytes(uc.mem_read(sp+4,16));calls.append(pc)
    if pc==0x11dd6:
     assert int.from_bytes(args[:4],'big')==10;uc.reg_write(UC_M68K_REG_D0,chosen)
    elif pc==0x154a6:
     ptr,count,sector,dest=struct.unpack('>4I',args)
     assert bytes(uc.mem_read(ptr,12))==b'G2HAREM.DAT\0';assert (count,sector,dest)==(4,chosen*4,0x90000)
    else:assert int.from_bytes(args[:4],'big')==original
    ret=int.from_bytes(uc.mem_read(sp,4),'big');uc.reg_write(UC_M68K_REG_A7,sp+4);uc.reg_write(UC_M68K_REG_PC,ret)
   u.hook_add(UC_HOOK_CODE,hook);u.emu_start(LOAD+HELPER,0x81000,count=1000)
   assert calls==([0x11dd6,0x154a6] if culture in (4,5) else [0x15706])
   assert u.reg_read(UC_M68K_REG_A7)==0x90004
   assert all(u.reg_read(reg)==0x12340000+n for n,reg in enumerate(regs))
   cases+=1
print(f'PASS: {cases} actual 68000 selector cases; cultures, all slots, all ten choices, stack and registers')


# Exercise the unmodified game RNG: it must yield valid sector indices.
r=Path(__file__).resolve().parents[1];inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'))
f=next(f for f in inv['files'] if f['path']=='SMAIN.PRG;1');image=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes()
u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000)
u.mem_write(0xc000,image[f['lba']*2048:][:f['size']]);u.reg_write(UC_M68K_REG_SR,0x2700);seen=set()
for _ in range(1000):
 u.reg_write(UC_M68K_REG_A7,0x90000);u.mem_write(0x90000,struct.pack('>II',0x81000,10));u.emu_start(0x11dd6,0x81000,count=10000)
 v=u.reg_read(UC_M68K_REG_D0);assert 0<=v<10;seen.add(v)
assert seen==set(range(10));print('PASS: native RNG reaches all ten cards and stays in range')
