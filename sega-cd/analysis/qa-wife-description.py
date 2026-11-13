from pathlib import Path
import json,struct,subprocess,os,sys,shutil
r=Path.cwd();o=r/'analysis/qa-wife-description';o.mkdir(exist_ok=True)
s=bytearray((r/'analysis/qa-overlays/s0-cold.state').read_bytes())
def wr(a,b):
 if len(b)%2:b+=b'\0'
 v=bytearray(b);v[::2],v[1::2]=b[1::2],b[::2];s[229614+a:229614+a+len(b)]=v

sys.path.insert(0,'tools')
from text_encoding import encode
m=json.loads(Path('build/manifest.json').read_text('utf8'));pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
wr(0x6ac00,encode('Халифе\nОчень рассудительна',pairs)+b'\0')
wr(0x6aff0,bytes.fromhex('48790006ac004eb900017436588f60fe'));struct.pack_into('<I',s,1016136,0x6aff0);(o/'fixture.state').write_bytes(s)
env=os.environ.copy();env.update(STATE_IN=str(o/'fixture.state'),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue','800','[]'],env=env,check=True,stdout=subprocess.DEVNULL)
shutil.copyfile(r/'analysis/screen-latest.png',o/'wife.png')
