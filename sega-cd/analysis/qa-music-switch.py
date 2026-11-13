from pathlib import Path
import json,subprocess,os,sys,shutil
r=Path.cwd();o=r/'analysis/qa-music-switch';o.mkdir(exist_ok=True);d=json.loads(Path('analysis/music-review-inputs.json').read_text('utf8'));env=os.environ.copy();env.pop('STATE_IN',None);env.update(STATE_OUT=str(o/'cold.state'),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}');subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue',str(d['frames']),json.dumps(d['inputs'])],env=env,check=True,stdout=subprocess.DEVNULL);shutil.copyfile('analysis/screen-latest.png',o/'cold.png')
