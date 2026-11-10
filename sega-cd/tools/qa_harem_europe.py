"""Controlled emulator checks: real room setup, success drawing, CD loading and exit.
QA fixtures skip greeting/minigame and force RNG; production ISO remains untouched.
"""
from pathlib import Path
import json,struct,os,subprocess,shutil,zlib,sys,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from harem_success_europe import read_png,HELPER
R=Path(__file__).resolve().parents[1];OUT=R/'analysis/qa-harem-europe';OUT.mkdir(exist_ok=True)
inv=json.loads((R/'analysis/disc-inventory.json').read_text('utf8'));image=(R/'build/genchou-hishi-ru-experimental.iso').read_bytes();files={f['path']:f for f in inv['files']};f=files['XXX.PRG;1'];baseline=(R/'analysis/europe-harem-cold.state').read_bytes();pbase=229614
assert len(baseline)==1036288
main=files['SMAIN.PRG;1'];signature=image[main['lba']*2048:main['lba']*2048+64]
swapped=bytearray(signature);swapped[::2],swapped[1::2]=signature[1::2],signature[::2]
assert baseline[pbase+0xc000:pbase+0xc040]==swapped
shutil.copyfile(R/'build/genchou-hishi-ru-experimental.iso',R/'build/qa-generated/trial.iso')
def screenshot(path):
 b=Path(path).read_bytes();w,h=struct.unpack_from('>II',b,16);p=8;data=b''
 while p<len(b):
  n=int.from_bytes(b[p:p+4],'big')
  if b[p+4:p+8]==b'IDAT':data+=b[p+8:p+8+n]
  p+=n+12
 d=zlib.decompress(data);assert all(d[y*(w*3+1)]==0 for y in range(h))
 return [tuple(d[y*(w*3+1)+1+x*3:y*(w*3+1)+4+x*3]) for y in range(40,200) for x in range(80,160)]
def original(culture):
 off=files['GH2GRP.DAT;1']['lba']*2048+(0x16b+(culture+3)*4)*2048;raw=image[off:off+6400]
 pal=[tuple(((v>>s)&14)*255//14 for s in (0,4,8)) for v in struct.unpack_from('>16H',image,f['lba']*2048+0x4de8)]
 out=[]
 for y in range(160):
  for x in range(80):
   b=raw[((y//8)*10+x//8)*32+(y%8)*4+(x%8)//2];out.append(pal[(b>>4 if x%2==0 else b&15)])
 return out
colors={};report=[]
env=os.environ.copy();env['CORE_OPTIONS']='{"genesis_plus_gx_cart_size":"none"}'
for culture,chosen in [(c,n) for c in (4,5) for n in range(10)]+[(c,0) for c in (0,1,2,3,6,7)]:
 tag=f'culture-{culture}-card-{chosen+1:02}';st=bytearray(baseline);raw=bytearray(image[f['lba']*2048:f['lba']*2048+0x5000])
 off=raw.index(bytes.fromhex('4eb900011dd6'),HELPER);raw[off:off+6]=bytes([0x70,chosen])+bytes.fromhex('4e714e71')
 # Preserve native room setup and display-enable, skip voiced greeting/gameplay.
 raw[0x361e:0x3622]=bytes.fromhex('60000006');raw[0x362c:0x3630]=bytes.fromhex('60000044')
 raw[0x4ff0:0x4ff8]=bytes.fromhex('4eb90006600060fe')
 def write(addr,data):
  swapped=bytearray(data);swapped[::2],swapped[1::2]=data[1::2],data[::2];st[pbase+addr:pbase+addr+len(data)]=swapped
 write(0x66000,raw);write(0x5ef7c,struct.pack('>I',0x6af00));wife=bytearray(26);wife[16]=culture<<2;wife[20:22]=struct.pack('>H',4);write(0x6af00,wife)
 struct.pack_into('<I',st,1016136,0x6aff0);fixture=OUT/'fixture.state';fixture.write_bytes(st)
 env['STATE_IN']=str(fixture);env['STATE_OUT']=str(OUT/'shown.state')
 subprocess.run([sys.executable,str(R/'tools/emulate.py'),str(R/'build/qa-generated/trial.cue'),'500','[]'],env=env,check=True,stdout=subprocess.DEVNULL)
 path=OUT/(tag+'.png');shutil.copyfile(R/'analysis/screen-latest.png',path)
 expected=read_png(R/f'assets/harem-europe/card-{chosen+1:02}.png') if culture in (4,5) else original(culture)
 if culture in (4,5):expected=[(72,72,72) if p==(0,0,0) else p for p in expected]
 actual=screenshot(path)
 for a,b in zip(expected,actual):
  if culture not in (4,5) and a==(0,0,0):continue
  if a in colors:assert colors[a]==b,(tag,a,b,colors[a])
  else:colors[a]=b
 assert len(set(colors.values()))==len(colors)
 # Native exit must complete after the success delay, not freeze in the loader.
 env['STATE_IN']=str(OUT/'shown.state');env['STATE_OUT']=str(OUT/'returned.state')
 subprocess.run([sys.executable,str(R/'tools/emulate.py'),str(R/'build/qa-generated/trial.cue'),'1000','[]'],env=env,check=True,stdout=subprocess.DEVNULL)
 returned=(OUT/'returned.state').read_bytes();assert struct.unpack_from('<I',returned,1016136)[0]==0x6aff6,tag
 if chosen==0:shutil.copyfile(R/'analysis/screen-latest.png',OUT/(tag+'-return.png'))
 report.append(dict(culture=culture,card=chosen+1 if culture in (4,5) else 'original',opaque_pixels_match=True,all_12800_pixels_match=culture in (4,5),returned=True,screenshot=path.name))
 print('PASS',tag,flush=True)
(OUT/'report.json').write_text(json.dumps(dict(iso_sha256=hashlib.sha256(image).hexdigest(),method=__doc__,cases=report,palette_mapping=[(a,b) for a,b in colors.items()]),ensure_ascii=False,indent=2)+'\n','utf8')
