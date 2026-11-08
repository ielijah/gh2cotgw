"""Full contextual command phrases, without English word-order fragments."""
TABLE=0x12aa40
QUESTIONS=0x12ae00
CODE=0x12ac00
TEXT=0x12ad00
STATEMENTS=['Отдать приказ атаки','Перемещение войск','Приказ посылки','Отдать дипломатический приказ']
PROMPTS=['Дать приказ атаки какой земле?','Откуда переместить?','Откуда высылаем?','Дать дипломатический приказ какой земле?']

def apply(rom,src,encode,assembler):
    for table,start,stride,phrases in [(TABLE,0x12aa60,32,STATEMENTS),(QUESTIONS,0x12ae20,64,PROMPTS)]:
        for i,phrase in enumerate(phrases):
            addr=start+i*stride;raw=encode(phrase)+b'\0';assert len(raw)<=stride
            rom[addr:addr+len(raw)]=raw
            rom[table+i*4:table+i*4+4]=addr.to_bytes(4,'big')
    for ref,table in [(0x29364,QUESTIONS),(0x298dc,TABLE)]:
        assert src[ref:ref+4]==bytes.fromhex('0004be80')
        rom[ref:ref+4]=table.to_bytes(4,'big')
    c=assembler(CODE);c.emit('2f08206f0008')
    choices=[(0x3cece,'Мы атакуем'),(0x3b792,'Мы атакуем'),(0x3cee2,'Пересылаем золото'),(0x3ceec,'Пересылаем продовольствие'),(0x3ced6,'Перемещаем войска')]
    for i,(source,phrase) in enumerate(choices):
        target=TEXT+i*32;raw=encode(phrase)+b'\0';assert len(raw)<=32;rom[target:target+len(raw)]=raw
        c.emit('b1fc'+f'{source:08x}');c.branch('66','next'+str(i))
        c.emit('205f4879'+f'{target:08x}'+'4eb900006c22588f4e75')
        c.label('next'+str(i))
    c.emit('205f');c.jump(0x6c3a)
    raw=c.finish();assert CODE+len(raw)<TEXT;rom[CODE:CODE+len(raw)]=raw
    assert src[0xc59a:0xc5a0]==bytes.fromhex('4eb900006c3a')
    rom[0xc59a:0xc5a0]=bytes.fromhex('4eb9')+CODE.to_bytes(4,'big')
