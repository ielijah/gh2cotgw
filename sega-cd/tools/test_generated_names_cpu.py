"""Real 68000 generators, bounded Russian conversion, and dictionary coverage."""
from pathlib import Path
import json,struct,sys,random
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
from unicorn.m68k_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from generated_names_data import mappings
from text_encoding import encode
from single_letters import code as single_code
r=Path(__file__).resolve().parents[1];m=json.loads((r/'build/manifest.json').read_text('utf8'));iv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));f=next(f for f in iv['files'] if f['path']=='SMAIN.PRG;1');im=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();main=im[f['lba']*2048:f['lba']*2048+f['size']];g=m['text_compositor']['generated_names'];tokens=mappings();pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()};reverse={v:k for k,v in pairs.items()}
u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,main)
def call(fn,args):
 u.mem_write(0x90000,struct.pack('>'+str(len(args)+1)+'I',0x81000,*args));u.reg_write(UC_M68K_REG_A7,0x90000);u.emu_start(fn,0x81000,count=2000000)
 assert u.reg_read(UC_M68K_REG_PC)==0x81000,(hex(fn),hex(u.reg_read(UC_M68K_REG_PC)))
 assert u.reg_read(UC_M68K_REG_A7)==0x90004
 return u.reg_read(UC_M68K_REG_D0)
def reference(raw,mode):
 text='';unknown=[];pos=0
 while pos<len(raw) and len(text)<32:
  if raw[pos]==27:pos+=2;continue
  match=next(((a,s) for a,mask,s in tokens if mask&(1<<mode) and raw.startswith(a,pos)),None)
  if match:a,s=match;text+=s;pos+=len(a)
  else:
   n=2 if 0x80<=raw[pos]<0xa0 or raw[pos]>=0xe0 else 1;unknown.append(raw[pos:pos+n]);pos+=n
 text=text[:32].rstrip();text=text[:1].upper()+text[1:];out=b'';pos=0
 while pos<len(text) and len(out)<14:
  pair=text[pos:pos+2]
  if len(pair)==2 and (pair in pairs or pair.isascii()):data=pairs.get(pair,pair.encode('ascii') if pair.isascii() else None);n=2
  else:data=single_code(text[pos]) if not text[pos].isascii() else text[pos].encode();n=1
  if len(out)+len(data)>14:break
  out+=data;pos+=n
 return out,unknown,text
cases=[]
# Cover each dictionary token in every applicable context, including overrides.
for raw,mask,ru in tokens:
 for mode in range(24):
  if mask&(1<<mode):cases.append((raw,mode))
# Native procedural routines exercise real random syllables and all culture tables.
for mode in range(24):
 table,index=(0x4b2a8,mode) if mode<8 else (0x4b410,mode-8) if mode<16 else (0x4b5bc,mode-16)
 fn=int.from_bytes(main[table+index*4:table+index*4+4],'big')
 for seed in range(64):
  u.mem_write(0x636fc,struct.pack('>I',seed*1009+17));u.mem_write(0x80000,b'\0'+bytes([85])*63);call(fn,[0x80000]);raw=bytes(u.mem_read(0x80000,64)).split(b'\0')[0];cases.append((raw,mode))
# Scenario-specific country generators bypass the culture table.
for mode,fn in [(16,0x17ef2),(19,0x17f2e)]:
 for seed in range(64):
  u.mem_write(0x636fc,struct.pack('>I',seed*701+19));u.mem_write(0x80000,b'\0'+bytes([85])*63);call(fn,[0x80000]);cases.append((bytes(u.mem_read(0x80000,64)).split(b'\0')[0],mode))
unknown=[];tested=0
for raw,mode in dict.fromkeys(cases):
 expected,bad,spelling=reference(raw,mode)
 if bad:unknown.append(dict(raw=raw.hex(),mode=mode,unknown=[b.hex() for b in bad]));continue
 assert len(raw)<32
 u.mem_write(0x80000,raw+b'\0'+bytes([85])*(64-len(raw)-1));before=bytes(u.mem_read(0x80000,64))
 errors=call(0xc000+g['convert'],[0x80000,mode%8,16 if mode<8 else 15 if mode<16 else 32]);actual=bytes(u.mem_read(0x80000,64));result=actual.split(b'\0')[0]
 assert errors==0,(raw,mode,errors)
 assert result==expected,(raw,mode,spelling,result.hex(),expected.hex())
 assert len(result)<=14 and actual[15:]==before[15:],(raw,mode,'guard')
 tested+=1
(r/'analysis/generated-names-unknown.json').write_text(json.dumps(unknown,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not unknown,unknown[:10]
print(f'PASS: {tested} native/dictionary cases; 24 culture/sex/country contexts; no Japanese tokens, buffer overruns, or stack imbalance')

# All original extracted name/dynasty components must have a recognized context.
parts=json.loads((r/'analysis/remaining-translation-2839.json').read_text('utf8'))['main_pool_remaining']
for entry in parts:
 raw=entry['ja'].encode('shift_jis')
 assert any(not reference(raw,mode)[1] for mode in range(24)),entry
# Exercise the outer country generator, including scenario overrides of culture.
for scenario in range(5):
 for culture in range(8):
  mode=16 if scenario==0 else 19 if scenario==1 else 16+culture
  fn=0x17ef2 if scenario==0 else 0x17f2e if scenario==1 else int.from_bytes(main[0x4b5bc+culture*4:0x4b5c0+culture*4],'big')
  for seed in (17,12345,987654):
   u.mem_write(0x636fc,struct.pack('>I',seed));u.mem_write(0x80000,bytes(64));call(fn,[0x80000]);raw=bytes(u.mem_read(0x80000,64)).split(b'\0')[0]
   expected,bad,_=reference(raw,mode);assert not bad
   u.mem_write(0x7fd1e,bytes([scenario]));u.mem_write(0x636fc,struct.pack('>I',seed));u.mem_write(0x80000,bytes(64));call(0x180be,[0x80000,culture])
   assert bytes(u.mem_read(0x80000,64)).split(b'\0')[0]==expected,(scenario,culture,seed)
print(f'PASS: all {len(parts)} original generator components covered; 120 outer country calls preserve scenario-specific readings')
