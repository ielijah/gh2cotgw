"""Verify late scenario records, overlay fields and expanded mission-table dispatch."""
from pathlib import Path
import json,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
from unicorn.m68k_const import *
from text_encoding import encode,encode_stream
r=Path(__file__).resolve().parents[1];m=json.loads((r/'build/manifest.json').read_text('utf8'));v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));original=(r/'disc'/v['image']).read_bytes();patched=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();files={f['path']:f for f in v['files']};wave=json.loads((r/'analysis/late-fields-wave.json').read_text('utf8'));entries={(e['file'],e['offset']):e for e in m['applied']+m['text_compositor']['relocated_texts']};pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()};reverse={v:k for k,v in pairs.items()}
def decode(raw):
 out='';i=0
 while i<len(raw):
  if raw[i]>=0xf0:out+=reverse[raw[i:i+2]];i+=2
  else:assert raw[i]<128;out+=chr(raw[i]);i+=1
 return out
names=0
for w in wave:
 e=entries[w['file'],w['offset']];base=files[e['file']]['lba']*2048;off=int(e['offset'],16);dest=files['SMAIN.PRG;1']['lba']*2048+e['storage_offset'] if 'storage_offset' in e else base+off
 expected=(encode_stream if e.get('native_stream') else encode)(e['ru'],pairs)
 assert patched[dest:dest+len(expected)+1]==expected+b'\0'
 assert all(len(x.rstrip())<=22 for x in decode(expected).split('\n'))
 if e['kind']=='person_name':
  assert len(expected)<=14
  assert patched[base+off-4:base+off]==original[base+off-4:base+off]
  assert patched[base+off+15:base+off+22]==original[base+off+15:base+off+22]
  names+=1
assert names==13
f=files['SMAIN.PRG;1'];main=patched[f['lba']*2048:f['lba']*2048+f['size']]
u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(UC_CPU_M68K_M68000);u.mem_map(0,0x100000);u.mem_write(0xc000,main);u.reg_write(UC_M68K_REG_SR,0x2700)
for index,label in enumerate(['Поход','Переход','Доставка']):
 u.reg_write(UC_M68K_REG_A7,0x90000);u.mem_write(0x90000,b'STACKGUARD');u.reg_write(UC_M68K_REG_D2,index);u.reg_write(UC_M68K_REG_A2,0x11ade)
 u.emu_start(0x259c4,0x259f0,count=10000)
 assert u.reg_read(UC_M68K_REG_PC)==0x259f0 and u.reg_read(UC_M68K_REG_A7)==0x90000
 assert bytes(u.mem_read(0x90000,10))==b'STACKGUARD'
 text=decode(bytes(u.mem_read(0x59ec8,128)).split(b'\0')[0]);assert label in text and 'Выполнить?' in text,text
 assert all(len(line.rstrip())<=22 for line in text.splitlines())
print(f'PASS: {len(wave)} late fields; all 13 names preserve adjacent flags/records; all three expanded mission labels execute and fit the native report')
