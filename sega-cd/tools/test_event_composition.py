"""Validate shared confirmation and alliance composition against original call sites."""
from pathlib import Path
import json, struct, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from text_encoding import encode
ROOT=Path(__file__).resolve().parents[1]
i=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
s=(ROOT/'disc'/i['image']).read_bytes()
f=next(x for x in i['files'] if x['path']=='SMAIN.PRG;1')
b=s[f['lba']*2048:][:f['size']]
m=json.loads((ROOT/'build/manifest.json').read_text('utf8'))
e={int(x['offset'],16):x for x in m['applied'] if x['file']=='SMAIN.PRG;1'}
pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
reverse={v:k for k,v in pairs.items()}
def decode(raw):
    result='';p=0
    while p<len(raw):
        if raw[p]>=0xf0:result+=reverse[raw[p:p+2]];p+=2
        else:result+=chr(raw[p]);p+=1
    return result
# Shared confirmation: copy the supplied prompt, append 26FEC, show yes/no.
assert b[0xd428:0xd43e]==bytes.fromhex('2f2e00084eb900011ac6487900032fec4eb900011ade')
suffix=e[0x26fec]['ru']
for offset in [0x29630,0x29648,0x29662,0x2967c,0x29690]:
    prompt=e[offset]['ru']
    assert prompt.endswith('\n')
    actual=decode(encode(prompt,pairs)+encode(suffix,pairs)).rstrip()
    assert actual.count('?')==1 and ' ?' not in actual
    assert len(actual.splitlines())==2
    assert max(map(len,actual.splitlines()))<=22
# Original alliance outcome table, selected after a country name.
offsets=[0x28d9e,0x28d8a,0x28d72,0x28d5e]
assert struct.unpack_from('>4I',b,0x4d1ec)==tuple(x+0xc000 for x in offsets)
assert b[0x1cf32:0x1cf3e]==bytes.fromhex('207c000591ec2f3000004e94')
for offset in offsets+[0x28cd4,0x28d12,0x28d46]:
    suffix=e[offset]['ru'];assert suffix.startswith('\n')
    for country in ['Монголы','Киевская Русь','Монгольская империя']:
        actual=decode(encode(country,pairs)+encode(suffix,pairs)).rstrip()
        assert len(actual.splitlines())==2
        assert max(map(len,actual.splitlines()))<=22
print('PASS: five policy prompts and seven country outcomes compose in two lines; original call sites and pointer table verified')
