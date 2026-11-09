"""Native 32x16 harem buttons using the established Mega Drive Cyrillic menu font."""
from pathlib import Path
import sys,json,hashlib,struct
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'mega-drive/tools'))
from menu_graphics import render
sys.path.insert(0,str(ROOT/'tools'))
from koei_decode import decode

def build():
    inventory=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
    image=(ROOT/'disc'/inventory['image']).read_bytes()
    bank=next(f for f in inventory['files'] if f['path']=='GH2GRP.DAT;1');base=bank['lba']*2048
    report=json.loads((ROOT/'translation/buttons.json').read_text('utf8'))
    captions={'DC':'Лесть','DD':'Образ','DE':'Любовь','DF':'Дары','E0':'Совет','E1':'Уйти'}
    report['entries']=[e for e in report['entries'] if e['resource'] not in captions]
    previews=[]
    for key,caption in captions.items():
        n=int(key,16);ptr=struct.unpack_from('>I',image,base+0x939c+n*4)[0]
        original,_=decode(image[base+ptr-0xb2800:]);assert len(original)==256
        result=bytes(render(original,n,caption,{},b''))
        assert {v for b in original for v in (b>>4,b&15)}=={v for b in result for v in (b>>4,b&15)}
        path=f'assets/buttons/{key.lower()}.bin';(ROOT/path).write_bytes(result)
        report['entries'].append(dict(resource=key,caption=caption,file=path,size=len(result),sha256=hashlib.sha256(result).hexdigest(),source_cd_sha256=hashlib.sha256(original).hexdigest(),adaptation=None,origin='sega-cd-harem',font_source='mega-drive/translation/menu-font.json'))
        previews.append(result)
    (ROOT/'translation/buttons.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Static asset preview, not an emulator capture.
    from emulate import png
    colors={0:(0,0,0),9:(132,65,65),14:(239,239,239),15:(32,20,20)}
    rgb=bytearray()
    for y in range(16):
        for raw in previews:
            for x in range(32):
                b=raw[(y//8*4+x//8)*32+y%8*4+x%8//2];v=(b>>(4 if x%2==0 else 0))&15
                rgb.extend(colors.get(v,(100,100,100)))
    png(ROOT/'analysis/harem-buttons-preview.png',192,16,rgb)
    print('Built six native-size harem labels')
if __name__=='__main__':build()
