from pathlib import Path
import sys,json,hashlib,re
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from emulate import png
original=(ROOT/'rom/original.gen').read_bytes()
reference=next((ROOT/'rom/reference').glob('*.md')).read_bytes()
print('Reference SHA256:',hashlib.sha256(reference).hexdigest())
ranges=[];start=None
for i,(a,b) in enumerate(zip(original,reference)):
    if a!=b and start is None:start=i
    if a==b and start is not None:ranges.append((start,i));start=None
if start is not None:ranges.append((start,len(reference)))
(ROOT/'analysis/reference-diff.json').write_text(json.dumps([dict(start=f'{a:06X}',end=f'{b:06X}',size=b-a) for a,b in ranges],indent=2))
print('Changed code ranges:',[(hex(a),hex(b)) for a,b in ranges if a<0x3947a][:180])
w,h=384,576;rgb=bytearray()
for y in range(h):
    for x in range(w):
        glyph=(y//48)*16+x//24
        ink=reference[0x46244+glyph*16+(y//3)%16]&(128>>((x//3)%8))
        rgb.extend((255,255,255) if ink else (0,0,0))
png(ROOT/'analysis/font-reference.png',w,h,rgb)

class Plain(HTMLParser):
    def __init__(self): super().__init__();self.parts=[];self.skip=0;self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag in ('p','br','tr','hr','div'):self.parts.append('\n')
        if tag=='a':
            href=dict(attrs).get('href','')
            if 'topic.php' in href:self.links.append(href)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip-=1
        if tag in ('p','tr','div'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
p=Plain();p.feed((ROOT/'analysis/forum-topic35.html').read_bytes().decode('cp1251'))
plain=re.sub(r'\n[ \t]*\n+', '\n\n', ''.join(p.parts))
(ROOT/'analysis/forum-topic35.txt').write_text(plain,encoding='utf-8')
print('Forum text saved; topic links:',sorted(set(p.links))[-25:])
