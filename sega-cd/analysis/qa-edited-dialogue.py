from pathlib import Path
import json,struct,subprocess,os,sys,shutil
r=Path.cwd();o=r/'analysis/qa-edited-dialogue';o.mkdir(exist_ok=True)
s=bytearray((r/'analysis/qa-province-only/s0-cold.state').read_bytes())
def wr(a,b):
 if len(b)%2:b+=b'\0'
 v=bytearray(b);v[::2],v[1::2]=b[1::2],b[::2];s[229614+a:229614+a+len(b)]=v

for offset in [0x28188,0x2829a,0x28364,0x283be,0x2841c,0x2862a,0x2879e]:
 wr(0x6aff0,bytes.fromhex('4879')+(offset+0xc000).to_bytes(4,'big')+bytes.fromhex('4eb900017436588f60fe'));struct.pack_into('<I',s,1016136,0x6aff0);(o/'fixture.state').write_bytes(s)
 env=os.environ.copy();env.update(STATE_IN=str(o/'fixture.state'),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
 subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue','800','[]'],env=env,check=True,stdout=subprocess.DEVNULL)
 shutil.copyfile(r/'analysis/screen-latest.png',o/f'{offset:X}.png')
