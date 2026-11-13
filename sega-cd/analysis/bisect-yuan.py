from pathlib import Path
import json,subprocess,os,struct,zlib
r=Path('.'); inv=json.loads((r/'analysis/disc-inventory.json').read_text());iso=(r/'build/playable-dub/track01.iso').read_bytes();f=next(f for f in inv['files'] if f['path']=='SMAIN.PRG;1');raw=iso[f['lba']*2048:f['lba']*2048+f['size']];sw=bytearray(raw);sw[::2],sw[1::2]=raw[1::2],raw[::2];base=(r/'analysis/yuan-original-main.state').read_bytes()
def test(lo,hi):
 st=bytearray(base);st[278766+lo:278766+hi]=sw[lo:hi];(r/'analysis/yuan-bisect.state').write_bytes(st)
 env=os.environ.copy();env['CORE_OPTIONS']='{"genesis_plus_gx_cart_size":"none"}';env['STATE_IN']='analysis/yuan-bisect.state';env.pop('STATE_OUT',None)
 subprocess.run(['../.runtime/python/python.exe','tools/emulate.py','build/qa-generated/trial.cue','800','[[10,20,5],[120,130,5],[230,240,5],[350,360,8]]'],env=env,stdout=subprocess.DEVNULL,timeout=20,check=True)
 png=(r/'analysis/screen-latest.png').read_bytes();p=8;data=b''
 while p<len(png):
  n=int.from_bytes(png[p:p+4],'big');t=png[p+4:p+8]
  if t==b'IDAT':data+=png[p+8:p+8+n]
  p+=n+12
 rgb=zlib.decompress(data);black=rgb.count(b'\x00\x00\x00');print(hex(lo),hex(hi),'black',black,flush=True)
 (r/f'analysis/yuan-bisect-{lo:x}-{hi:x}.png').write_bytes(png)
 return black>15000
lo=0x20000;hi=0x37490
if test(lo,hi):
 while hi-lo>16:
  mid=((lo+hi)//4)*2
  if test(lo,mid):hi=mid
  else:lo=mid
 print('CULPRIT',hex(lo),hex(hi))
