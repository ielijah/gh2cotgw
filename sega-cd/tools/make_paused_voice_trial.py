from pathlib import Path
import json,sys,av,wave
from gradio_client import Client,handle_file
sys.stdout.reconfigure(encoding='utf8')
r=Path(__file__).resolve().parents[1];out=r/'build/audio-preview'
c=Client('openbmb/VoxCPM-Demo',verbose=False)
style='A young adult woman in her early twenties, light clear youthful feminine voice. Hurt and offended, restrained resentment and slight reproach, quietly but firmly. Conversational Russian, moderate unhurried pace. No elderly rasp, no trembling or melodramatic crying. Keep the reference speaker identity. Pronunciation: the adjective дорогА means dear, loved. Stress the LAST syllable GA, da-ra-GAH. Never pronounce the noun дорОга meaning road. Emphasize the final stressed A.'
parts=['Если я вам дарагА́.','Прошу вас уйти.']
clips=[]
for n,text in enumerate(parts):
 print('Generating clause',n+1,flush=True)
 path=c.predict(text_input=text,control_instruction=style,reference_wav_path_input=handle_file(str(out/'track03-reference.wav')),use_prompt_text=False,prompt_text_input='',cfg_value_input=2.5,do_normalize=False,denoise=False,api_name='/generate')
 chunks=[]
 with av.open(path) as container:
  res=av.AudioResampler(format='s16',layout='stereo',rate=44100)
  for frame in container.decode(audio=0):chunks.extend(f.to_ndarray().tobytes() for f in res.resample(frame))
  chunks.extend(f.to_ndarray().tobytes() for f in res.resample(None))
 clips.append(b''.join(chunks))
raw=clips[0]+bytes(round(0.5*44100)*4)+clips[1]
with wave.open(str(out/'track03-young-pause.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(raw)
(out/'paused-voice-trial.json').write_text(json.dumps(dict(canonical_text='Если я вам дорога, прошу вас уйти.',tts_clauses=parts,style=style,inserted_pause_seconds=0.5,seconds=len(raw)/176400,stress_verified_by_listener=False),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Saved paused trial',len(raw)/176400,flush=True)
