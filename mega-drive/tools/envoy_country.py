"""Genitive country forms in the incoming-envoy announcement only."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
CODE,TABLE,STRINGS=0x107000,0x107100,0x107300

def apply(rom,src,encode,assembler):
    forms=json.loads((ROOT/'translation/envoy-country-forms.json').read_text(encoding='utf-8'))
    countries=json.loads((ROOT/'translation/fields.json').read_text(encoding='utf-8'))['countries']
    assert set(forms)==set(countries.values())
    cursor=STRINGS
    for i,(nom,gen) in enumerate(forms.items()):
        assert len(encode('Прибыл посол от '+gen))+1<=64
        for j,text in enumerate((nom,gen)):
            data=encode(text)+b'\0'
            rom[TABLE+i*8+j*4:TABLE+i*8+j*4+4]=cursor.to_bytes(4,'big')
            rom[cursor:cursor+len(data)]=data;cursor+=len(data)
    assert TABLE+len(forms)*8+4<=STRINGS and cursor<=0x107f00
    rom[TABLE+len(forms)*8:TABLE+len(forms)*8+4]=bytes(4)
    c=assembler(CODE)
    c.emit('48e7e0f0')
    c.emit('247c'+f'{TABLE:08x}')
    c.label('next');c.emit('225a2009');c.branch('67','done')
    c.emit('206f0020') # One argument: source at SP+32 after register save.
    c.label('compare');c.emit('1018b019');c.branch('66','skip')
    c.emit('4a00');c.branch('66','compare')
    c.emit('2f520020');c.branch('60','done')
    c.label('skip');c.emit('588a');c.branch('60','next')
    c.label('done');c.emit('4cdf0f07');c.jump(0x6c3a)
    data=c.finish();assert CODE+len(data)<=TABLE
    rom[CODE:CODE+len(data)]=data
    assert src[0x2fa0e:0x2fa14]==bytes.fromhex('4eb900006c3a')
    rom[0x2fa0e:0x2fa14]=bytes.fromhex('4eb9')+CODE.to_bytes(4,'big')
