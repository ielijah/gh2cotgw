from pathlib import Path
import json,sys,struct
sys.path.insert(0,str(Path(__file__).resolve().parent))
from unicorn import *
from unicorn.m68k_const import *
from text_encoding import encode
r=Path(__file__).resolve().parents[1];m=json.loads((r/'build/manifest.json').read_text('utf8'));v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));f=next(x for x in v['files'] if x['path']=='SMAIN.PRG;1');im=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();main=im[f['lba']*2048:][:f['size']];pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
for name in ['Монголы','Империя монголов','Свящ Рим империя','Киевская Русь','Мо'*16]:
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,main);u.reg_write(UC_M68K_REG_SR,0x2700);raw=encode(name,pairs)+b'\0';u.mem_write(0x80000,raw)
 stack=struct.pack('>5I',0x81000,0x330ba,0x80000,29,0x80200)+b'GUARD123';u.mem_write(0x90000,stack);u.reg_write(UC_M68K_REG_A7,0x90000);seen=[]
 def hook(uc,pc,size,data):
  if pc!=0x11034:return
  sp=uc.reg_read(UC_M68K_REG_A7);args=struct.unpack('>4I',uc.mem_read(sp+4,16));assert (args[0],args[2],args[3])==(0x330ba,29,0x80200)
  b=bytes(uc.mem_read(args[1],64)).split(b'\0')[0];seen.append(b)
  cols=0;i=0
  while i<len(b):cols+=1 if b[i]<128 or b[i]==0xfc else 2;i+=1 if b[i]<128 else 2
  assert cols<=13,(name,cols)
  uc.reg_write(UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(UC_M68K_REG_A7,sp+4)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0xc000+m['text_compositor']['map_labels']['helper'],0x81000,count=100000)
 assert seen and bytes(u.mem_read(0x90000,len(stack)))==stack and bytes(u.mem_read(0x80000,len(raw)))==raw
 print('PASS map country',name)
