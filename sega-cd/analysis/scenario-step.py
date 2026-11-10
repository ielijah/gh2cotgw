from pathlib import Path
import os,sys,subprocess,shutil,json,struct
r=Path.cwd();o=r/'analysis/qa-scenarios-final';n=int(sys.argv[1]);src,dst,frames,seq=sys.argv[2:];env=os.environ.copy();env.update(STATE_IN=str(o/f's{n}-{src}.state'),STATE_OUT=str(o/f's{n}-{dst}.state'),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue',frames,seq],env=env,check=True,stdout=subprocess.DEVNULL);shutil.copyfile(r/'analysis/screen-latest.png',o/f's{n}-{dst}.png');print(n,dst,flush=True)
