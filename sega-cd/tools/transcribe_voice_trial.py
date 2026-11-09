from pathlib import Path
import json,sys
from faster_whisper import WhisperModel
sys.stdout.reconfigure(encoding='utf8')
r=Path(__file__).resolve().parents[1]; cache=r.parent/'.runtime/audio/models'
print('Loading Japanese ASR model',flush=True)
model=WhisperModel('base',device='cpu',compute_type='int8',download_root=str(cache),cpu_threads=4)
results=[]
for number in (2,3,4):
 p=next((r/'disc').glob(f'*(Track {number:02} of*wav'))
 segments,info=model.transcribe(str(p),language='ja',beam_size=5,condition_on_previous_text=False,vad_filter=True)
 rows=[dict(start=s.start,end=s.end,text=s.text,probability=s.avg_logprob,no_speech_probability=s.no_speech_prob) for s in segments]
 result=dict(track=number,file=p.name,segments=rows);results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
 dest=r/'build/audio-preview/transcription-trial.json';dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
