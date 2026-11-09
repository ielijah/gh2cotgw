"""Read-only ISO9660 inventory and source-track verification; no disc data exported."""
from pathlib import Path
import hashlib, json, re, wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis'
OUT.mkdir(exist_ok=True)
images = list((ROOT / 'disc').glob('*.iso'))
assert len(images) == 1, 'Expected exactly one source ISO'
data = images[0].read_bytes()
assert len(data) % 2048 == 0
pvd = data[16*2048:17*2048]
assert pvd[:7] == b'\x01CD001\x01', 'Expected ISO9660 primary descriptor'

def record(buf):
    length = buf[32]
    return dict(lba=int.from_bytes(buf[2:6], 'little'), size=int.from_bytes(buf[10:14], 'little'),
                directory=bool(buf[25]&2), name=buf[33:33+length].decode('ascii', errors='replace'))

files = []
seen = set()
def walk(directory, prefix=''):
    key = (directory['lba'], directory['size'])
    assert key not in seen, 'Directory cycle'
    seen.add(key)
    start = directory['lba']*2048
    end = start+directory['size']
    assert end <= len(data)
    pos = start
    while pos < end:
        n = data[pos]
        if not n:
            pos = (pos//2048+1)*2048
            continue
        assert n >= 34 and pos+n <= end
        item = record(data[pos:pos+n]); pos += n
        if item['name'] in ('\x00','\x01'): continue
        item['path'] = prefix+item.pop('name')
        assert item['lba']*2048+item['size'] <= len(data)
        if item['directory']: walk(item, item['path']+'/')
        else:
            payload = data[item['lba']*2048:item['lba']*2048+item['size']]
            item['sha256'] = hashlib.sha256(payload).hexdigest()
            files.append(item)
walk(record(pvd[156:]))
tracks = []
for path in sorted((ROOT/'disc').glob('*')):
    if not path.is_file(): continue
    item = dict(name=path.name, size=path.stat().st_size)
    with path.open('rb') as stream: item['sha256'] = hashlib.file_digest(stream,'sha256').hexdigest()
    if path.suffix.lower()=='.wav':
        with wave.open(str(path),'rb') as audio:
            item.update(channels=audio.getnchannels(), sample_width=audio.getsampwidth(),
                        sample_rate=audio.getframerate(), frames=audio.getnframes())
            assert (item['channels'],item['sample_width'],item['sample_rate'])==(2,2,44100)
    tracks.append(item)
cues = list((ROOT/'disc').glob('*.cue'))
assert len(cues)==1
cue = cues[0].read_text(encoding='utf-8-sig')
references = re.findall(r'^FILE "([^"]+)"',cue,re.M)
assert len(references)==90 and len(set(references))==90
assert all((ROOT/'disc'/name).is_file() for name in references)
report = dict(image=images[0].name, sha256=hashlib.sha256(data).hexdigest(), size=len(data),
              boot_signature=data[:16].decode('ascii',errors='replace'),
              volume=pvd[40:72].decode('ascii').strip(), files=files, tracks=tracks,
              cue_track_count=len(references))
(OUT/'disc-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(f"PASS: {len(data)//2048} ISO sectors; {len(files)} files; 90 CUE tracks present; WAV format checked")
for item in files: print(f"{item['lba']:5} {item['size']:8} {item['path']}")
