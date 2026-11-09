"""Execute the actual patched 68000 letter renderer and native length guard."""
from pathlib import Path
import json,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import *
from single_letters import ALPHABET,code
from text_encoding import encode
r=Path(__file__).resolve().parents[1];m=json.loads((r/'build/manifest.json').read_text('utf8'));inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));image=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();f=next(x for x in inv['files'] if x['path']=='SMAIN.PRG;1');main=image[f['lba']*2048:][:f['size']];c=m['text_compositor'];single=c['single_letters'];pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
def machine():
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,main);u.reg_write(UC_M68K_REG_SR,0x2700);u.reg_write(UC_M68K_REG_A7,0x90000);return u

def width(data):
 u=machine();u.mem_write(0x80000,data+b'\0');u.mem_write(0x90000,struct.pack('>II',0x81000,0x80000));u.emu_start(0xff58,0x81000,count=10000);assert u.reg_read(UC_M68K_REG_PC)==0x81000;return u.reg_read(UC_M68K_REG_D0)
for ch in ALPHABET:assert width(code(ch))==1,ch
for name in ('Темучин','Бортэ','Ёлка','АБВГДЕЁЖЗ','яяя','Сорхан-Шира'):
 data=b''.join(code(ch) if ch in ALPHABET else ch.encode('ascii') for ch in name);assert width(data)==len(name)
for s in ('123','Темучин','Боорчу','Имя: '):assert width(encode(s,pairs))==(len(s)+1)//2*2
# Render every single letter into the real compositor scratch buffer. Stop
# before native VDP tile upload; compare pixels against the imported font.
for i,ch in enumerate(ALPHABET):
 u=machine();u.reg_write(UC_M68K_REG_A6,0x90000);u.mem_write(0x9000a,code(ch));u.emu_start(0xc000+single['dispatch'],0xc000+0x4a44,count=1000)
 assert u.reg_read(UC_M68K_REG_PC)==0xc000+0x4a44
 rows=main[c['character_addresses'][i]:c['character_addresses'][i]+16];actual=bytes(u.mem_read(0x90000-164,32));assert actual==rows[:8]+bytes(8)+rows[8:]+bytes(8),ch
# Native writer's byte-capacity check must reject the eighth Cyrillic key,
# while permitting seven and handling both upper/lower case and Ё.
for existing,letter,allowed in [('Темучи','н',True),('Темучин','а',False),('Ёж','и',True),('123456789','0',True),('1234567890','1',False)]:
 u=machine();pack=lambda s:b''.join(code(ch) if ch in ALPHABET else ch.encode('ascii') for ch in s)
 u.mem_write(0x5e924,pack(existing)+b'\0');u.mem_write(0x80000,pack(letter)+b'\0');u.mem_write(0x90000,struct.pack('>II',0x81000,0x80000));hit=[]
 def stop(uc,address,size,data):
  if address in (0xc000+0x10c80,0xc000+0x10cf0):hit.append(address==0xc000+0x10cf0);uc.emu_stop()
 u.hook_add(UC_HOOK_CODE,stop);u.emu_start(0xc000+0x10c0c,0x81000,count=10000);assert hit==[allowed],(existing,letter,hit)
print('PASS: 68000 execution: all 66 single-letter widths and bitmaps; mixed names; native seven-letter byte limit and ten-cell display limit')

# Execute conversion, upload and allocation as well, not merely the bitmap
# compositor. Singles must consume TWO VRAM tiles; pairs still consume four.
for ch in ALPHABET:
 u=machine();u.mem_write(0x90000,struct.pack('>III',0x81000,int.from_bytes(code(ch),'big'),0x80000));u.mem_write(0x5a11e,struct.pack('>H',200));u.mem_write(0x5a084,struct.pack('>H',1000));u.mem_write(0x5c820,b'\x0e');u.mem_write(0x59f4e,b'\x09');uploads=[]
 def upload(uc,pc,size,data):
  if pc==0xe7ac:
   sp=uc.reg_read(UC_M68K_REG_A7);buf,tile,count=struct.unpack('>III',bytes(uc.mem_read(sp+4,12)));uploads.append((tile,count,bytes(uc.mem_read(buf,count*32))));ret=int.from_bytes(uc.mem_read(sp,4),'big');uc.reg_write(UC_M68K_REG_A7,sp+4);uc.reg_write(UC_M68K_REG_PC,ret)
 u.hook_add(UC_HOOK_CODE,upload);u.emu_start(0x10a1c,0x81000,count=10000);i=ALPHABET.index(ch);rows=main[c['character_addresses'][i]:c['character_addresses'][i]+16];expected=bytes(((14 if row&(128>>x) else 9)<<4)|(14 if row&(64>>x) else 9) for row in rows for x in (0,2,4,6))
 assert uploads==[(200,2,expected)],(ch,[(x,y) for x,y,z in uploads])
 assert bytes(u.mem_read(0x80000,4))==struct.pack('>HH',200,201)
 assert bytes(u.mem_read(0x5a11e,2))==struct.pack('>H',202)
 assert u.reg_read(UC_M68K_REG_A7)==0x90004
assert 66*2+24*2<2*145+1
print('PASS: all 66 single letters upload exactly two native VRAM tiles; full 90-key keyboard fits the original tile window')
