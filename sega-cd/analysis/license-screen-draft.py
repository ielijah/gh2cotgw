"""Russian license screen using the documented BIOS jump table and original logo."""
import struct,hashlib
from text_compositor import Code
START,END=0x5d4,0x7f0
GLYPHS={
 'П':'7f63636363636300', 'И':'63676f7b73636300',
 'З':'3e63030e03633e00', 'Д':'1e363666667f6300',
 'Л':'1f33336363636300', 'Й':'141c63676b736300',
 'Ё':'14003f303e303f00', 'Ц':'63636363637f0300',
}
LATIN=dict(zip('АВЕКМНОРСТХ','ABEKMHOPCTX'))
LINES=['ПРОИЗВЕДЕНО КОМПАНИЕЙ','SEGA ENTERPRISES ИЛИ ПО ЕЁ ЛИЦЕНЗИИ.']
def patches(source):
 assert source[START:END]==bytes(END-START)
 assert source[0x226:0x22a]==bytes.fromhex('4eb80364')
 mapping={ch:chr(0x61+n) for n,ch in enumerate(GLYPHS)}
 def text(s):return ''.join(mapping.get(ch,LATIN.get(ch,ch)) for ch in s).encode('ascii')
 lines=[b' '*((36-len(s))//2)+text(s) for s in LINES]
 caption=b'\0\0'.join(lines)+b'\xff'
 assert len(caption)<=0x354-0x30e and all(len(s)<=36 for s in LINES)
 q=Code();refs=[]
 def lea(label):
  q.emit('43fa0000');refs.append((len(q.data)-2,label))
 def jsr(addr):q.emit('4eb8'+f'{addr:04x}')
 q.emit('40e72f38fd083f38fd0646fc2700')
 # PC-relative interrupt address; no BIOS-version-specific private routines.
 q.emit('41fa0000');refs.append((len(q.data)-2,'vblank'))
 q.emit('21c8fd0831fc4ef9fd06')
 jsr(0x2ac);jsr(0x2a0);jsr(0x328)
 lea('font');q.emit('203c4c200000223c00011011740'+str(len(GLYPHS)))
 jsr(0x320)
 lea(0x22e);jsr(0x2e4)
 q.emit('203c60000000223c00022022741b');jsr(0x320)
 lea(0x30e);q.emit('203c42040003');jsr(0x31c)
 q.emit('203c479e000372087402363c0100');jsr(0x36c)
 jsr(0x2d8)
 q.emit('3e3c012b');q.label('wait');jsr(0x308)
 pos=len(q.data);q.emit('51cfffff');struct.pack_into('>h',q.data,pos+2,q.labels['wait']-(pos+2))
 q.emit('46fc270031dffd0621dffd0846df4e75')
 q.label('vblank');q.emit('48e7fffe');jsr(0x360);jsr(0x2e8)
 q.emit('4238fe264cdf7fff4e73')
 q.label('font');q.data.extend(b''.join(bytes.fromhex(v) for v in GLYPHS.values()))
 raw=bytearray(q.finish())
 for off,label in refs:
  target=START+q.labels[label] if isinstance(label,str) else label
  struct.pack_into('>h',raw,off,target-(START+off))
 assert START+len(raw)<=END
 return [(0x226,bytes.fromhex('6100')+struct.pack('>h',START-0x228)),(0x30e,caption+bytes(0x354-0x30e-len(caption))),(START,bytes(raw))]
def apply(image,source):
 ranges=[]
 for off,raw in patches(source):
  image[off:off+len(raw)]=raw
  ranges.append(dict(offset=off,length=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 return dict(lines=LINES,font='8x8; original BIOS Latin glyphs and matching Cyrillic',ranges=ranges)
