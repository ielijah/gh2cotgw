"""Build flat CUE packages: every FILE resolves independently in Genesis Plus GX."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, wave
ROOT=Path(__file__).resolve().parents[1]

def package(mode):
    inventory=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
    source_cue=next((ROOT/'disc').glob('*.cue')).read_text('utf-8-sig')
    output=ROOT/'build'/('playable-'+mode)
    output.mkdir(exist_ok=True)
    records=[]; number=0
    def replace(match):
        nonlocal number
        number+=1
        original=ROOT/'disc'/match[1]
        source=original
        if number==1 and mode!='original': source=ROOT/'build/genchou-hishi-ru-experimental.iso'
        if (2<=number<=79 or number==90) and mode=='dub': source=ROOT/f'build/audio-ru/track{number:02}-ru.wav'
        target=output/f'track{number:02}{source.suffix.lower()}'
        assert source.is_file(),source
        shutil.copyfile(source,target)
        if number>1:
            with wave.open(str(target)) as audio:
                assert (audio.getnchannels(),audio.getsampwidth(),audio.getframerate())==(2,2,44100)
                assert audio.getnframes()%588==0
        with target.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        records.append(dict(track=number,file=target.name,sha256=digest))
        return f'FILE "{target.name}" {match[2]}'
    cue=re.sub(r'FILE "([^"]+)" (\w+)',replace,source_cue)
    assert number==90
    cue_path=output/'game.cue';cue_path.write_text(cue,encoding='ascii')
    # Model the emulator's FILE path handling, which reuses the previous directory.
    previous=cue_path
    for filename in re.findall(r'FILE "([^"]+)"',cue):
        previous=previous.parent/filename
        assert previous.is_file(),previous
        assert previous.parent==output
        assert len(str(previous).encode())<255, 'Move repository to a shorter path'
    (output/'tracks.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
    print(f'PASS: {mode}, all 90 tracks resolve: {cue_path}')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['original','japanese-audio','dub'])
    package(parser.parse_args().mode)
