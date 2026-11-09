from pathlib import Path
import sys,wave,json,shutil,hashlib
from gradio_client import Client,handle_file
sys.stdout.reconfigure(encoding='utf8')
r=Path(__file__).resolve().parents[1];out=r/'build/audio-preview';out.mkdir(exist_ok=True)
source=next((r/'disc').glob('*(Track 03 of*wav'))
with wave.open(str(source),'rb') as src:
 params=src.getparams();audio=src.readframes(src.getnframes())
 # Remove the original two-second pregap only from the model reference.
 with wave.open(str(out/'track03-reference.wav'),'wb') as dst:
  dst.setparams(params);dst.writeframes(audio[int(1.87*44100)*4:int(6.19*44100)*4])
text='Если я вам дорога́, прошу вас уйти.'
client=Client('ResembleAI/Chatterbox-Multilingual-TTS',verbose=False)
print('Generating Russian voice-conditioned trial from track 03',flush=True)
result=client.predict(text_input=text,language_id='ru',audio_prompt_path_input=handle_file(str(out/'track03-reference.wav')),exaggeration_input=0.45,temperature_input=0.65,seed_num_input=42,cfgw_input=0.4,api_name='/generate_tts_audio')
print('Result',result,flush=True)
shutil.copyfile(result,out/'track03-ru-clone-raw.wav')
(out/'voice-clone-trial.json').write_text(json.dumps(dict(source_track=3,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),ja_asr='私のことを考えくださるなら、お引き取りください',ru=text,provider='Official ResembleAI Chatterbox Multilingual Hugging Face demo',reference_seconds=[1.87,6.19],seed=42,note='Synthetic experimental cross-language voice match; not an original actor recording. Not yet installed into the disc CUE.'),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
