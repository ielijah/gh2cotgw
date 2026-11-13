from pathlib import Path
import json,os,subprocess,sys,shutil,struct,re
r=Path.cwd();o=r/'analysis/qa-overlays';o.mkdir(exist_ok=True)
base=[x for x in json.load(open('tools/harem-regression-inputs.json'))['inputs'] if x[0]<25000]
for n in [0]:
 route=base+[[25010,25020,0]]+[[25610+j*100,25620+j*100,5] for j in range(n)]+[[26060,26070,8]]
 route += [[t,t+10,8] for t in [26610,27210,27810,28410,29010,29610]]
 route += [[28310,28320,7],[28910,28920,7]]
 env=os.environ.copy();env.pop('STATE_IN',None);env.update(STATE_OUT=str(o/f's{n}-cold.state'),CORE_OPTIONS='{"genesis_plus_gx_cart_size":"none"}')
 subprocess.run([sys.executable,'tools/emulate.py','build/playable-dub/game.cue','38000',json.dumps(route)],env=env,check=True,stdout=subprocess.DEVNULL)
 shutil.copyfile(r/'analysis/screen-latest.png',o/f's{n}-cold.png');(o/f's{n}-route.json').write_text(json.dumps(route));print('cold',n,flush=True)
