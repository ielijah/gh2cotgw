"""Execute selector and option toggle machine code, including native special IDs."""
from pathlib import Path
import json,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import *
from harem_cards import code,groups,LOAD,HELPER,ROOT
regs=[UC_M68K_REG_D0,UC_M68K_REG_D1,UC_M68K_REG_D2,UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_D6,UC_M68K_REG_D7,UC_M68K_REG_A0,UC_M68K_REG_A1,UC_M68K_REG_A2,UC_M68K_REG_A3,UC_M68K_REG_A4,UC_M68K_REG_A5,UC_M68K_REG_A6]
cases=0
for culture,(count,base) in enumerate(groups()):
 for original in range(11):
  for disabled in (False,True):
   for chosen in range(count+1):
    u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000)
    u.reg_write(UC_M68K_REG_SR,0x2700);u.mem_write(LOAD+HELPER,code());u.mem_write(0x5ef7c,struct.pack('>I',0x80000));u.mem_write(0x80010,bytes([(culture<<2)|0xe3]))
    u.mem_write(0x7fd58,bytes([0xbf|(0x40 if disabled else 0)]))
    u.reg_write(UC_M68K_REG_A7,0x90000);u.mem_write(0x90000,struct.pack('>II',0x81000,original))
    for n,reg in enumerate(regs):u.reg_write(reg,0x12340000+n)
    calls=[]
    def hook(uc,pc,size,data):
     if pc not in (0x11dd6,0x154a6,0x15706,0xc0f4):return
     sp=uc.reg_read(UC_M68K_REG_A7);args=bytes(uc.mem_read(sp+4,16));calls.append(pc)
     if pc==0x11dd6:
      assert int.from_bytes(args[:4],'big')==count+1;uc.reg_write(UC_M68K_REG_D0,chosen)
     elif pc==0x154a6:
      ptr,sectors,sector,dest=struct.unpack('>4I',args)
      assert bytes(uc.mem_read(ptr,12))==b'G2HAREM.DAT\0'
      assert (sectors,sector,dest)==(4,(base+chosen)*4,0x90000),(culture,chosen,sector)
     elif pc==0xc0f4:assert struct.unpack('>7I',bytes(uc.mem_read(sp+4,28)))==(26,1,10,5,10,20,0)
     else:assert int.from_bytes(args[:4],'big')==original
     ret=int.from_bytes(uc.mem_read(sp,4),'big');uc.reg_write(UC_M68K_REG_A7,sp+4);uc.reg_write(UC_M68K_REG_PC,ret)
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(LOAD+HELPER,0x81000,count=1000)
    assert calls==([0x15706] if disabled else [0x11dd6,0x15706] if chosen==count else [0x11dd6,0x154a6,0xc0f4])
    assert u.reg_read(UC_M68K_REG_A7)==0x90004
    assert all(u.reg_read(reg)==0x12340000+n for n,reg in enumerate(regs))
    assert bytes(u.mem_read(0x7fd58,1))==bytes([0xbf|(0x40 if disabled else 0)])
    cases+=1
print(f'PASS: {cases} 68000 selector cases; every culture, original slot, generated choice, toggle, preserved registers and stack')

inv=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'));manifest=json.loads((ROOT/'build/manifest.json').read_text('utf8'))
f=next(f for f in inv['files'] if f['path']=='SMAIN.PRG;1');image=(ROOT/'build/genchou-hishi-ru-experimental.iso').read_bytes();main=image[f['lba']*2048:][:f['size']]
for initial in range(256):
 for accept in (False,True):
  u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,main);u.reg_write(UC_M68K_REG_SR,0x2700)
  u.mem_write(0x7fd58,bytes([initial]));u.reg_write(UC_M68K_REG_A7,0x90000);u.mem_write(0x90000,struct.pack('>I',0x81000))
  def toggle(uc,pc,size,data):
   if pc!=0x31d16:return
   sp=uc.reg_read(UC_M68K_REG_A7)
   assert int.from_bytes(uc.mem_read(sp+4,4),'big')==0x40
   assert bytes(uc.mem_read(0x7fd58,1))==bytes([initial^0x40])
   if accept:uc.mem_write(0x7fd58,bytes([initial]))
   uc.reg_write(UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(UC_M68K_REG_A7,sp+4)
  u.hook_add(UC_HOOK_CODE,toggle);u.emu_start(0xc000+manifest['text_compositor']['harem_options']['handler'],0x81000,count=500)
  assert bytes(u.mem_read(0x7fd58,1))==bytes([initial^(0x40 if accept else 0)])
  assert u.reg_read(UC_M68K_REG_A7)==0x90004 and u.reg_read(UC_M68K_REG_D0)==0
print('PASS: 512 option confirmation/cancellation cases; all unrelated setting bits preserved')
