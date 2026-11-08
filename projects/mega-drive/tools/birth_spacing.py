"""Remove legacy name padding only in the two childbirth messages."""
TRIM=0x12a900
LORD=0x12a980
MOTHER=0x12a9c0

def apply(rom,src,encode,assembler):
    c=assembler(TRIM)
    c.emit('48e700c0207c00ff2ce82248')
    c.label('scan');c.emit('4a18');c.branch('66','scan')
    c.emit('5388')
    c.label('back');c.emit('b1c9');c.branch('67','done')
    c.emit('0c280020ffff');c.branch('66','done')
    c.emit('4220');c.branch('60','back')
    c.label('done');c.emit('4cdf03004e75')
    raw=c.finish();assert TRIM+len(raw)<LORD
    rom[TRIM:TRIM+len(raw)]=raw
    for code,hook,original in [(LORD,0x22eda,0xdab6),(MOTHER,0x22f16,0x6c22)]:
        # Forward the original argument, preserving the caller's stack layout.
        raw=bytes.fromhex('2f2f00044eb9')+original.to_bytes(4,'big')+bytes.fromhex('588f4eb9')+TRIM.to_bytes(4,'big')+bytes.fromhex('4e75')
        rom[code:code+len(raw)]=raw
        assert src[hook:hook+6]==bytes.fromhex('4eb9')+original.to_bytes(4,'big')
        rom[hook:hook+6]=bytes.fromhex('4eb9')+code.to_bytes(4,'big')
