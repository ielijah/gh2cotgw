"""European success cards: separate ISO resource; original eleven cards retained."""
from pathlib import Path
import struct, zlib, hashlib
from text_compositor import Code
ROOT=Path(__file__).resolve().parents[1]
RESOURCE=b'G2HAREM.DAT;1'
LBA=4723; COUNT=10; SLOT=8192; HOOK=0x400c; HELPER=0x4e10; LOAD=0x66000

def read_png(path):
 data=Path(path).read_bytes(); assert data[:8]==b'\x89PNG\r\n\x1a\n'
 p=8; compressed=b''
 while p<len(data):
  n=int.from_bytes(data[p:p+4],'big');kind=data[p+4:p+8];chunk=data[p+8:p+8+n];p+=12+n
  if kind==b'IHDR': w,h,depth,color,comp,filt,interlace=struct.unpack('>IIBBBBB',chunk)
  if kind==b'IDAT':compressed+=chunk
 assert (w,h,depth,interlace)==(80,160,8,0) and color in (2,6)
 channels=3 if color==2 else 4
 raw=zlib.decompress(compressed);stride=w*channels;prev=bytearray(stride);pixels=[];p=0
 for y in range(h):
  mode=raw[p];p+=1;row=bytearray(raw[p:p+stride]);p+=stride
  for x in range(stride):
   a=row[x-channels] if x>=channels else 0;b=prev[x];c=prev[x-channels] if x>=channels else 0
   if mode==1:predict=a
   elif mode==2:predict=b
   elif mode==3:predict=(a+b)//2
   elif mode==4:
    t=a+b-c;aa,bb,cc=abs(t-a),abs(t-b),abs(t-c);predict=a if aa<=bb and aa<=cc else b if bb<=cc else c
   else:assert mode==0;predict=0
   row[x]=(row[x]+predict)&255
  if channels==4:assert all(row[x+3]==255 for x in range(0,stride,4))
  pixels.extend(tuple(row[x:x+3]) for x in range(0,stride,channels));prev=row
 return pixels

def bank(source,files):
 off=files['XXX.PRG;1']['lba']*2048+0x4de8
 pal=[tuple(((v>>s)&14)*255//14 for s in (0,4,8)) for v in struct.unpack_from('>16H',source,off)]
 result=bytearray();records=[]
 for n in range(1,11):
  path=ROOT/f'assets/harem-europe/card-{n:02}.png';rgb=read_png(path)
  assert set(rgb)<=set(pal),path
  # VDP index zero is transparent; use the existing darkest opaque shade.
  px=[max(1,pal.index(v)) for v in rgb];raw=bytearray()
  for ty in range(20):
   for tx in range(10):
    for y in range(8):
     for x in range(0,8,2):
      p=(ty*8+y)*80+tx*8+x;raw.append(px[p]<<4|px[p+1])
  assert len(raw)==6400
  records.append(dict(file=path.relative_to(ROOT).as_posix(),png_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),tile_sha256=hashlib.sha256(raw).hexdigest(),colors=len(set(px)),transparent_black_to_opaque_gray=True))
  result.extend(raw+bytes(SLOT-len(raw)))
 return bytes(result),records

def code():
 c=Code();c.emit('48e7fffe20790005ef7c7000102800100240001c0c400010');c.branch('67','europe')
 c.emit('0c400014');c.branch('66','original')
 c.label('europe');c.emit('4878000a4eb900011dd6588f02800000ffffe5882f3c000900002f0048780004')
 c.emit('487900000000');pointer=len(c.data)-4
 c.emit('4eb9000154a64fef0010');c.branch('60','done')
 c.label('original');c.emit('2f2f00404eb900015706588f')
 c.label('done');c.emit('4cdf7fff4e75');c.label('filename');c.data.extend(b'G2HAREM.DAT\0\0')
 raw=bytearray(c.finish());struct.pack_into('>I',raw,pointer,LOAD+HELPER+c.labels['filename']);assert HELPER+len(raw)<=0x5000
 return bytes(raw)

def directory(data):
 p=20*2048;end=p+2048;rows=[]
 while p<end and data[p]:
  n=data[p];r=bytearray(data[p:p+n]);assert n>=34;rows.append(r);p+=n
 assert not any(data[p:end]);return rows

def apply(image,source,files):
 cards,records=bank(source,files);start=LBA*2048
 assert start+len(cards)<=len(image) and not any(source[start:start+len(cards)])
 assert all(f['lba']*2048+f['size']<=start for f in files.values())
 rows=directory(source);assert not any(bytes(r[33:33+r[32]])==RESOURCE for r in rows)
 for r in rows:
  if bytes(r[33:33+r[32]])==b'XXX.PRG;1':
   assert int.from_bytes(r[10:14],'little')==0x4e08
   r[10:18]=struct.pack('<I',0x5000)+struct.pack('>I',0x5000)
 template=next(r for r in rows if bytes(r[33:33+r[32]])==b'GH2GRP.DAT;1')
 new=bytearray(template[:33])+RESOURCE
 if len(new)%2:new.append(0)
 new[0]=len(new);new[32]=len(RESOURCE)
 new[2:10]=struct.pack('<I',LBA)+struct.pack('>I',LBA)
 new[10:18]=struct.pack('<I',len(cards))+struct.pack('>I',len(cards))
 rows.append(new);rows.sort(key=lambda r:bytes(r[33:33+r[32]]))
 root=b''.join(rows);assert len(root)<=2048
 image[20*2048:21*2048]=root+bytes(2048-len(root))
 image[start:start+len(cards)]=cards
 base=files['XXX.PRG;1']['lba']*2048;helper=code()
 assert source[base+HOOK:base+HOOK+6]==bytes.fromhex('4eb900015706')
 assert not any(source[base+0x4e08:base+0x5000])
 image[base+HOOK:base+HOOK+6]=bytes.fromhex('4eb9')+struct.pack('>I',LOAD+HELPER)
 image[base+HELPER:base+HELPER+len(helper)]=helper
 return dict(resource=RESOURCE.decode(),lba=LBA,size=len(cards),cultures=[4,5],cards=records,helper=HELPER,helper_size=len(helper),ranges=[(20*2048,2048),(start,len(cards)),(base+HOOK,6),(base+HELPER,len(helper))])

def verify(source,image,files,report):
 cards,_=bank(source,files);assert image[LBA*2048:LBA*2048+len(cards)]==cards
 old={bytes(r[33:33+r[32]]):r for r in directory(source)};new={bytes(r[33:33+r[32]]):r for r in directory(image)}
 assert set(new)==set(old)|{RESOURCE}
 for name,r in old.items():
  actual=new[name]
  if name==b'XXX.PRG;1':
   expected=bytearray(r);expected[10:18]=struct.pack('<I',0x5000)+struct.pack('>I',0x5000);assert actual==expected
  else:assert actual==r,name
 r=new[RESOURCE];assert int.from_bytes(r[2:6],'little')==int.from_bytes(r[6:10],'big')==LBA
 assert int.from_bytes(r[10:14],'little')==int.from_bytes(r[14:18],'big')==len(cards)
 base=files['XXX.PRG;1']['lba']*2048
 assert image[base+HOOK:base+HOOK+6]==bytes.fromhex('4eb9')+struct.pack('>I',LOAD+HELPER)
 assert image[base+HELPER:base+HELPER+len(code())]==code()
 g=files['GH2GRP.DAT;1']['lba']*2048+0x16b*2048
 assert image[g:g+11*SLOT]==source[g:g+11*SLOT]
 assert image[:20*2048]==source[:20*2048]
 assert report['cultures']==[4,5] and report['helper_size']==len(code())
 print('PASS: ten European cards, original palette and eleven original cards; ISO directory extension and loader hook')
