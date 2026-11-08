"""Expand the saved season and normalize display-only spacing."""
CODE=0x12a400
DATA=0x12a600

def apply(rom,src,encode,assembler):
    c=assembler(CODE)
    c.emit('4e56ffb048e7c0f0206e000843eeffb0')
    for i,(short,full) in enumerate([('Вес','Весна'),('Лет','Лето'),('Осн','Осень'),('Зим','Зима'),('Ос.','Осень')]):
        raw=encode(short)
        c.emit('0c1000'+raw[:1].hex());c.branch('66','next'+str(i))
        c.emit('0c2800'+raw[1:2].hex()+'0001');c.branch('66','next'+str(i))
        c.emit('0c2800'+raw[2:].hex()+'0002');c.branch('66','next'+str(i))
        off=DATA+i*8;b=encode(full)+b'\0';rom[off:off+len(b)]=b
        c.emit('54885288247c'+f'{off:08x}')
        c.label('copy'+str(i));c.emit('101a');c.branch('67','season_done')
        c.emit('12c0');c.branch('60','copy'+str(i))
        c.label('next'+str(i))
    c.emit('7200');c.branch('60','loop')
    c.label('season_done');c.emit('12fc00207201')
    c.label('loop');c.emit('1018');c.branch('67','end')
    c.emit('0c000020');c.branch('66','letter')
    c.emit('4a01');c.branch('66','loop')
    c.emit('7201');c.branch('60','write')
    c.label('letter');c.emit('7200')
    c.label('write');c.emit('12c0');c.branch('60','loop')
    c.label('end');c.emit('4a01');c.branch('67','terminate')
    c.emit('5389')
    c.label('terminate');c.emit('4211486effb04eb900006c3a588f4cdf0f034e5e4e75')
    b=c.finish();assert CODE+len(b)<DATA
    rom[CODE:CODE+len(b)]=b
    assert src[0x268c6:0x268cc]==bytes.fromhex('4eb900006c3a')
    rom[0x268c6:0x268cc]=bytes.fromhex('4eb9')+CODE.to_bytes(4,'big')
