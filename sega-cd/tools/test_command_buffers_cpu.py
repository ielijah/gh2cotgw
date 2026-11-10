from pathlib import Path
import json,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from unicorn import *
from unicorn.m68k_const import *
from text_encoding import encode
r=Path(__file__).resolve().parents[1];m=json.loads((r/'build/manifest.json').read_text('utf8'));v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));f=next(x for x in v['files'] if x['path']=='SMAIN.PRG;1');im=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();main=im[f['lba']*2048:][:f['size']];pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()};rev={v:k for k,v in pairs.items()}
def dec(b):
 out='';i=0
 while i<len(b):
  if b[i]>=0xf0:out+=rev.get(b[i:i+2],'?');i+=2
  else:out+=chr(b[i]);i+=1
 return out
cases=[(0x2acf0,0x2af54,UC_M68K_REG_A4,0x22,range(3)),(0x2b012,0x2b0f2,UC_M68K_REG_A2,0x1a,range(1)),(0x2b8d0,0x2b960,UC_M68K_REG_A3,0x18,range(3)),(0x2bb64,0x2bc5c,UC_M68K_REG_A4,0x24,range(1)),(0x2bcfe,0x2bdf0,UC_M68K_REG_A4,0x24,range(1)),(0x2c0d0,0x2c1b6,UC_M68K_REG_A2,0x28,range(1))]
# Derive the actual buffer displacement from the patched LEA, not hardcoded old sizes.
lea={0x2acf0:0x2acfe,0x2b012:0x2b01a,0x2b8d0:0x2b8dc,0x2bb64:0x2bb72,0x2bcfe:0x2bd0c,0x2c0d0:0x2c0dc}
reports=[]
for fn,start,reg,old,kinds in cases:
 for kind in kinds:
  u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,main);u.reg_write(UC_M68K_REG_SR,0x2700)
  saved={UC_M68K_REG_A6:0x87654,UC_M68K_REG_A2:0x81234,UC_M68K_REG_A3:0x82346,UC_M68K_REG_A4:0x83456,UC_M68K_REG_A5:0x84568}
  for k,val in saved.items():u.reg_write(k,val)
  stack=struct.pack('>I',0x81000)+b'GUARD123';u.mem_write(0x90000,stack);u.reg_write(UC_M68K_REG_A7,0x90000);u.emu_start(fn,fn+8,count=2)
  fp=u.reg_read(UC_M68K_REG_A6);disp=struct.unpack_from('>h',main,lea[fn]-0xc000+2)[0];dest=fp+disp
  u.reg_write(reg,dest);u.reg_write(UC_M68K_REG_D2,kind);u.reg_write(UC_M68K_REG_D6,kind);u.reg_write(UC_M68K_REG_D5,9999);u.reg_write(UC_M68K_REG_D3,9999)
  if reg!=UC_M68K_REG_A3:u.reg_write(UC_M68K_REG_A3,0x83000);u.mem_write(0x83000,struct.pack('>I',0x84000))
  seen=[]
  def hook(uc,pc,size,data):
   if pc not in (0x19412,0x16dda,0x11dd6):return
   sp=uc.reg_read(UC_M68K_REG_A7);d=int.from_bytes(uc.mem_read(sp+4,4),'big')
   if pc==0x19412:seen.append(bytes(uc.mem_read(d,180)).split(b'\0')[0])
   if pc==0x16dda:
    b=bytes(uc.mem_read(d,180)).split(b'\0')[0];uc.mem_write(d,b+b'33:'+encode('Река Онон Река',pairs)+b'\0')
   uc.reg_write(UC_M68K_REG_D0,0 if pc!=0x11dd6 else 5);uc.reg_write(UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(UC_M68K_REG_A7,sp+4)
  u.hook_add(UC_HOOK_CODE,hook)
  err=None
  try:u.emu_start(start,0x81000,count=100000)
  except UcError as e:err=str(e)
  intact=all(u.reg_read(k)==val for k,val in saved.items()) and bytes(u.mem_read(0x90000,len(stack)))==stack and u.reg_read(UC_M68K_REG_PC)==0x81000
  full=dec(seen[0])+dec(main[0x26fec:].split(b'\0')[0]) if seen else ''
  if '--strict' in sys.argv:assert len(full.splitlines())<=2 and max(map(len,full.splitlines()))<=22,full
  record=dict(raw_hex=seen[0].hex() if seen else None,full_text=full,function=hex(fn),kind=kind,bytes=len(seen[0]) if seen else None,text=dec(seen[0]) if seen else None,stack_intact=intact,error=err);reports.append(record);print(record)
(r/'analysis/buffer-command-audit.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n','utf8')
if '--strict' in sys.argv:assert all(x['stack_intact'] for x in reports)
