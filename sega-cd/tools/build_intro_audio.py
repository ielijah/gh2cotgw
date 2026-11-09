"""Mix the approved ruler voice with separated intro music, preserving CD length."""
from pathlib import Path
import hashlib, json, wave
import av
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100
PREVIEW = ROOT/'build/audio-preview'

def decode(path):
    chunks=[]
    resampler=av.AudioResampler(format='fltp', layout='stereo', rate=RATE)
    with av.open(str(path)) as container:
        for frame in container.decode(audio=0):
            chunks.extend(f.to_ndarray() for f in resampler.resample(frame))
    chunks.extend(f.to_ndarray() for f in resampler.resample(None))
    return np.concatenate(chunks,axis=1)

def tempo(samples, speed):
    frame=av.AudioFrame.from_ndarray(np.ascontiguousarray(samples), format='fltp',layout='stereo')
    frame.sample_rate=RATE
    graph=av.filter.Graph()
    source=graph.add('abuffer', f'sample_rate={RATE}:sample_fmt=fltp:channel_layout=stereo:time_base=1/{RATE}')
    effect=graph.add('atempo',str(speed))
    sink=graph.add('abuffersink')
    planar=graph.add('aformat','sample_fmts=fltp')
    source.link_to(effect);effect.link_to(planar);planar.link_to(sink);graph.configure()
    graph.push(frame);graph.push(None)
    result=[]
    while True:
        try: result.append(graph.pull().to_ndarray())
        except (av.error.EOFError,av.error.BlockingIOError): break
    return np.concatenate(result,axis=1)

def main():
    original=next((ROOT/'disc').glob('*(Track 90 of*wav'))
    with wave.open(str(original)) as wav:
        params=wav.getparams()
        original_pcm=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').reshape(-1,2).copy()
    music,_=sf.read(PREVIEW/'separated/htdemucs/intro-source-100s/no_vocals.wav',dtype='float32',always_2d=True)
    speech={n:decode(PREVIEW/f'intro-narrator-{n}.mp3') for n in (1,2,3)}
    # Clause boundaries checked against word timestamps. Timeline uses original CD seconds.
    cues=[(1,0,3.5,14.58,.82),(1,3.5,5.9,21.3,.82),(1,5.9,None,26.1,.82),
          (2,0,1.6,34.0,.82),(2,1.6,7.7,37.0,.82),(2,7.7,12.7,47.0,.82),
          (2,12.7,15.05,54.0,.82),(2,15.05,19.25,58.0,.82),
          (2,19.25,None,66.0,.82),(3,0,None,87.9,.90)]
    mix=original_pcm.astype(np.float32)/32768
    # Crossfade only the narrated section; untouched PCM before/after is retained below.
    first,last=int(13.5*RATE),int(96*RATE)
    weights=np.ones(last-first,dtype=np.float32)
    fade=RATE//2
    weights[:fade]=np.linspace(0,1,fade);weights[-fade:]=np.linspace(1,0,fade)
    mix[first:last]=mix[first:last]*(1-weights[:,None])+music[first:last]*weights[:,None]
    timings=[]
    for part,start,end,at,speed in cues:
        data=speech[part][:,int(start*RATE):None if end is None else int(end*RATE)]
        data=tempo(data,speed).T
        fade=min(int(.008*RATE),len(data)//2)
        data[:fade]*=np.linspace(0,1,fade)[:,None]
        data[-fade:]*=np.linspace(1,0,fade)[:,None]
        offset=round(at*RATE); stop=offset+len(data)
        assert first<=offset<stop<=last,(part,start,end,at,len(data)/RATE)
        mix[offset:stop]+=data*.82
        timings.append(dict(part=part,source_start=start,source_end=end,start=at,end=stop/RATE,speed=speed))
    peak=float(np.max(np.abs(mix[first:last])))
    assert peak<1,('Clipping',peak)
    pcm=original_pcm.copy()
    pcm[first:last]=np.rint(mix[first:last]*32768).astype('<i2')
    output=ROOT/'build/audio-ru/track90-ru.wav'
    with wave.open(str(output),'wb') as wav:
        wav.setparams(params);wav.writeframes(pcm.tobytes())
    sf.write(PREVIEW/'intro-ru-preview.wav',pcm[:100*RATE],RATE,subtype='PCM_16')
    assert np.array_equal(pcm[:first],original_pcm[:first])
    assert np.array_equal(pcm[last:],original_pcm[last:])
    report=dict(track=90,voice='Государь',provider='ElevenLabs',
                source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                frames=len(pcm),sample_rate=RATE,modified_seconds=[13.5,96],
                peak=peak,cues=timings,music_separation='Demucs htdemucs',
                limitations='Source separation may leave audible artifacts; preview for listening review.')
    (ROOT/'build/audio-ru/intro-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
