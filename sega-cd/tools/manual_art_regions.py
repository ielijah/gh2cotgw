"""Locate colour illustrations in the manual; headings and margins are excluded."""
from PIL import Image,ImageFilter,ImageDraw
from pathlib import Path
import numpy as np,json
ROOT=Path(__file__).resolve().parents[1]
result={}
for n in range(3,62):
    im=Image.open(ROOT/f'tmp/pdfs/source-{n+1:02}.png').convert('RGB').resize((1100,1100))
    a=np.asarray(im.resize((275,275))).astype(int)
    mask=((a.max(2)-a.min(2)>65)&(a.min(2)<155)).astype('uint8')*255
    m=np.asarray(Image.fromarray(mask).filter(ImageFilter.MaxFilter(5))).copy()>0
    m[:15,:]=False;m[259:,:]=False;m[:,:28]=False;m[:,249:]=False
    boxes=[]
    for y in range(15,259):
        for x in range(28,249):
            if not m[y,x]:continue
            stack=[(x,y)];m[y,x]=False;xs=[];ys=[]
            while stack:
                xx,yy=stack.pop();xs.append(xx);ys.append(yy)
                for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                    u,v=xx+dx,yy+dy
                    if 0<=u<275 and 0<=v<275 and m[v,u]:m[v,u]=False;stack.append((u,v))
            x0,x1,y0,y1=min(xs)*4,max(xs)*4,min(ys)*4,max(ys)*4
            w,h=x1-x0,y1-y0
            if len(xs)>35 and w>30 and h>25 and not (w>500 and h<130):
                boxes.append([x0+5,y0+5,x1-1,y1-1])
    result[n]=sorted(boxes,key=lambda b:(b[1],b[0]))
(ROOT/'tmp/pdfs/art-regions.json').write_text(json.dumps(result),'utf8')
print(json.dumps({n:result[n] for n in [19,20,24,25,29,35,36,40,41,54]}))
