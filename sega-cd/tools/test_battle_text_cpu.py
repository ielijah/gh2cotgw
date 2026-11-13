"""Execute battle formats/composite reports with the real 68000 string routines."""
from pathlib import Path
import json,re,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import *
from text_encoding import encode,encode_stream
from single_letters import code
r=Path(__file__).resolve().parents[1];m=json.loads((r/'build/manifest.json').read_text('utf8'));v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));im=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes()
files={f['path']:im[f['lba']*2048:f['lba']*2048+f['size']] for f in v['files']}
pairs={k:bytes.fromhex(x) for k,x in m['paired_glyphs'].items()};rev={v:k for k,v in pairs.items()}
letters=''.join(chr(ord('А')+n) for n in range(64))+'Ёё';singles={code(c):c for c in letters}
def decode(raw):
 out='';i=0
 while i<len(raw):
  if raw[i]>=0xf0:out+=(singles if raw[i]==0xfc else rev)[raw[i:i+2]];i+=2
  else:assert raw[i]<128;out+=chr(raw[i]);i+=1
 return out
u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,files['SMAIN.PRG;1']);u.mem_write(0x66000,files['HEX.PRG;1']);u.reg_write(UC_M68K_REG_SR,0x2700)
def cstr(a):return bytes(u.mem_read(a,150)).split(b'\0')[0]
captured=[]
def hook(uc,pc,size,data):
 if pc not in (0x82000,0x17436):return
 sp=uc.reg_read(UC_M68K_REG_A7);ptr=int.from_bytes(uc.mem_read(sp+4,4),'big');captured.append(cstr(ptr))
 uc.reg_write(UC_M68K_REG_D0,1);uc.reg_write(UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(UC_M68K_REG_A7,sp+4)
u.hook_add(UC_HOOK_CODE,hook)
def call(fn,args):
 stack=struct.pack('>'+str(len(args)+1)+'I',0x81000,*args)+b'ARGGUARD'
 u.mem_write(0x90000,stack);u.reg_write(UC_M68K_REG_A7,0x90000);u.emu_start(fn,0x81000,count=200000)
 assert u.reg_read(UC_M68K_REG_PC)==0x81000 and u.reg_read(UC_M68K_REG_A7)==0x90004
 assert bytes(u.mem_read(0x90000,len(stack)))==stack
entries=m['applied']+m['text_compositor']['relocated_texts'];byoff={int(e['offset'],16):e for e in entries if e['file']=='HEX.PRG;1'}
def ptr(off):
 e=byoff[off];return 0xc000+e['storage_offset'] if 'storage_offset' in e else 0x66000+off
wave=json.loads((r/'analysis/battle-dialogue-wave.json').read_text('utf8'))
for e in wave:
 off=int(e['offset'],16);raw=cstr(ptr(off));args=[];u.mem_write(0x80000,encode('Константин',pairs)+b'\0')
 for token in re.findall(r'%[0-9]*[ds]',e['ru']):args.append(0x80000 if token.endswith('s') else 99)
 u.mem_write(0x80200,struct.pack('>'+str(len(args))+'I',*args) if args else bytes(4))
 captured.clear();call(0x10214,[ptr(off),0x80200,0x82000]);out=decode(b''.join(captured))
 assert '%' not in out and all(len(line.rstrip())<=22 for line in out.split('\n')),(e,out)
 assert len(out.split('\n'))<=4 and len(out)<128,(e,out)
# Native concatenation: numbered legions, resource reports and destination questions.
def assemble(items):
 for n,item in enumerate(items):
  if isinstance(item,tuple):call(0x11af4,[item[0]])
  else:call(0x11ac6 if n==0 else 0x11ade,[ptr(item)])
 return decode(cstr(0x59ec8))
for verb,expected in [(0x13c66,'пополняет запасы'),(0x13c6c,'охотится')]:
 assert assemble([0x13c78,(5,),0x13c72,verb,0x13c60]).rstrip()==f'Легион 5:\n{expected}.'
for off in (0x13ce2,0x13cea,0x13cf2,0x13cf8,0x13d00):
 out=assemble([0x13d0c,off,0x13d06]).rstrip();assert out.count('?')==1 and ' ?' not in out and len(out)<=22,out
for prefix,suffix in [(0x13bc2,0x13bb2),(0x13c00,0x13bf0)]:
 out=assemble([prefix,(5,),suffix]).rstrip();assert '5: расставьте' in out and len(out)<=22,out
# Map end-turn prompt uses its own shared confirmation, not the battle suffix.
call(0x17460,[0xc000+0x4af5a]);out=decode(captured[-1]);assert out.rstrip()=='Завершить ход \nХорошо?' or out.rstrip()=='Завершить ход\nХорошо?',repr(out)
assert max(map(len,out.split('\n')))<=22
# Surrender bridge appends the predicate before the winner's name, preserving registers.
u.mem_write(0x59ec8,encode('Боорчу',pairs)+b'\n\0');u.mem_write(0x65504,struct.pack('>I',0x80500))
keep={UC_M68K_REG_D0:123,UC_M68K_REG_D1:456,UC_M68K_REG_A1:0x81234}
for reg,val in keep.items():u.reg_write(reg,val)
call(0xc000+m['text_compositor']['battle_text']['helper'],[])
assert all(u.reg_read(reg)==val for reg,val in keep.items()) and u.reg_read(UC_M68K_REG_A0)==0x80500
call(0x11ade,[0x80000]);call(0x11ade,[ptr(0x13f60)])
out=decode(cstr(0x59ec8));assert out.rstrip()=='Боорчу\nсдался.\nПобедитель:\nКонстантин.',repr(out)
print(f'PASS: {len(wave)} native battle formats, numeric/name substitutions, legion reports, destination questions, end-turn confirmation and surrender bridge; stack guards intact')

# The march HUD owns only six font tiles: one digit plus the original suffix.
# A translated four-column suffix used ten tiles and wrapped over the digit.
march_suffix=decode(cstr(ptr(0x13afa)))
assert march_suffix.strip()=='' and (1+len(march_suffix))*2<=6,repr(march_suffix)
tactical_format=decode(cstr(ptr(0x14248)))
assert tactical_format=='%2d' and 2*2<=10,repr(tactical_format)
# Reserve 17 columns for province number/name, then a separate defence field.
assert files['HEX.PRG;1'][0xd780:0xd782]==bytes.fromhex('0014')
for amount in (0,4,99,100,255):
 u.mem_write(0x80200,struct.pack('>I',amount));captured.clear()
 call(0x10214,[ptr(0x142c8),0x80200,0x82000]);out=decode(b''.join(captured))
 assert out.startswith(' Защ:') and len(out)<=8,(amount,out)
 assert 3+3+14<=20 and 20+len(out)<=30
print('PASS: march/tactical glyph budgets and province/defence column bounds')
