from pathlib import Path
import av,wave,json,sys
from gradio_client import Client
sys.stdout.reconfigure(encoding='utf8')
r=Path(__file__).resolve().parents[1];o=r/'build/audio-preview';c=Client('openbmb/VoxCPM-Demo',verbose=False)
style='A young adult woman aged 20, bright light clear feminine soprano, youthful resonant voice, smooth and fresh, not breathy or husky. She is slightly offended and hurt by her boyfriend, holding back her feelings. Intimate conversational Russian, gentle reproach, clear vowels, quietly firm request. Youthful lively inflection, no storyteller cadence, no granny voice, no age-related rasp or vibrato. Moderate speaking pace. Pronounce the adjective daragAH with stress on its LAST syllable.'
clips=[]
for n,text in enumerate(['Если я вам дарагА́.','Прошу вас уйти.']):
 print('Generating voice design clause',n+1,flush=True)
 path=c.predict(text_input=text,control_instruction=style,reference_wav_path_input=None,use_prompt_text=False,prompt_text_input='',cfg_value_input=2.0,do_normalize=False,denoise=False,api_name='/generate')
 data=[]
 with av.open(path) as container:
  res=av.AudioResampler(format='s16',layout='stereo',rate=44100)
  for frame in container.decode(audio=0):data.extend(f.to_ndarray().tobytes() for f in res.resample(frame))
  data.extend(f.to_ndarray().tobytes() for f in res.resample(None))
 clips.append(b''.join(data))
raw=clips[0]+bytes(22050*4)+clips[1]
with wave.open(str(o/'track03-youthful-design.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(raw)
(o/'youthful-design.json').write_text(json.dumps(dict(style=style,reference_used=False,original_timbre_preserved=False,pause_seconds=0.5,seconds=len(raw)/176400,subjective_quality_verified=False),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Saved',len(raw)/176400,flush=True)
