from pathlib import Path
import json,struct,subprocess,os,sys,shutil
r=Path.cwd();o=r/'analysis/qa-music-switch';s=bytearray((o/'cold.state').read_bytes())
for n in list(range(9))+[0,5,1,8,0]:
 code=bytes.fromhex('4878')+n.to_bytes(2,'big')+bytes.fromhex('4eb90006a0d8588f60fe');v=bytearray(code);v[::2],v[1::2]=code[1::2],code[::2];s[229614+0x65e00:229614+0x65e00+len(v)]=v;struct.pack_into('<I',s,1016136,0x65e00);(o/'fixture.state').write_bytes(s)
 env=os.environ.copy();env.update(STATE_IN=str(o/'fixture.state'),STATE_OUT=str(o/'after.state'),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
 subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue','400','[]'],env=env,check=True,stdout=subprocess.DEVNULL);shutil.copyfile('analysis/screen-latest.png',o/f'title-{n}.png');s=bytearray((o/'after.state').read_bytes())
