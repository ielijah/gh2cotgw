"""Use accusative country names only in the player-side confirmation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREFIX=0x106200
CODE=0x106240
TABLE=0x106400
STRINGS=0x106800

def apply(rom,src,encode,assembler):
    forms=json.loads((ROOT/'translation/play-country-forms.json').read_text(encoding='utf-8'))
    countries=json.loads((ROOT/'translation/fields.json').read_text(encoding='utf-8'))['countries']
    assert set(forms)==set(countries.values())
    prefix=encode('Играть за ')+b'\0'
    rom[PREFIX:PREFIX+len(prefix)]=prefix
    assert src[0x2611c:0x26120]==(0x3b312).to_bytes(4,'big')
    rom[0x2611c:0x26120]=PREFIX.to_bytes(4,'big')
    cursor=STRINGS
    for i,(nom,acc) in enumerate(forms.items()):
        # Original local string buffer is 36 bytes, before the selection flags.
        assert len(encode('Играть за '+acc+'?'))+1<=36
        for j,text in enumerate((nom,acc)):
            data=encode(text)+b'\0'
            rom[TABLE+i*8+j*4:TABLE+i*8+j*4+4]=cursor.to_bytes(4,'big')
            rom[cursor:cursor+len(data)]=data;cursor+=len(data)
    assert TABLE+len(forms)*8+4<=STRINGS and cursor<=0x108000
    rom[TABLE+len(forms)*8:TABLE+len(forms)*8+4]=bytes(4)
    c=assembler(CODE)
    c.emit('48e7e0f0') # Save D0-D2/A0-A3: source argument is now SP+36.
    c.emit('247c'+f'{TABLE:08x}')
    c.label('next');c.emit('225a2009');c.branch('67','done')
    c.emit('206f0024')
    c.label('compare');c.emit('1018b019');c.branch('66','skip')
    c.emit('4a00');c.branch('66','compare')
    c.emit('2f520024');c.branch('60','done')
    c.label('skip');c.emit('588a');c.branch('60','next')
    c.label('done');c.emit('4cdf0f07');c.jump(0x5302)
    data=c.finish();assert CODE+len(data)<=TABLE
    rom[CODE:CODE+len(data)]=data
    assert src[0x26132:0x26138]==bytes.fromhex('4eb900005302')
    rom[0x26132:0x26138]=bytes.fromhex('4eb9')+CODE.to_bytes(4,'big')
