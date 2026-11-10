"""Exercise native resource-report assembly: long Cyrillic must not overwrite stack."""
from pathlib import Path
import json,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import *
from single_letters import code
r=Path(__file__).resolve().parents[1]
v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'))
f=next(x for x in v['files'] if x['path']=='SMAIN.PRG;1')
im=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes()
main=im[f['lba']*2048:f['lba']*2048+f['size']]
def text(s): return b''.join(c.encode() if c.isascii() else code(c) for c in s)
count=0
for fn in (0x19160,0x19242):
 for prefix in ('Золото ', 'Продовольствие ', 'Военное снаряжение '):
  for amount in (0,999,65535):
   u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
   u.mem_map(0,0x100000);u.mem_write(0xc000,main)
   u.reg_write(UC_M68K_REG_SR,0x2700)
   saved={UC_M68K_REG_A2:0x81234,UC_M68K_REG_A3:0x82346,UC_M68K_REG_A6:0x83456}
   for reg,val in saved.items():u.reg_write(reg,val)
   u.mem_write(0x80000,text(prefix)+b'\0')
   args=[amount,0x80000,10] if fn==0x19160 else [0x80000]
   stack=struct.pack('>'+str(1+len(args))+'I',0x81000,*args)+b'GUARD123'
   u.mem_write(0x90000,stack);u.reg_write(UC_M68K_REG_A7,0x90000);reports=[]
   def hook(uc,pc,size,data):
    if pc not in (0x19412,0x16dda):return
    sp=uc.reg_read(UC_M68K_REG_A7);dest=int.from_bytes(uc.mem_read(sp+4,4),'big')
    if pc==0x16dda:
     old=bytes(uc.mem_read(dest,128)).split(b'\0')[0]
     uc.mem_write(dest,old+text('Чингисхан')+b'\0')
    else: reports.append(bytes(uc.mem_read(dest,128)).split(b'\0')[0])
    uc.reg_write(UC_M68K_REG_D0,0)
    uc.reg_write(UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(UC_M68K_REG_A7,sp+4)
   u.hook_add(UC_HOOK_CODE,hook);u.emu_start(fn,0x81000,count=100000)
   assert u.reg_read(UC_M68K_REG_PC)==0x81000
   assert u.reg_read(UC_M68K_REG_A7)==0x90004
   assert bytes(u.mem_read(0x90000,len(stack)))==stack
   assert all(u.reg_read(reg)==val for reg,val in saved.items())
   assert len(reports)==1 and 20<len(reports[0])<126
   count+=1
print(f'PASS: {count} native resource reports; return address, arguments, guard, saved registers and stack intact')
