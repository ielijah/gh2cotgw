"""Check decimal substitutions and compatibility of all existing plain strings."""
from pathlib import Path
import json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from text_encoding import encode,decimal_tokens,NATIVE

r=Path(__file__).resolve().parents[1]
m=json.loads((r/'build/manifest.json').read_text('utf8'))
pairs={k:bytes.fromhex(v) for k,v in m['paired_glyphs'].items()}
reverse={v:k for k,v in pairs.items()}

def decode(data):
    out=[];i=0
    while i<len(data):
        if data[i]>=0xf0:
            out.append(reverse[data[i:i+2]]);i+=2
        else:
            out.append(chr(data[i]));i+=1
    return ''.join(out)

plain=formatted=0
for e in m['applied']:
    if not e.get('native_decimal_format'):
        # The pre-tokenizer encoder, independently reproduced.
        result=[]
        for line in e['ru'].split('\n'):
            line+=' ' if len(line)%2 else ''
            result.append(b''.join(line[i:i+2].encode('ascii') if all(c in NATIVE for c in line[i:i+2])
                                   else pairs[line[i:i+2]] for i in range(0,len(line),2)))
        assert encode(e['ru'],pairs)==b'\n'.join(result)
        plain+=1;continue
    raw=encode(e['ru'],pairs,True)
    tokens=decimal_tokens(e['ru'])
    assert tokens==decimal_tokens(e['ja'])
    assert re.findall(rb'%[0-9]*d',raw)==[t.encode() for t in tokens]
    assert len(raw)<=len(e['ja'].encode('shift_jis'))
    for value in (0,1,9,10,99,100,999):
        args=tuple(value for _ in tokens)
        actual=decode(raw % args)
        expected=e['ru'] % args
        assert [l.rstrip() for l in actual.split('\n')]==[l.rstrip() for l in expected.split('\n')],(e,actual,expected)
        assert max(map(len,actual.split('\n')))<=22,(e,actual)
    formatted+=1
for bad in ('%s','%n','%q','%','%*d'):
    try: decimal_tokens(bad)
    except AssertionError: pass
    else: raise AssertionError(('Unsupported directive accepted',bad))
assert formatted>=13
print(f'PASS: {plain} plain strings match pair encoding;  {formatted} decimal templates preserve tokens and exact internal spaces, values 0..999 checked')

# Original 68000 ASCII branch maps A..^ by adding D1 to the character byte.
inv=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'))
source=(r/'disc'/inv['image']).read_bytes()
item=next(f for f in inv['files'] if f['path']=='SMAIN.PRG;1')
main=source[item['lba']*2048:item['lba']*2048+item['size']]
assert main[0x4c34:0x4c48]==bytes.fromhex('0c020041650e0c02005e62081602060300d16034')
for numeral in ('I','II','III','IV','V','VIII','IX','X'):
    result=encode(numeral,pairs)
    assert result==(numeral+(' ' if len(numeral)%2 else '')).encode('ascii')
for ch,index in {'I':0x1a,'V':0x27,'X':0x29}.items():
    assert index==(ord(ch)+0xd1)&255
    assert any(main[0x36490+index*16:0x36490+(index+1)*16])
for e in m['applied']:
    if not any(ch in e['ru'] for ch in 'IVX'):
        old=[]
        for line in e['ru'].split('\n'):
            line+=' ' if len(line)%2 else ''
            if e.get('native_decimal_format'):break
            old.append(b''.join(line[i:i+2].encode('ascii') if all(c in '0123456789/ ?,C-!.:;()' for c in line[i:i+2]) else pairs[line[i:i+2]] for i in range(0,len(line),2)))
        else:
            assert encode(e['ru'],pairs)==b'\n'.join(old)
print('PASS: native Roman numerals I/V/X, original ASCII mapping and non-Roman encoding compatibility')
