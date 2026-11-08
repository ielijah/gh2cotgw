"""List untranslated printable candidates in a selected ROM interval."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
b=(ROOT/'rom/original.gen').read_bytes()
done=json.loads((ROOT/'translation/reviewed.json').read_text(encoding='utf-8'))
for p in (ROOT/'translation').glob('batch-*.json'): done.update(json.loads(p.read_text(encoding='utf-8')))
start=int(sys.argv[1],16);end=int(sys.argv[2],16)
for m in re.finditer(rb'[ -~]{4,}',b[start:end]):
    text=m.group().decode('ascii')
    if text not in done and re.search('[A-Za-z]{3}',text): print(f'{start+m.start():06X} {text!r}')
