"""Controlled Genesis Plus GX success scenes using a current-build cold-boot state.

Skips the minigame and holds the success scene for pixel checks. Does not alter
the production ISO. Native palette, CD filesystem and rendering code execute.
"""
from pathlib import Path
import json,struct,os,subprocess,shutil,zlib,sys,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from harem_cards import ROOT as R,HELPER,groups,entries,read_png
OUT=R/'analysis/qa-harem-cards';OUT.mkdir(exist_ok=True)
inv=json.loads((R/'analysis/disc-inventory.json').read_text('utf8'));image=(R/'build/genchou-hishi-ru-experimental.iso').read_bytes();files={f['path']:f for f in inv['files']};f=files['XXX.PRG;1'];main=files['SMAIN.PRG;1']
baseline=(R/'analysis/qa-card-options/cold-map.state').read_bytes();pbase=229614
assert len(baseline)==1036288
def screenshot(path):
 b=Path(path).read_bytes();w,h=struct.unpack_from('>II',b,16);p=8;data=b''
 while p<len(b):
  n=int.from_bytes(b[p:p+4],'big')
  if b[p+4:p+8]==b'IDAT':data+=b[p+8:p+8+n]
  p+=n+12
 d=zlib.decompress(data);assert all(d[y*(w*3+1)]==0 for y in range(h))
 return [tuple(d[y*(w*3+1)+1+x*3:y*(w*3+1)+4+x*3]) for y in range(40,200) for x in range(80,160)]
def original(index):
 off=files['GH2GRP.DAT;1']['lba']*2048+(0x16b+index*4)*2048;raw=image[off:off+6400]
 pal=[tuple(((v>>s)&14)*255//14 for s in (0,4,8)) for v in struct.unpack_from('>16H',image,f['lba']*2048+0x4de8)]
 return [pal[(raw[((y//8)*10+x//8)*32+(y%8)*4+(x%8)//2]>>(4 if x%2==0 else 0))&15] for y in range(160) for x in range(80)]
cases=[]
for culture,(count,base) in enumerate(groups()):
 for chosen in range(count):cases.append((culture,chosen,4,False))
 for disabled in (False,True):
  for wife in ([0,1,7,4] if culture==0 else [4]):cases.append((culture,count,wife,disabled))
colors={};report=[];rows=entries()
env=os.environ.copy();env['CORE_OPTIONS']='{"genesis_plus_gx_cart_size":"none"}'
for culture,chosen,wife_id,disabled in cases:
 count,base=groups()[culture];is_new=not disabled and chosen<count
 native={0:0,1:1,7:2}.get(wife_id,culture+3)
 tag=f'c{culture}-'+(f'new-{rows[base+chosen]["card"]:02}' if is_new else f'original-{native:02}-off{int(disabled)}')
 st=bytearray(baseline)
 def write(addr,data):
  swapped=bytearray(data);swapped[::2],swapped[1::2]=data[1::2],data[::2];st[pbase+addr:pbase+addr+len(data)]=swapped
 write(0xc000,image[main['lba']*2048:][:main['size']])
 raw=bytearray(image[f['lba']*2048:][:0x5000]);off=raw.index(bytes.fromhex('4eb900011dd6'),HELPER);raw[off:off+6]=bytes([0x70,chosen])+bytes.fromhex('4e714e71')
 raw[0x361e:0x3622]=bytes.fromhex('60000006');raw[0x362c:0x3630]=bytes.fromhex('60000044');raw[0x4050:0x4054]=bytes.fromhex('4878003c')
 raw[0x4ff0:0x4ff8]=bytes.fromhex('4eb90006600060fe');write(0x66000,raw)
 write(0x5ef7c,struct.pack('>I',0x6af00));wife=bytearray(26);wife[16]=culture<<2;wife[20:22]=struct.pack('>H',wife_id);write(0x6af00,wife)
 write(0x7fd58,bytes([0x40 if disabled else 0,0]));struct.pack_into('<I',st,1016136,0x6aff0)
 fixture=OUT/'fixture.state';fixture.write_bytes(st);env['STATE_IN']=str(fixture);env['STATE_OUT']=str(OUT/'shown.state')
 subprocess.run([sys.executable,str(R/'tools/emulate.py'),str(R/'build/qa-cards/game.cue'),'1000','[]'],env=env,check=True,stdout=subprocess.DEVNULL)
 path=OUT/(tag+'.png');shutil.copyfile(R/'analysis/screen-latest.png',path)
 expected=read_png(R/rows[base+chosen]['file']) if is_new else original(native)
 for pos,(a,b) in enumerate(zip(expected,screenshot(path))):
  if not is_new and a==(0,0,0):continue
  if a in colors:assert colors[a]==b,(tag,pos,a,b,colors[a])
  else:colors[a]=b
 assert colors.get((0,0,0),(0,0,0))==(0,0,0),'Black was replaced or transparent'
 assert len(set(colors.values()))==len(colors)
 report.append(dict(culture=culture,card=rows[base+chosen]['card'] if is_new else native,generated=is_new,disabled=disabled,wife_id=wife_id,all_pixels_match=is_new,opaque_pixels_match=True,screenshot=path.name))
 print('PASS',tag,flush=True)
(OUT/'report.json').write_text(json.dumps(dict(iso_sha256=hashlib.sha256(image).hexdigest(),method=__doc__,cases=report,palette_mapping=[(a,b) for a,b in colors.items()]),ensure_ascii=False,indent=2)+'\n','utf8')
