from pathlib import Path
import json,struct,subprocess,os,sys,shutil
r=Path.cwd();o=r/'analysis/qa-command-windows';o.mkdir(exist_ok=True);base=(r/'analysis/qa-scenarios-final/s1-t3.state').read_bytes();m=json.load(open('build/manifest.json'));v=json.load(open('analysis/disc-inventory.json'));f=next(x for x in v['files'] if x['path']=='SMAIN.PRG;1');im=Path('build/genchou-hishi-ru-experimental.iso').read_bytes();suffix=im[f['lba']*2048+0x26fec:].split(b'\0')[0]
rows=json.load(open('analysis/buffer-command-audit.json',encoding='utf8'))
for n,row in enumerate(rows):
 s=bytearray(base)
 def wr(a,b):
  if len(b)%2:b+=b'\0'
  v=bytearray(b);v[::2],v[1::2]=b[1::2],b[::2];s[229614+a:229614+a+len(b)]=v
 wr(0x6ac00,bytes.fromhex(row['raw_hex'])+suffix+b'\0');wr(0x6aff0,bytes.fromhex('48790006ac004eb900017436588f60fe'));struct.pack_into('<I',s,1016136,0x6aff0);(o/'fixture.state').write_bytes(s)
 env=os.environ.copy();env.update(STATE_IN=str(o/'fixture.state'),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
 subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue','800','[]'],env=env,check=True,stdout=subprocess.DEVNULL)
 shutil.copyfile(r/'analysis/screen-latest.png',o/f'{n:02}.png');print('render',n,flush=True)
