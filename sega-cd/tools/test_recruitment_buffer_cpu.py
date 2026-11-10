"""Regression: AI recruitment must not overwrite its frame with Russian text."""
from pathlib import Path
import json,struct,sys
from unicorn import *
from unicorn.m68k_const import *
r=Path(__file__).resolve().parents[1];inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));f=next(x for x in inv['files'] if x['path']=='SMAIN.PRG;1');im=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();main=im[f['lba']*2048:][:f['size']]
for kind in range(4):
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,main);u.reg_write(UC_M68K_REG_SR,0x2700)
 u.mem_write(0x7fd48,struct.pack('>I',0x80000));u.mem_write(0x8000e,b'\xff\xff');u.mem_write(0x7fd20,b'\x05')
 saved={UC_M68K_REG_A6:0x87654,UC_M68K_REG_A2:0x81234,UC_M68K_REG_A3:0x82346,UC_M68K_REG_A4:0x83456,UC_M68K_REG_A5:0x84568}
 for k,v in saved.items():u.reg_write(k,v)
 stack=struct.pack('>4I',0x81000,kind,0,0x10)+b'GUARD123';u.mem_write(0x90000,stack);u.reg_write(UC_M68K_REG_A7,0x90000);reports=[]
 def hook(uc,pc,size,data):
  values={0x10004:0,0x1929c:1,0x13a0a:0,0x11d00:0,0x11d74:0,0x11dd6:0,0x16ef0:1,0x19412:0}
  if pc not in values:return
  sp=uc.reg_read(UC_M68K_REG_A7)
  def arg(n):return int.from_bytes(uc.mem_read(sp+4+4*n,4),'big')
  if pc==0x1929c:
   uc.mem_write(arg(0),b'\x07');uc.mem_write(arg(1),b'\x01');uc.mem_write(arg(2),b'\xff\xff')
  if pc==0x19412:
   raw=bytes(uc.mem_read(arg(0),128)).split(b'\0')[0];reports.append(raw);assert len(raw)<124
  uc.reg_write(UC_M68K_REG_D0,values[pc]);uc.reg_write(UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(UC_M68K_REG_A7,sp+4)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x2b18c,0x81000,count=200000)
 assert u.reg_read(UC_M68K_REG_PC)==0x81000
 assert bytes(u.mem_read(0x90000,len(stack)))==stack
 assert all(u.reg_read(k)==v for k,v in saved.items())
 assert len(reports)==1
 print('PASS recruitment',kind,'bytes',len(reports[0]))
