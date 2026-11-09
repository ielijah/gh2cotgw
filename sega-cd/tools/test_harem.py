"""Cold boot, new campaign, harem conversation and return to map; record CDDA only."""
from pathlib import Path
import os,sys,json,subprocess,shutil,wave,array,hashlib
ROOT=Path(__file__).resolve().parents[1]
route=json.loads((ROOT/'tools/harem-regression-inputs.json').read_text('utf8'))
env=os.environ.copy()
for key in ('STATE_IN','STATE_OUT','AUDIO_OUT'): env.pop(key,None)
env['CORE_OPTIONS']=json.dumps({'genesis_plus_gx_cart_size':'none','genesis_plus_gx_fm_preamp':'0','genesis_plus_gx_psg_preamp':'0','genesis_plus_gx_pcm_volume':'0','genesis_plus_gx_cdda_volume':'100'})
env['AUDIO_OUT']=str(ROOT/'analysis/harem-regression-cdda.wav')
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(ROOT/'build/playable-dub/game.cue'),str(route['frames']),json.dumps(route['inputs'])],env=env,check=True)
shutil.copyfile(ROOT/'analysis/screen-latest.png',ROOT/'analysis/harem-regression-return.png')
# Golden frame was visually verified: harem closed, map and command menu restored.
assert hashlib.sha256((ROOT/'analysis/harem-regression-return.png').read_bytes()).hexdigest()=='bf562897aa5105da86f63e99438fab86bf651ad2562afd7a367897e291acff44', 'Final map differs: inspect screenshot'
with wave.open(env['AUDIO_OUT']) as wav:
    # These windows correspond to the intro music and the harem response in the fixed route.
    peaks={}
    for label,start,end in [('intro',300,360),('harem',570,700)]:
        wav.setpos(start*44100)
        samples=array.array('h',wav.readframes((end-start)*44100))
        peaks[label]=max(map(abs,samples),default=0)
        assert peaks[label]>100,(label,peaks)
report=dict(frames=route['frames'],cdda_peaks=peaks,core_sha256=hashlib.sha256((ROOT.parent/'.runtime/emulator/genesis_plus_gx_libretro.dll').read_bytes()).hexdigest(),final_screen='harem-regression-return.png',final_map_matches_verified_frame=True)
(ROOT/'analysis/harem-regression.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
