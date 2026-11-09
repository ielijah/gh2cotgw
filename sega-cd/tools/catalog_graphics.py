"""Translate the three pre-rendered biography categories in their original slots."""
from pathlib import Path
import hashlib,json,sys,struct
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'mega-drive/tools'))
from menu_graphics import render
from koei_decode import decode
from koei_compress import encode
CATEGORIES=[(0x309584,0x98,'Воины'),(0x30961c,0x8c,'Дети'),(0x3096a8,0x60,'Жёны')]

def pixels(caption):
 raw=bytearray(render(bytes([0x99])*256,0xdc,caption.replace('ё','е'),{},b''))
 if 'ё' in caption:
  font=json.loads((ROOT.parent/'mega-drive/translation/menu-font.json').read_text('utf8'));base=caption.replace('ё','е');width=sum(len(font[ch][0]) for ch in base)+len(base)-1;left=max(1,(32-width)//2);i=caption.index('ё');x=left+sum(len(font[ch][0])+1 for ch in base[:i])
  def put(px,py,value):
   off=(py//8*4+px//8)*32+py%8*4+px%8//2;shift=4 if px%2==0 else 0;raw[off]=(raw[off]&~(15<<shift))|(value<<shift)
  for dx in (0,3):
   if x+dx>0:put(x+dx-1,3,15)
   put(x+dx,2,14)
 return bytes(raw)

# The sort-label pointer table starts immediately after the last compressed
# category at 309708, BEFORE the category pointer table at 309728.
SORT=[(0x3090c8,0x96,'Имя'),(0x30915e,0x94,'Полит'),(0x3091f2,0x9c,'Война'),(0x30928e,0x9c,'Лидер'),(0x30932a,0x90,'Хариз')]
FIELDS=SORT+CATEGORIES
LOAD_BASE=0x273000
BANKS=[(0x3090c8,0x3093ba,0x309708,SORT),(0x309584,0x309708,0x309728,CATEGORIES)]

def apply(image,source,files):
 base=files['GH2GRP.DAT;1']['lba']*2048;records=[];ranges=[]
 for start,end,pointers,fields in BANKS:
  packed_bank=bytearray()
  for index,(off,capacity,caption) in enumerate(fields):
   old=source[base+off:base+off+capacity];raw,_=decode(old);assert len(raw)==256
   assert struct.unpack_from('>I',source,base+pointers+index*4)[0]==off-LOAD_BASE
   new=pixels(caption);packed=encode(new);assert decode(packed)[0]==new
   dest=start+len(packed_bank);packed_bank.extend(packed)
   if len(packed_bank)%2:packed_bank.append(0)
   struct.pack_into('>I',image,base+pointers+index*4,dest-LOAD_BASE)
   records.append(dict(offset=off,length=capacity,caption=caption,pointer_offset=pointers+index*4,new_offset=dest,compressed_size=len(packed),source_sha256=hashlib.sha256(old).hexdigest(),raw_sha256=hashlib.sha256(new).hexdigest()))
  assert start+len(packed_bank)<=end
  image[base+start:base+end]=packed_bank+bytes(end-start-len(packed_bank))
  ranges.extend([(start,end-start),(pointers,len(fields)*4)])
 assert image[base+0x30971c:base+0x309728]==source[base+0x30971c:base+0x309728], 'Unused graphic pointers must remain intact'
 return dict(file='GH2GRP.DAT;1',labels=records,ranges=ranges,font_source='mega-drive/translation/menu-font.json')
