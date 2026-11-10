from pathlib import Path
import struct,collections
from unicorn import *
from unicorn.m68k_const import *
from capstone import *
s=Path('analysis/qa-first-turn/pre-crash.state').read_bytes();b=Path('analysis/qa-first-turn/pre-prg.bin').read_bytes()
u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x1000000);u.mem_write(0,b);u.reg_write(UC_M68K_REG_SR,0x2000)
regs=[UC_M68K_REG_D0,UC_M68K_REG_D1,UC_M68K_REG_D2,UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_D6,UC_M68K_REG_D7,UC_M68K_REG_A0,UC_M68K_REG_A1,UC_M68K_REG_A2,UC_M68K_REG_A3,UC_M68K_REG_A4,UC_M68K_REG_A5,UC_M68K_REG_A6,UC_M68K_REG_A7]
for n,reg in enumerate(regs):u.reg_write(reg,struct.unpack_from('<I',s,1016072+n*4)[0])
cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000);hist=collections.deque(maxlen=40)
def hook(u,pc,size,data):
 hist.append((pc,u.reg_read(UC_M68K_REG_A7),u.reg_read(UC_M68K_REG_A6)))
 if pc in (0xe7ac,0xc0f4):
  sp=u.reg_read(UC_M68K_REG_A7);u.reg_write(UC_M68K_REG_PC,int.from_bytes(u.mem_read(sp,4),'big'));u.reg_write(UC_M68K_REG_A7,sp+4)
 if pc==0x6196 or pc==0x619a: u.emu_stop()
u.hook_add(UC_HOOK_CODE,hook)
def wr(u,access,address,size,value,data):
 if address == 0xaf5c and size==1 and value>=0x80:
  print('TEXT WRITE',hex(u.reg_read(UC_M68K_REG_PC)),hex(address),size,hex(value));u.emu_stop()
u.hook_add(UC_HOOK_MEM_WRITE,wr)
try:u.emu_start(struct.unpack_from('<I',s,1016136)[0],0,count=500000)
except UcError as e:print(e)
for pc,sp,fp in hist:
 raw=bytes(u.mem_read(pc,12)) if pc<0xfffff0 else b''
 i=next(cs.disasm(raw,pc),None);print(hex(pc),hex(sp),hex(fp),i.mnemonic+' '+i.op_str if i else '')
