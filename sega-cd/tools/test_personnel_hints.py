"""Check the six personnel hints that share one appended ending."""
from pathlib import Path
import json, struct, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from text_encoding import encode
inventory = json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf-8'))
source = (ROOT/'disc'/inventory['image']).read_bytes()
f = next(x for x in inventory['files'] if x['path']=='SMAIN.PRG;1')
original = source[f['lba']*2048:][:f['size']]
# Six pointer-table choices feed the same text builder, followed by the suffix.
offsets = [0x285b0,0x2859e,0x2858e,0x28578,0x28562,0x2854c]
assert struct.unpack('>6I',original[0x4cbe8:0x4cc00]) == tuple(o+0xc000 for o in offsets)
assert original[0x18576:0x18582] == bytes.fromhex('4879000345c24eb900011ade')
m = json.loads((ROOT/'build/manifest.json').read_text('utf-8'))
entries = {int(x['offset'],16):x for x in m['applied'] if x['file']=='SMAIN.PRG;1'}
pairs = {k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
reverse = {v:k for k,v in pairs.items()}
def decode(raw):
    result='';i=0
    while i<len(raw):
        if raw[i]>=0xf0:
            result+=reverse[raw[i:i+2]];i+=2
        else:
            result+=chr(raw[i]);i+=1
    return result
suffix=entries[0x285c2]['ru']
assert suffix=='?'
for offset in offsets:
    text=entries[offset]['ru']
    raw=encode(text,pairs)+encode(suffix,pairs)
    actual=decode(raw).rstrip()
    assert actual==text+'?',(offset,actual)
    assert actual.count('?')==1 and ' ?' not in actual
    assert len(actual)<=22
print('PASS: all 6 personnel hints use the original shared suffix; one question mark, no inserted gap, <=22 columns')
