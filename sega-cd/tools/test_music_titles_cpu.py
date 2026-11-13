"""Run the music-title helper on a 68000 and verify its native call contract."""
from pathlib import Path
import json,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import *
from text_encoding import encode
r=Path(__file__).resolve().parents[1];m=json.loads((r/'build/manifest.json').read_text('utf8'));v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));image=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();files={x['path']:image[x['lba']*2048:x['lba']*2048+x['size']] for x in v['files']};main=files['SMAIN.PRG;1'];init=files['INIT.PRG;1'];record=m['text_compositor']['music_titles'];mapping={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()};titles=[e for e in m['applied']+m['text_compositor']['relocated_texts'] if e['file']=='INIT.PRG;1' and 0x14fd4<=int(e['offset'],16)<=0x1502c];assert len(titles)==9
for e in titles:
 lines=e['ru'].split('\n');assert len(lines)<=3 and max((len(line)+1)//2*2 for line in lines)<=12
 assert len(encode(e['ru'],mapping).replace(b'\n',b''))*2<record.get('tile_capacity',75)
for track in range(9):
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,main);u.mem_write(0x66000,init);u.reg_write(UC_M68K_REG_SR,0x2700);u.reg_write(UC_M68K_REG_A7,0x90000);args=list(range(1,9));u.mem_write(0x90000,struct.pack('>9I',0x81000,*args));u.reg_write(UC_M68K_REG_D2,track);u.mem_write(0x59f4c,b'\x00\x0c');calls=[]
 def hook(uc,pc,size,data):
  if pc in (0xc0f4,0x1047c,0x11034):
   sp=uc.reg_read(UC_M68K_REG_A7);n=7 if pc==0xc0f4 else 2;vals=struct.unpack('>'+str(n)+'I',bytes(uc.mem_read(sp+4,n*4)));calls.append((pc,vals))
   if pc==0x11034:assert bytes(uc.mem_read(0x59f4c,2))==b'\0\2'
   ret=int.from_bytes(uc.mem_read(sp,4),'big');uc.reg_write(UC_M68K_REG_A7,sp+4);uc.reg_write(UC_M68K_REG_PC,ret)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(record['helper']+0xc000,0x81000,count=1000);pointer=int.from_bytes(init[0x1778a+track*4:0x1778e+track*4],'big')
 assert calls==[(0xc0f4,(26,0,2,19,13,6,0x8000)),(0x1047c,(2,19)),(0x11034,(0x7b038,pointer))],calls
 assert u.reg_read(UC_M68K_REG_A7)==0x90004 and bytes(u.mem_read(0x59f4c,2))==b'\0\x0c'
print('PASS: all nine music titles fit frame and tile window; native rectangle arguments, text cursor, selected pointer, restored margin and stack')
