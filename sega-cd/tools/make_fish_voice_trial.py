from pathlib import Path
import sys,json,av,wave
from gradio_client import Client,handle_file
sys.stdout.reconfigure(encoding='utf8')
r=Path(__file__).resolve().parents[1];o=r/'build/audio-preview';c=Client('artificialguybr/fish-s2-pro-zero',verbose=False)
parts=['[young adult woman][hurt][soft voice]Если я вам дорогА́.','[young adult woman][restrained resentment][soft voice]Прошу вас уйти.']
clips=[]
for n,text in enumerate(parts):
 print('Fish generating clause',n+1,flush=True)
 path=c.predict(text=text,ref_audio=handle_file(str(o/'track03-reference.wav')),ref_text='私のことを考えくださるなら、お引き取りください。',max_new_tokens=512,chunk_length=200,top_p=0.7,repetition_penalty=1.2,temperature=0.65,api_name='/tts_inference')
 print('Fish returned',path,flush=True)
 chunks=[]
 with av.open(path) as container:
  res=av.AudioResampler(format='s16',layout='stereo',rate=44100)
  for frame in container.decode(audio=0):chunks.extend(f.to_ndarray().tobytes() for f in res.resample(frame))
  chunks.extend(f.to_ndarray().tobytes() for f in res.resample(None))
 clips.append(b''.join(chunks))
raw=clips[0]+bytes(22050*4)+clips[1]
with wave.open(str(o/'track03-fish-trial.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(raw)
(o/'fish-voice-trial.json').write_text(json.dumps(dict(provider='Community Fish S2 Pro Hugging Face demo artificialguybr/fish-s2-pro-zero',clauses=parts,reference='track03-reference.wav',synthetic=True,pause_seconds=0.5,seconds=len(raw)/176400,stress_and_voice_age_verified=False,cue_installed=False),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Saved Fish voice trial',len(raw)/176400,flush=True)
