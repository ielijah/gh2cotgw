"""Check production command builders and render the five requested phrases."""
from pathlib import Path
import sys,struct,subprocess,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode
from attack_phrases import CODE,STATEMENTS,PROMPTS
rom=(ROOT/'build/genghis2-ru-experimental.gen').read_bytes()
def pea(p):return bytes.fromhex('4879')+struct.pack('>I',p)
cases=[]
for i,action in enumerate(['приказ атаки','приказ перемещения','приказ отправки','дипломатический приказ']):
 cases.append(('give-'+str(i),bytes.fromhex('7400')[:-1]+bytes([i])+rom[0x29350:0x2937e]+bytes.fromhex('4fef000c'),PROMPTS[i]))
 cases.append(('issue-'+str(i),bytes([0x74,i])+rom[0x298c8:0x298f6]+bytes.fromhex('4fef000c'),STATEMENTS[i]))
for i,p in enumerate([0x3b792,0x3cece]):
 code=pea(0x39a44)+bytes.fromhex('4eb900006c22588f')+pea(p)+bytes.fromhex('4eb9')+struct.pack('>I',CODE)+bytes.fromhex('588f')
 cases.append(('we-attack-'+str(i),code,'Мы атакуем'))
for i,(p,text) in enumerate([(0x3cee2,'Пересылаем золото'),(0x3ceec,'Пересылаем продовольствие'),(0x3ced6,'Перемещаем войска')]):
 code=pea(0x39a44)+bytes.fromhex('4eb900006c22588f')+pea(p)+bytes.fromhex('4eb9')+struct.pack('>I',CODE)+bytes.fromhex('588f')
 cases.append(('dispatch-'+str(i),code,text))
for label,ptr,text in [('form-legions',0x12ab40,'Сформировать легионы лично?'),('return-safely',0x3d114,'Вернись невредимым!')]:
 cases.append((label,pea(ptr)+bytes.fromhex('4eb900006c22588f'),text))
r=bytearray(rom);base=len(r);c=bytearray.fromhex('46fc2700')
for i,(_,code,text) in enumerate(cases):
 c+=code
 for j in range(0,64,4):c+=bytes.fromhex('23f9')+struct.pack('>II',0xff2ce8+j,0xff9000+i*64+j)
c+=bytes.fromhex('33fca55a00ffdffe60fe');r.extend(c);r[4:8]=struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
p=ROOT/'build/diagnostics/attack-phrases.gen';p.write_bytes(r)
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'120'],check=True,capture_output=True)
m=bytearray((ROOT/'analysis/memory-2.bin').read_bytes());m[::2],m[1::2]=m[1::2],m[::2]
assert m[0xdffe:0xe000].hex()=='a55a'
for i,(label,code,text) in enumerate(cases):
 got=m[0x9000+i*64:0x9040+i*64].split(b'\0')[0];assert got==encode(text),(label,got,encode(text))
print('PASS:',len(cases),'native command phrases',flush=True)
inputs=[[1900,1910,3],[3000,3010,3],[4100,4110,8],[5100,5110,8],[5500,5510,8],[6400,6410,8],[7200,7210,8]]+[[t,t+10,8] for t in range(8100,10501,600)]
for label,code,text in cases:
 if label not in ['give-1','issue-1','give-2','issue-2','dispatch-0']:continue
 r=bytearray(rom);base=len(r);r.extend(bytes.fromhex('4eb900009c00')+code+pea(0xff2ce8)+bytes.fromhex('4eb900007df0588f60fe'))
 r[0xa436:0xa43c]=bytes.fromhex('4eb9')+struct.pack('>I',base);r[0x1a4:0x1a8]=struct.pack('>I',len(r)-1)
 p=ROOT/f'build/diagnostics/{label}.gen';p.write_bytes(r)
 subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(p),'12000',json.dumps(inputs)],check=True,capture_output=True)
 print('Rendered',label,flush=True)
