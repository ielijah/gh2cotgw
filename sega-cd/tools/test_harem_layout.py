"""Static regression for the harem's unsigned right-aligned two-line bubble."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
inventory=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
source=(ROOT/'disc'/inventory['image']).read_bytes()
def payload(name):
    f=next(f for f in inventory['files'] if f['path']==name)
    return source[f['lba']*2048:f['lba']*2048+f['size']]
# XXX 389A calls SMAIN 6DC0 with right anchor 24. SMAIN computes
# uint8(left) = uint8(anchor - width - 1), before building the bubble.
assert payload('XXX.PRG;1')[0x3892:0x389a]==bytes.fromhex('4878001348780018')
assert payload('SMAIN.PRG;1')[0x6dd0:0x6dd8]==bytes.fromhex('14059404060200ff')
def width(text): return max((len(line)+1)//2*2 for line in text.split('\n'))
old='Будь я звездой\nвидела бы вас каждую ночь'
assert width(old)==26 and (24-width(old)-1)&255==253
entries=json.loads((ROOT/'translation/harem-screen.json').read_text('utf8'))
manifest=json.loads((ROOT/'build/manifest.json').read_text('utf8'))
for entry in entries:
    assert entry['max_columns']==22 and entry['max_lines']==2
    assert width(entry['ru'])<=22
    assert len(entry['ru'].split('\n'))<=2
    assert 0<=24-width(entry['ru'])-1<24
    applied=next(e for e in manifest['applied'] if e['file']==entry['file'] and e['offset']==entry['offset'])
    assert applied['ru']==entry['ru']
example=next(e for e in entries if e['offset']=='2A6D4')
report=dict(dialogues=len(entries),max_columns=22,max_lines=2,old_left_column_wrapped=253,new_example_left_column=24-width(example['ru'])-1,example=example['ru'],emulator_run=False,scope='Static bounds and build correspondence; no visual emulator verification')
(ROOT/'analysis/harem-layout-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS: native anchor assertions, reproduced old underflow, all 80 harem dialogue bounds')
