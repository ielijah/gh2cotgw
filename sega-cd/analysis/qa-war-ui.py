"""Prepared Genesis Plus GX UI checks; reload current PRGs before each fixture."""
from pathlib import Path
import json,struct,subprocess,os,sys,shutil
sys.path.insert(0,str(Path('tools').resolve()))
from text_encoding import encode_stream
r=Path.cwd();o=r/'analysis/qa-war-ui';o.mkdir(exist_ok=True)
v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));m=json.loads((r/'build/manifest.json').read_text('utf8'));im=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes();pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
entries={(e['file'],e['offset']):e for e in m['applied']+m['text_compositor']['relocated_texts']}
def ptr(file,off):
 e=entries[file,off];return 0xc000+e['storage_offset'] if 'storage_offset' in e else (0xc000 if file.startswith('SMAIN') else 0x66000)+int(off,16)
def pea(a):return bytes.fromhex('4879')+struct.pack('>I',a)
def jsr(a):return bytes.fromhex('4eb9')+struct.pack('>I',a)
def run(name,base,code,extra=[]):
 s=bytearray((r/base).read_bytes())
 def wr(a,b):
  if len(b)%2:b+=b'\0'
  z=bytearray(b);z[::2],z[1::2]=b[1::2],b[::2];s[229614+a:229614+a+len(b)]=z
 for file,a in [('SMAIN.PRG;1',0xc000),('HEX.PRG;1',0x66000)]:
  f=next(f for f in v['files'] if f['path']==file);wr(a,im[f['lba']*2048:f['lba']*2048+f['size']])
 for a,b in extra:wr(a,b)
 wr(0x7f000,code+bytes.fromhex('60fe'));struct.pack_into('<I',s,1016136,0x7f000);(o/'fixture.state').write_bytes(s)
 env=os.environ.copy();env.update(STATE_IN=str(o/'fixture.state'),STATE_OUT=str(o/(name+'.state')))
 subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue','800','[]'],env=env,check=True,stdout=subprocess.DEVNULL);shutil.copyfile(r/'analysis/screen-latest.png',o/(name+'.png'))
mapbase='analysis/qa-province-only/s0-cold.state';battlebase='analysis/qa-battle-wave-final.state'
for index in range(3):
 code=bytes.fromhex('7400')[:-1]+bytes([index])+bytes.fromhex('247c00011ade4ef9000259c4')
 cont=pea(0x59ec8)+jsr(0x17436)+bytes.fromhex('588f60fe')
 run('mission-'+str(index),mapbase,code,[(0x259f0,bytes.fromhex('4ef90007f040')),(0x7f040,cont)])
run('legions',mapbase,pea(ptr('SMAIN.PRG;1','4D4C6'))+jsr(0x17436)+bytes.fromhex('588f'))
code=pea(ptr('SMAIN.PRG;1','297F8'))+jsr(0x11ac6)+bytes.fromhex('588f487804b0')+jsr(0x11af4)+bytes.fromhex('588f')+pea(ptr('SMAIN.PRG;1','297E0'))+jsr(0x11ade)+bytes.fromhex('588f')+pea(0x59ec8)+jsr(0x17436)+bytes.fromhex('588f')
run('supply',mapbase,code)
run('march-counter',battlebase,jsr(0x67a5e))
run('tactical-counter',battlebase,jsr(0x707ca))
(o/'report.json').write_text(json.dumps({'iso_sha256':m['iso_sha256'],'emulator':'Genesis Plus GX','method':'Prepared rendering fixtures with current SMAIN and HEX reloaded; not full battle playthrough.','cases':['mission-0','mission-1','mission-2','legions','supply','march-counter','tactical-counter']},ensure_ascii=False,indent=2),'utf8')

run('march-counter-3',battlebase,jsr(0x67a5e),[(0x656f8,struct.pack('>I',0x7e800)),(0x7e800,bytes(6)+bytes([18,0]))])
run('tactical-counter-30',battlebase,jsr(0x707ca),[(0x65d3e,bytes([30,0]))])

# Exercise the same native field renderer/positions without entering the modal header.
def push(n):return pea(n)
def clean(n):return bytes.fromhex('4fef')+struct.pack('>H',n)
code=push(175)+push(62)+jsr(0x106e2)+clean(8)+push(14)+jsr(0x105ac)+clean(4)+push(1)+jsr(0x10600)+clean(4)
code+=push(14)+push(3)+jsr(0x1047c)+clean(8)+pea(0x7e900)+jsr(0x10af8)+clean(4)
code+=push(14)+push(20)+jsr(0x1047c)+clean(8)+push(4)+pea(ptr('HEX.PRG;1','142C8'))+jsr(0x11034)+clean(8)
run('province-defence',battlebase,code,[(0x7e900,encode_stream('5:Горы Баргучин',pairs)+bytes([0]))])
report=json.loads((o/'report.json').read_text('utf8'));report['cases']+=['march-counter-3','tactical-counter-30','province-defence'];report['note']='Deployment sprites can overlap the artificial tactical HUD fixture; this is not a playthrough of a tactical battle.';(o/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
