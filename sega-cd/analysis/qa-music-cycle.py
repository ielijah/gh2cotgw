from pathlib import Path
import json,os,subprocess,sys,shutil
r=Path.cwd();o=r/'analysis/qa-music-switch';previous=o/'cold.state'
for n,button in enumerate([5]*8+[4]*8):
 env=os.environ.copy();dest=o/f'switch-{n:02}.state';env.update(STATE_IN=str(previous),STATE_OUT=str(dest),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
 subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue','300',json.dumps([[10,20,button]])],env=env,check=True,stdout=subprocess.DEVNULL);shutil.copyfile('analysis/screen-latest.png',o/f'switch-{n:02}.png');previous=dest
