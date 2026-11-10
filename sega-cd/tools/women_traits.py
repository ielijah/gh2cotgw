"""Separate gameplay inheritance from history in the wives' catalogue cards."""
from pathlib import Path
import json, struct, textwrap
ROOT=Path(__file__).resolve().parents[1]

def texts():
    rows=json.loads((ROOT/'analysis/women-biographies-research.json').read_text('utf8'))
    result=[]
    for r in rows:
        # Only the original inheritance clause; not later historical prose.
        first=r['ja'].split('産')[0]
        traits=[ru for ja,ru in [('政治力','политики'),('戦闘力','воины'),('指揮力','лидеры')] if ja in first]
        charisma='魅力' in first
        text=('Дети: '+', '.join(traits)+(' с харизмой' if charisma else '')) if traits else ('Дети с харизмой' if charisma else 'Дети: не указано')
        lines=textwrap.wrap(text,18,break_long_words=False)
        assert len(lines)<=3 and sum((len(x)+1)//2*2 for x in lines)<=64
        result.append('\n'.join(lines))
    return result

def apply(image,source,files,bank,order,encode):
    base=files['INIT.PRG;1']['lba']*2048
    pos=(bank['start']+bank['used']+1)&~1
    table=pos;pos+=84*4
    pointers=[];records=[]
    for text in texts():
        raw=encode(text)+b'\0';pointers.append(0x66000+pos)
        image[base+pos:base+pos+len(raw)]=raw
        records.append(dict(offset=pos,length=len(raw),text=text));pos+=len(raw)
    for dest,old in enumerate(order):struct.pack_into('>I',image,base+table+dest*4,pointers[old])
    pos=(pos+1)&~1;helper=pos
    # Original biography call, followed by an independent glyph pool for traits.
    code=bytes.fromhex('48e7fffe700030022f00487800024eb900068d7c508f')
    # Catalogue font base is tile A0. Body ends at 1FF; portrait uses
    # 200..237. Traits use 240..2BF, below the catalogue frame graphics.
    code+=bytes.fromhex('4878010f487800d04eb9000106e2508f')
    code+=bytes.fromhex('487800064878000b4eb90001047c508f')
    code+=bytes.fromhex('70003002e588207c')+struct.pack('>I',0x66000+table)
    code+=bytes.fromhex('33fc000b00059f4c2f3008004eb900010af8588f33fc000200059f4c4cdf7fff4e75')
    assert pos+len(code)<=bank['end']
    image[base+pos:base+pos+len(code)]=code;pos+=len(code)
    changes=[(0x318e,'30022f00487800026100fbe4','4eb9'+struct.pack('>I',0x66000+helper).hex()+'4e714e714e71'),(0x31a6,'0030','0028')]
    for off,old,new in changes:
        assert source[base+off:base+off+len(bytes.fromhex(old))]==bytes.fromhex(old)
        image[base+off:base+off+len(bytes.fromhex(new))]=bytes.fromhex(new)
    return dict(table=table,records=records,helper=helper,code=code.hex(),end=pos,free=bank['end']-pos,patches=changes,
                x=11,y=6,columns=18,lines=3,glyph_first=0xd0,glyph_last=0x10f)
