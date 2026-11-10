"""Optional culture-specific cards plus the unmodified native eligible portrait.

The ISO is expanded by whole sectors; all existing file LBAs are retained.
Bit 6 of the saved options byte means ORIGINAL ONLY (zero = default enabled).
"""
from pathlib import Path
import json,struct,hashlib
from harem_success_europe import read_png,directory,ROOT,RESOURCE,SLOT,HOOK,HELPER,LOAD
from text_compositor import Code
OPTION=0x7fd58
MASK=0x40

def entries():
 rows=json.loads((ROOT/'assets/harem-generated/manifest.json').read_text('utf-8-sig'))
 assert len(rows)==76 and not any(r['culture']==0 and r['card']==2 for r in rows)
 assert [r['culture'] for r in rows]==sorted(r['culture'] for r in rows)
 return rows

def groups():
 rows=entries();out=[];base=0
 for culture in range(8):
  count=sum(r['culture']==culture for r in rows);assert count>0
  out.append((count,base));base+=count
 return out

def bank(source,files):
 off=files['XXX.PRG;1']['lba']*2048+0x4de8
 pal=[tuple(((v>>s)&14)*255//14 for s in (0,4,8)) for v in struct.unpack_from('>16H',source,off)]
 result=bytearray();records=[]
 for entry in entries():
  path=ROOT/entry['file'];rgb=read_png(path);assert set(rgb)<=set(pal),path
  px=[pal.index(v) for v in rgb];raw=bytearray()
  for ty in range(20):
   for tx in range(10):
    for y in range(8):
     for x in range(0,8,2):
      p=(ty*8+y)*80+tx*8+x;raw.append(px[p]<<4|px[p+1])
  assert len(raw)==6400
  records.append(dict(**entry,png_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),tile_sha256=hashlib.sha256(raw).hexdigest()))
  result.extend(raw+bytes(SLOT-len(raw)))
 return bytes(result),records

def code():
 c=Code();c.emit('48e7fffe083900060007fd58');c.branch('66','original')
 c.emit('20790005ef7c700010280010e44802400007e548')
 c.emit('41f900000000');table=len(c.data)-4
 c.emit('45f00000740034127600362a0002300252402f00')
 c.emit('4eb900011dd6588f02800000ffffb042');c.branch('64','original')
 c.emit('d043e5882f3c000900002f0048780004487900000000');pointer=len(c.data)-4
 c.emit('4eb9000154a64fef0010')
 # Clear the background plane only behind the generated card. Index zero
 # remains true black, not transparent room pixels or a substituted gray.
 c.emit('42a7487800144878000a487800054878000a487800014878001a4eb90000c0f44fef001c')
 c.branch('60','done')
 c.label('original');c.emit('2f2f00404eb900015706588f')
 c.label('done');c.emit('4cdf7fff4e75')
 c.label('groups')
 for count,base in groups():c.data.extend(struct.pack('>HH',count,base))
 c.label('filename');c.data.extend(b'G2HAREM.DAT\0\0')
 raw=bytearray(c.finish())
 struct.pack_into('>I',raw,table,LOAD+HELPER+c.labels['groups'])
 struct.pack_into('>I',raw,pointer,LOAD+HELPER+c.labels['filename'])
 assert HELPER+len(raw)<=0x5000
 return bytes(raw)

def apply(image,source,files):
 cards,records=bank(source,files);assert len(image)==len(source) and len(source)%2048==0
 start=len(source);lba=start//2048;image.extend(cards)
 rows=directory(source)
 for r in rows:
  if bytes(r[33:33+r[32]])==b'XXX.PRG;1':
   assert int.from_bytes(r[10:14],'little')==0x4e08
   r[10:18]=struct.pack('<I',0x5000)+struct.pack('>I',0x5000)
 template=next(r for r in rows if bytes(r[33:33+r[32]])==b'GH2GRP.DAT;1')
 new=bytearray(template[:33])+RESOURCE
 if len(new)%2:new.append(0)
 new[0]=len(new);new[32]=len(RESOURCE)
 new[2:10]=struct.pack('<I',lba)+struct.pack('>I',lba)
 new[10:18]=struct.pack('<I',len(cards))+struct.pack('>I',len(cards))
 rows.append(new);rows.sort(key=lambda r:bytes(r[33:33+r[32]]))
 root=b''.join(rows);assert len(root)<=2048
 image[20*2048:21*2048]=root+bytes(2048-len(root))
 pvd=16*2048;assert source[pvd:pvd+7]==b'\x01CD001\x01'
 image[pvd+80:pvd+88]=struct.pack('<I',len(image)//2048)+struct.pack('>I',len(image)//2048)
 base=files['XXX.PRG;1']['lba']*2048;helper=code()
 assert source[base+HOOK:base+HOOK+6]==bytes.fromhex('4eb900015706')
 assert not any(source[base+0x4e08:base+0x5000])
 image[base+HOOK:base+HOOK+6]=bytes.fromhex('4eb9')+struct.pack('>I',LOAD+HELPER)
 image[base+HELPER:base+HELPER+len(helper)]=helper
 return dict(resource=RESOURCE.decode(),lba=lba,size=len(cards),source_size=len(source),expanded_size=len(image),cultures=list(range(8)),groups=groups(),cards=records,helper=HELPER,helper_size=len(helper),option_address=OPTION,disabled_mask=MASK,ranges=[(pvd+80,8),(20*2048,2048),(start,len(cards)),(base+HOOK,6),(base+HELPER,len(helper))])

def verify(source,image,files,report):
 cards,_=bank(source,files);assert len(image)==len(source)+len(cards)
 assert image[len(source):]==cards
 old={bytes(r[33:33+r[32]]):r for r in directory(source)};new={bytes(r[33:33+r[32]]):r for r in directory(image)}
 assert set(new)==set(old)|{RESOURCE}
 for name,r in old.items():
  expected=bytearray(r)
  if name==b'XXX.PRG;1':expected[10:18]=struct.pack('<I',0x5000)+struct.pack('>I',0x5000)
  assert new[name]==expected,name
 r=new[RESOURCE];assert int.from_bytes(r[2:6],'little')==int.from_bytes(r[6:10],'big')==len(source)//2048
 assert int.from_bytes(r[10:14],'little')==int.from_bytes(r[14:18],'big')==len(cards)
 pvd=16*2048;assert int.from_bytes(image[pvd+80:pvd+84],'little')==int.from_bytes(image[pvd+84:pvd+88],'big')==len(image)//2048
 base=files['XXX.PRG;1']['lba']*2048
 assert image[base+HOOK:base+HOOK+6]==bytes.fromhex('4eb9')+struct.pack('>I',LOAD+HELPER)
 assert image[base+HELPER:base+HELPER+len(code())]==code()
 g=files['GH2GRP.DAT;1']['lba']*2048+0x16b*2048
 assert image[g:g+11*SLOT]==source[g:g+11*SLOT]
 assert image[base+0x3fac:base+HOOK]==source[base+0x3fac:base+HOOK], 'Native special-wife eligibility changed'
 assert report['groups']==[list(g) for g in groups()]
 print('PASS: 76 uncompressed generated cards; all 11 originals and their selection code retained; expanded ISO directory')
