"""Native colour/printf stream and calendar width regression."""
from pathlib import Path
import sys,json,re
sys.path.insert(0,str(Path(__file__).resolve().parent))
from text_encoding import encode_stream, encode, stream_tokens
r=Path(__file__).resolve().parents[1]
m=json.loads((r/'build/manifest.json').read_text('utf8'))
pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
reverse={v:k for k,v in pairs.items()}
def decode(data):
    result='';i=0
    while i<len(data):
        if data[i]==27:
            assert data[i+1] in (ord('C'),ord('B'));i+=3
        elif data[i]>=0xf0:result+=reverse[data[i:i+2]];i+=2
        else:result+=chr(data[i]);i+=1
    return result
entries={e['offset']:e for e in m['applied'] if e['file']=='SMAIN.PRG;1'}
date=encode_stream(entries['26510']['ru'],pairs)
price=encode_stream(entries['264FE']['ru'],pairs)
assert stream_tokens(entries['26510']['ru'])==stream_tokens(entries['26510']['ja'])
seasons=[e for e in m['text_compositor']['relocated_texts'] if e.get('kind')=='season']
assert {e['ru'] for e in seasons}=={' Вес',' Лет',' Осн',' Зим'}
for e in seasons:
    actual=decode(date % (1184,encode(e['ru'],pairs)))
    assert actual=='1184'+e['ru'] and len(actual)==8,actual
    # Text starts at x=176; the last half-width cell ends at x=240,
    # before the right frame at x=244. The old padded variant ended at x=248.
    assert 176+len(actual)*8==240
for whole,fraction in [(0,0),(1,0),(9,9),(99,9)]:
    actual=decode(price % (whole,fraction))
    assert actual==('\nЦена%2d.%d' % (whole,fraction))
print('PASS: all four seasons use exactly eight date cells; colour tokens and numeric price substitutions preserved')
