from pathlib import Path
import json,subprocess,sys,os,shutil
r=Path(__file__).resolve().parents[1];o=r/'analysis/qa-card-options'
route=json.loads((r/'tools/harem-regression-inputs.json').read_text())
env=os.environ.copy();env.pop('STATE_IN',None)
env.update(STATE_OUT=str(o/'cold-map.state'),AUDIO_OUT=str(o/'cold-cdda.wav'),CORE_OPTIONS=json.dumps({'genesis_plus_gx_cart_size':'none','genesis_plus_gx_fm_preamp':'0','genesis_plus_gx_psg_preamp':'0','genesis_plus_gx_pcm_volume':'0','genesis_plus_gx_cdda_volume':'100'}))
subprocess.run([sys.executable,str(r/'tools/emulate.py'),str(r/'build/qa-cards/game.cue'),'30500',json.dumps([v for v in route['inputs'] if v[0]<30500])],env=env,check=True)
shutil.copyfile(r/'analysis/screen-latest.png',o/'cold-map.png')
