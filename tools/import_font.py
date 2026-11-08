"""Extract both Russian faces from the user-provided translation ROM."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
REFERENCE_SHA='593ab1fef1f30ac3bf13a75be211f4536a765f24404fb1bfb92cdad81084161d'
UPPER={**dict(zip('АБВГДЕЖЗИ',range(0x41,0x4a))),**dict(zip('КЛМНОПРСТУФХЦЧШЩ',range(0x4a,0x5a))),'Э':0x5a,'Ю':0x5f,'Я':0x60}
LOWER={**dict(zip('абвгдежзи',range(0x61,0x6a))),**dict(zip('клмнопрстуфхцчшщ',range(0x6a,0x7a))),'й':0x27,'ъ':0x29,'ы':0x2a,'ь':0x28,'э':0x7a,'ю':0x2b,'я':0x2f,'ё':0x26}
def extract(reference,face):
    base=0x46244+face*96*16
    result={ch:reference[base+(code-32)*16:base+(code-31)*16] for ch,code in (UPPER|LOWER).items()}
    for ch in 'ЪЫЬ':
        lower=result[ch.lower()]
        result[ch]=bytes(lower[4+y*9//13] for y in range(13))+bytes(3)
    result['Й']=bytes([0x24,0x18])+result['И'][:11]+bytes(3)
    result['Ё']=bytes([0x24,0])+result['Е'][:11]+bytes(3)
    if face == 1:
        # Repair broken scanlines in the donor's thin face; keep 8x16 cells.
        result['й']=bytes([0,0,0x28,0x10,0x44,0x44,0x44,0x44,0x44,0x44,0x44,0x44,0x44,0x3c,0,0])
        result['ы']=bytes([0,0,0,0,0x42,0x42,0x42,0x7a,0x46,0x46,0x46,0x46,0x46,0x7a,0,0])
        result['ю']=bytes([0,0,0,0,0x4c,0x52,0x52,0x52,0x72,0x52,0x52,0x52,0x52,0x4c,0,0])
        result['р']=bytes([0,0,0,0,0x5c,0x62,0x42,0x42,0x42,0x42,0x42,0x64,0x58,0x40,0x40,0])
        result['д']=bytes([0,0,0,0,0x1c,0x14,0x14,0x24,0x24,0x24,0x44,0x44,0x7e,0x42,0x42,0])
    return result

ALIASES={35:78,36:73,38:43,42:43,59:58,60:40,61:45,62:41,95:45,96:39}
def pack_static(reference,original):
    """Keep all Russian letters in the stock 192-tile font allocation.

    Deduplicate 8x8 halves, fold remaining Latin text to capitals, and merge
    unused punctuation variants. The original '$' Roman I uses Latin I.
    """
    font=extract(reference,0);tiles=[];lookup={}
    def add(glyph):
        pair=[]
        for half in (glyph[:8],glyph[8:]):
            if half not in lookup:lookup[half]=0x40+len(tiles);tiles.append(half)
            pair.append(lookup[half])
        return pair
    cyr=[add(font[chr(ord('А')+i)]) for i in range(64)]+[add(font['Ё']),add(font['ё'])]
    latin=[]
    for i in range(192):
        ch=i%96+32
        if 97<=ch<=122:ch-=32
        ch=ALIASES.get(ch,ch)
        if ch>126:ch=32
        latin.append(add(original[0x46244+(ch-32)*16:0x46254+(ch-32)*16]))
    assert len(tiles)<=192, len(tiles)
    tiles+= [bytes(8)]*(192-len(tiles))
    packed=bytes(sum((15 if row&(128>>x) else 0)<<(4 if x%2==0 else 0) for x in (pair,pair+1)) for tile in tiles for row in tile for pair in range(0,8,2))
    return font,extract(reference,1),packed,latin,cyr
if __name__=='__main__':
    reference=next((ROOT/'rom/reference').glob('*.md')).read_bytes()
    assert hashlib.sha256(reference).hexdigest()==REFERENCE_SHA
    original=(ROOT/'rom/original.gen').read_bytes()
    font=extract(reference,0)
    alphabet=''.join(chr(ord('А')+i) for i in range(64))+'Ёё'
    cyr=b''.join(font[ch] for ch in alphabet)
    (ROOT/'translation/reference-cyrillic.bin').write_bytes(cyr)
    alternate=extract(reference,1)
    (ROOT/'translation/reference-cyrillic-alt.bin').write_bytes(b''.join(alternate[ch] for ch in alphabet))
    for mode in ('all','upper','lower'):
        glyphs=[original[0x46244+(c-32)*16:0x46254+(c-32)*16] for c in range(32,127) if mode=='all' or (not 97<=c<=122 if mode=='upper' else not 65<=c<=90)]
        glyphs+=list(font.values())
        tiles=set(glyph[i:i+8] for glyph in glyphs for i in (0,8))
        print(mode,len(tiles),'tiles')
    (ROOT/'analysis/font-provenance.json').write_text(json.dumps(dict(source_sha256=REFERENCE_SHA,bank_offset='046244',alternate_bank_offset='046844',original_codes={ch:f'{code:02X}' for ch,code in (UPPER|LOWER).items()},derived_uppercase=['Й','Ё','Ъ','Ы','Ь'],repaired_alternate=['й','ы','ю','р','д']),ensure_ascii=False,indent=2),encoding='utf-8')
    _,_,packed,latin,cyr=pack_static(reference,original)
    (ROOT/'analysis/font-layout.json').write_text(json.dumps(dict(permanent_tiles=len(packed)//32,cyrillic_pairs=dict(zip(alphabet,cyr)),latin_pairs=latin,latin_static_case='uppercase',aliases={chr(k):chr(v) for k,v in ALIASES.items()}),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Permanent packed font:',len(packed)//32,'tiles; 66 Russian glyphs')
