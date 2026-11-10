"""Bound list names; give full biography names a separate sixteen-cell pool."""
import struct

CARD_COLUMNS=16
CARD_SOURCE=0x3073b0

def card_map(columns):
 rows=[(0xe2d4,0xe2d5,0xe2d6),(0xe2d7,0xe2d8,0xe2d9),
       (0xe2d7,0xe2d8,0xe2d9),(0xe2da,0xe2db,0xe2dc)]
 values=[v for left,middle,right in rows for v in [left]+[middle]*columns+[right]]
 return struct.pack('>'+str(len(values))+'H',*values)

def allocate(reserve,put,Code):
 a=reserve(96,'catalog_list_name');c=Code()
 c.emit('48e7c0c04feffff0206f0028700a')
 c.label('scan');c.emit('4a18');c.branch('67','short')
 # DBRA D0,scan, encoded separately because Code.branch expects byte branches.
 pos=len(c.data);c.emit('51c80000');struct.pack_into('>h',c.data,pos+2,c.labels['scan']-(pos+2))
 c.emit('206f00282e902f68000400043f7c2e2e0008422f000a41d7');c.branch('60','print')
 c.label('short');c.emit('206f0028')
 c.label('print');c.emit('2f082f2f00284eb9000110344fef00184cdf03034e75')
 code=c.finish();assert len(code)<=96;put(a,code)
 frame=reserve(len(card_map(CARD_COLUMNS)),'catalog_card_frame')
 put(frame,card_map(CARD_COLUMNS))
 return dict(helper=a,size=len(code),columns=10,card_frame=frame,
             card_columns=CARD_COLUMNS,card_width=CARD_COLUMNS+2,
             card_rows=4,card_glyph_tiles=CARD_COLUMNS*2)

def patches(data):
 return [('INIT.PRG;1',0x32c4,'4eb900011034','4eb9'+struct.pack('>I',0xc000+data['helper']).hex()),
         ('INIT.PRG;1',0x2aba,'000943b0',struct.pack('>I',0xc000+data['card_frame']).hex()),
         ('INIT.PRG;1',0x2ac4,'000c','0012'),
         # Native cyclic glyph pool: the old 0..9 range overwrote the first
         # pair when the sixth Cyrillic pair was drawn. Reserve 0..15 instead.
         ('INIT.PRG;1',0x2c54,'0009','000f'),
         # Biography body must start AFTER the enlarged header glyph pool.
         ('INIT.PRG;1',0x2db0,'000a','0010')]

def apply(image,source,files,data):
 a=files['GH2GRP.DAT;1']['lba']*2048+CARD_SOURCE
 assert source[a:a+len(card_map(10))]==card_map(10)
 for file,off,old,new in patches(data):
  a=files[file]['lba']*2048+off;before=bytes.fromhex(old);after=bytes.fromhex(new)
  assert source[a:a+len(before)]==before;image[a:a+len(after)]=after
