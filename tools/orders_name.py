"""Trim legacy save-name padding only in the ruler's orders prompt."""
CODE=0x12a700

def apply(rom,src,encode,assembler):
    c=assembler(CODE)
    c.emit('4e56fff048e780e0206e000843eefff02449700b')
    c.label('copy');c.emit('1218');c.branch('67','end')
    c.emit('12c10c010020');c.branch('67','space')
    c.emit('2449')
    c.label('space');c.emit('5340');c.branch('6a','copy')
    c.label('end');c.emit('42122f2e000c486efff04eb90000db9e508f4cdf07014e5e4e75')
    b=c.finish();assert CODE+len(b)<0x12a800
    rom[CODE:CODE+len(b)]=b
    assert src[0xa482:0xa488]==bytes.fromhex('4eb90000db9e')
    rom[0xa482:0xa488]=bytes.fromhex('4eb9')+CODE.to_bytes(4,'big')

    # Only the appointment question needs accusative role labels.
    table=0x12a800
    for i,role in enumerate(['полководца','советника','наместника','правителя']):
        addr=0x12a820+i*0x20
        rom[table+i*4:table+i*4+4]=addr.to_bytes(4,'big')
        raw=encode(role)+b'\0';rom[addr:addr+len(raw)]=raw
    assert src[0x2363c:0x23640]==bytes.fromhex('0004a4fa')
    rom[0x2363c:0x23640]=table.to_bytes(4,'big')
