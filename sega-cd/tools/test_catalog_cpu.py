"""Execute the catalogue list wrapper for every translated record on a 68000."""
from pathlib import Path
import json,struct,sys
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import *
r=Path(__file__).resolve().parents[1];m=json.loads((r/'build/manifest.json').read_text('utf8'));inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));iso=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();files={f['path']:f for f in inv['files']}
def payload(name):
 f=files[name];return iso[f['lba']*2048:f['lba']*2048+f['size']]
main=payload('SMAIN.PRG;1');init=payload('INIT.PRG;1');base=0xc000;helper=base+m['text_compositor']['catalog_list']['helper'];truncated=0
for i in range(342):
 ptr=0x66000+0x15232+i*20;raw=init[0x15232+i*20:0x15232+(i+1)*20].split(b'\0')[0]
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(base,main);u.mem_write(0x66000,init)
 sp=0xf0000;stop=0xe0000;fmt=0xd0000;u.mem_write(fmt,b'%s\0');u.mem_write(sp,struct.pack('>III',stop,fmt,ptr));u.reg_write(UC_M68K_REG_A7,sp)
 regs=[UC_M68K_REG_D0,UC_M68K_REG_D1,UC_M68K_REG_A0,UC_M68K_REG_A1]
 for j,reg in enumerate(regs):u.reg_write(reg,0x12300+j)
 seen=[]
 def hook(uc,pc,size,data):
  if pc==0x11034:
   stack=uc.reg_read(UC_M68K_REG_A7);ret,actualfmt,p=struct.unpack('>III',bytes(uc.mem_read(stack,12)));out=bytes(uc.mem_read(p,16)).split(b'\0')[0];seen.append(out);assert actualfmt==fmt
   uc.reg_write(UC_M68K_REG_A7,stack+4);uc.reg_write(UC_M68K_REG_PC,ret)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(helper,stop,count=1000)
 assert seen==[raw if len(raw)<=10 else raw[:8]+b'..'],(i,raw,seen)
 assert u.reg_read(UC_M68K_REG_A7)==sp+4
 assert all(u.reg_read(reg)==0x12300+j for j,reg in enumerate(regs))
 assert bytes(u.mem_read(ptr,16))==init[ptr-0x66000:ptr-0x66000+16]
 truncated+=len(raw)>10
print(f'PASS: all 342 catalogue names execute within ten list columns; {truncated} long names marked with two dots, full records and stack preserved')
