from pathlib import Path
import json,sys,struct
sys.path.insert(0,'tools')
from unicorn import *
from unicorn.m68k_const import *
r=Path.cwd();v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));f=next(x for x in v['files'] if x['path']=='SMAIN.PRG;1');m=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes()[f['lba']*2048:][:f['size']]
for n in range(33):
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,m);u.reg_write(UC_M68K_REG_SR,0x2700);u.mem_write(0x7fd48,struct.pack('>I',0x7eb14+52*n));u.mem_write(0x90000,struct.pack('>I',0x81000));u.reg_write(UC_M68K_REG_A7,0x90000);seen=[]
 def hook(uc,pc,size,data):
  if pc not in [0x105ac,0x10600,0x106e2,0x1047c,0x11034]:return
  sp=uc.reg_read(UC_M68K_REG_A7)
  if pc==0x11034:seen.append(struct.unpack('>II',uc.mem_read(sp+4,8)))
  uc.reg_write(UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(UC_M68K_REG_A7,sp+4)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x16600,0x81000,count=10000);assert seen==[(0x32840,n+1)],seen
print('PASS: native indicator prints province number 1..33, independent of character stats')
