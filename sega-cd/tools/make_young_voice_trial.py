from pathlib import Path
import json,sys,shutil
from gradio_client import Client,handle_file
sys.stdout.reconfigure(encoding='utf8')
r=Path(__file__).resolve().parents[1];out=r/'build/audio-preview'
client=Client('openbmb/VoxCPM-Demo',verbose=False)
style='A young adult woman in her early twenties. A light, clear, youthful feminine voice. She is hurt and offended, speaking with restrained resentment and a slight reproach, quietly but firmly asking him to leave. Natural conversational Russian, not a narrator. No elderly rasp, no trembling, no melodramatic crying. Preserve the reference speaker identity while making her sound youthful.'
text='Если я вам дорога́, прошу вас уйти.'
print('Generating youthful offended voice using original track 03 reference',flush=True)
result=client.predict(text_input=text,control_instruction=style,reference_wav_path_input=handle_file(str(out/'track03-reference.wav')),use_prompt_text=False,prompt_text_input='',cfg_value_input=2.0,do_normalize=False,denoise=False,api_name='/generate')
print('Generated:',result,flush=True)
shutil.copyfile(result,out/'track03-young-offended-raw.mp3')
(out/'young-voice-trial.json').write_text(json.dumps(dict(provider='Official OpenBMB VoxCPM2 demo',text=text,style=style,reference='track03-reference.wav',synthetic=True,subjective_voice_quality_verified=False),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
