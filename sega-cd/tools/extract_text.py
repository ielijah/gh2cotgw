"""Extract unreviewed null-terminated Shift-JIS candidates from executable files."""
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parents[1]
inventory=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
source=(ROOT/'disc'/inventory['image']).read_bytes()
entries=[]
for item in inventory['files']:
    if not item['path'].endswith('.PRG;1'): continue
    blob=source[item['lba']*2048:item['lba']*2048+item['size']]
    for match in re.finditer(rb'[^\x00]{3,}\x00',blob):
        raw=match.group()[:-1]
        # Reject most machine code; keep only the observed newline/ESC controls.
        if any(value<32 and value not in (10,13,27) for value in raw): continue
        try: text=raw.decode('shift_jis')
        except UnicodeDecodeError: continue
        visible=re.sub('\x1b[A-Z]','',text).replace('\n','').replace('\r','')
        japanese=sum('\u3040'<=ch<='\u30ff' or '\u4e00'<=ch<='\u9fff' or '\uff61'<=ch<='\uff9f' for ch in visible)
        if japanese<2 or japanese/max(1,len(visible))<0.3: continue
        # Source-code and graphic bytes can still accidentally decode. These
        # entries are candidates, never automatically accepted as text slots.
        entries.append(dict(file=item['path'], offset=f'{match.start():X}',
                            capacity=len(raw), ja=text, ru='', status='unreviewed',
                            format_tokens=re.findall(r'%(?:[-+0 #]|\d|\.)*[a-zA-Z]',text)))
(ROOT/'translation/candidates.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(f'{len(entries)} unreviewed Shift-JIS candidates; this is not a coverage estimate')
