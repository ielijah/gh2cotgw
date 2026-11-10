"""Execute the ten-cell nameplate guard against long paired and editable names."""
from pathlib import Path
import json, struct, sys
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.m68k_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from text_encoding import encode
from single_letters import code
r=Path(__file__).resolve().parents[1]
m=json.loads((r/'build/manifest.json').read_text('utf8'))
i=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'))
f=next(f for f in i['files'] if f['path']=='SMAIN.PRG;1')
main=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes()[f['lba']*2048:][:f['size']]
c=m['text_compositor'];pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
def machine(raw):
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
 u.mem_map(0,0x100000);u.mem_write(0xc000,main);u.reg_write(UC_M68K_REG_SR,0x2700)
 u.mem_write(0x80000,raw+b'\0');u.mem_write(0x90000,struct.pack('>II',0x81000,0x80000));u.reg_write(UC_M68K_REG_A7,0x90000)
 return u
def width(raw):
 u=machine(raw);u.emu_start(0xff58,0x81000,count=10000);return u.reg_read(UC_M68K_REG_D0)
cases=[encode(s,pairs) for s in ('Хубилай-хан','Темучин','Боорчу','Чингисхан','Бортэ')]
cases += [code('Я')*n for n in range(1,15)]
cases += [b'A'*n for n in range(1,15)]
cases += [pairs['Ху']*n for n in range(1,8)]
for raw in cases:
 u=machine(raw);drawn=[]
 def intercept(uc,pc,size,data):
  if pc!=0x10af8:return
  sp=uc.reg_read(UC_M68K_REG_A7);p=int.from_bytes(uc.mem_read(sp+4,4),'big');s=bytearray()
  while uc.mem_read(p,1)[0]:s+=uc.mem_read(p,1);p+=1
  drawn.append(bytes(s));ret=int.from_bytes(uc.mem_read(sp,4),'big');uc.reg_write(UC_M68K_REG_A7,sp+4);uc.reg_write(UC_M68K_REG_PC,ret)
 u.hook_add(UC_HOOK_CODE,intercept);u.emu_start(0xc000+c['nameplate_draw'],0x81000,count=10000)
 assert len(drawn)==1 and width(drawn[0])<=10,(raw,drawn)
 assert drawn[0]==raw if width(raw)<=10 else drawn[0].endswith(b'..')
 assert u.reg_read(UC_M68K_REG_A7)==0x90004
 assert bytes(u.mem_read(0x80000,len(raw)+1))==raw+b'\0'
 u=machine(raw);u.mem_write(0x59eac,struct.pack('>H',20));u.emu_start(0xc000+c['nameplate_trim'],0x81000,count=10000)
 assert 0<=u.reg_read(UC_M68K_REG_D0)<=10
 if width(raw)>10:assert bytes(u.mem_read(0x59eac,2))==struct.pack('>H',20)
print(f'PASS: {len(cases)} nameplate cases; actual 68000 draw/width helpers, native widths, source strings and stack preserved')
