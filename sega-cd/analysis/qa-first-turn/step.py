from pathlib import Path
import os,sys,subprocess,shutil
r=Path.cwd();o=r/'analysis/qa-first-turn';src,dst,frames,seq=sys.argv[1:]
env=os.environ.copy();env.update(STATE_IN=str(o/(src+'.state')),STATE_OUT=str(o/(dst+'.state')),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue',frames,seq],env=env,check=True)
shutil.copyfile(r/'analysis/screen-latest.png',o/(dst+'.png'))
