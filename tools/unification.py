"""Local grammar for the Mongolian unification epilogue."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
CODE=0x128000
LOOKUP=0x128100
TEXT=0x128200
SEASONS=0x128380
COUNTRIES=0x128400
NAMES=0x128800
STRINGS=0x129000
def apply(rom,src,encode,assembler):
    rom.extend(bytes(max(0,0x12b000-len(rom))))
    text='\x1bCE\x1bB0%s %4d года\nвраждующие племена\nстепей Монголии были\nобъединены\n%s\nиз %s.'
    data=encode(text)+b'\0';assert len(data)<SEASONS-TEXT
    rom[TEXT:TEXT+len(data)]=data
    for i,s in enumerate(('Весной','Летом','Осенью','Зимой')):
        data=encode(s)+b'\0';rom[SEASONS+i*7:SEASONS+i*7+7]=data.ljust(7,b'\0')
    cursor=STRINGS
    for file,table,limit in [('envoy-country-forms.json',COUNTRIES,NAMES),('unification-names.json',NAMES,STRINGS)]:
        forms=json.loads((ROOT/'translation'/file).read_text(encoding='utf-8'))
        assert table+len(forms)*8+4<=limit
        for i,(nom,case) in enumerate(forms.items()):
            for j,s in enumerate((nom,case)):
                data=encode(s)+b'\0';rom[table+i*8+j*4:table+i*8+j*4+4]=cursor.to_bytes(4,'big')
                rom[cursor:cursor+len(data)]=data;cursor+=len(data)
        rom[table+len(forms)*8:table+len(forms)*8+4]=bytes(4)
    assert cursor<=len(rom)
    c=assembler(LOOKUP)
    c.emit('2248') # A1 keeps the input; A0 is the result, A2 walks the table.
    c.label('next');c.emit('265a200b');c.branch('67','done')
    c.emit('2049')
    c.label('cmp');c.emit('1018b01b');c.branch('66','skip')
    c.emit('4a00');c.branch('66','cmp')
    c.emit('2052');c.emit('4e75')
    c.label('skip');c.emit('588a');c.branch('60','next')
    c.label('done');c.emit('20494e75')
    data=c.finish();assert LOOKUP+len(data)<TEXT;rom[LOOKUP:LOOKUP+len(data)]=data
    c=assembler(CODE);c.emit('48e780f0') # D0/A0-A3, 20 bytes.
    c.emit('206f0024247c'+f'{NAMES:08x}'+'4eb9'+f'{LOOKUP:08x}'+'2f480024')
    c.emit('206f0028247c'+f'{COUNTRIES:08x}'+'4eb9'+f'{LOOKUP:08x}'+'2f480028')
    c.emit('4cdf0f01');c.jump(0x61b8)
    data=c.finish();assert CODE+len(data)<LOOKUP;rom[CODE:CODE+len(data)]=data
    for off,old,new in [(0x28346,0x4bb70,TEXT),(0x2833c,0x4bbce,SEASONS)]:
        assert int.from_bytes(src[off:off+4],'big')==old
        rom[off:off+4]=new.to_bytes(4,'big')
    assert src[0x2834a:0x28350]==bytes.fromhex('4eb9000061b8')
    rom[0x2834a:0x28350]=bytes.fromhex('4eb9')+CODE.to_bytes(4,'big')
    # Six explicit lines; move the window two rows up and add two rows.
    for off,old,new in [(0x282d2,12,14),(0x282da,14,12),(0x282e8,15,13)]:
        assert int.from_bytes(src[off:off+2],'big')==old
        rom[off:off+2]=new.to_bytes(2,'big')
    rom[0x1a4:0x1a8]=(len(rom)-1).to_bytes(4,'big')
