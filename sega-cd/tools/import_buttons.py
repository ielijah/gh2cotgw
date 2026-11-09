"""Transfer already verified Mega Drive button pixels; keep incompatible widths separate."""
from pathlib import Path
import hashlib,json,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from koei_decode import decode
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent
MD=next(p for p in (ROOT.parent/'mega-drive',WORKSPACE) if (p/'translation/graphics.json').is_file())
rom=(MD/'build/genghis2-ru-experimental.gen').read_bytes()
manifest=json.loads((MD/'build/manifest.json').read_text('utf8'))
assert hashlib.sha256(rom).hexdigest()==manifest['rom_sha256']
inventory=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
iso=(ROOT/'disc'/inventory['image']).read_bytes()
graphic_file=next(f for f in inventory['files'] if f['path']=='GH2GRP.DAT;1')
base=graphic_file['lba']*2048
captions={'B9':'Да','BA':'Нет',**json.loads((MD/'translation/graphics.json').read_text('utf8'))}
out=ROOT/'assets/buttons';out.mkdir(exist_ok=True)
previous=ROOT/'translation/buttons.json'
local_entries=[e for e in json.loads(previous.read_text('utf8'))['entries'] if e.get('origin') in ('sega-cd-keyboard','sega-cd-age')] if previous.exists() else []
entries=[];deferred=[]
compact=json.loads((MD/'translation/menu-font.json').read_text('utf8'))
(ROOT/'assets/button-compact-font.json').write_text(json.dumps({ch:compact[ch] for ch in 'ходвейст'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def two_line(raw,lines):
    assert len(raw)==128
    def offset(x,y):return (y//8*2+x//8)*32+y%8*4+x%8//2
    pixels=[[(raw[offset(x,y)]>>(4 if x%2==0 else 0))&15 for x in range(16)] for y in range(16)]
    for y in range(15):
        for x in range(1,16):pixels[y][x]=9
    for top,text in zip((0,8),lines):
        width=sum(len(compact[ch][0]) for ch in text)+len(text)-1
        assert width<=15
        left=1+(15-width)//2
        for ch in text:
            rows=compact[ch];assert len(rows)==7
            for y,row in enumerate(rows):
                for x,bit in enumerate(row):
                    if bit=='1':pixels[top+y][left+x]=14
            left+=len(rows[0])+1
    result=bytearray(raw)
    for y in range(16):
        for x in range(0,16,2):result[offset(x,y)]=pixels[y][x]<<4|pixels[y][x+1]
    return bytes(result)
for key,caption in captions.items():
    resource=int(key,16)
    old_pointer=struct.unpack_from('>I',iso,base+0x939c+resource*4)[0]
    old,_=decode(iso[base+old_pointer-0xb2800:])
    pointer=struct.unpack_from('>I',rom,0xa663c+resource*4)[0]
    new,_=decode(rom[pointer:])
    adaptation=None
    if len(old)!=len(new):
        lines={'1A':['хо','дов'],'FB':['дей','ств']}.get(key)
        if lines is None:
            deferred.append(dict(resource=key,caption=caption,cd_bytes=len(old),md_bytes=len(new),
                                 reason='Different native width; requires separate layout adaptation'))
            continue
        new=two_line(old,lines)
        adaptation=dict(layout='two-line native 16x16',lines=lines,
                        font_source='translation/menu-font.json',font_source_sha256=hashlib.sha256((MD/'translation/menu-font.json').read_bytes()).hexdigest())
    assert {v for b in old for v in (b>>4,b&15)}=={v for b in new for v in (b>>4,b&15)},key
    name=key.lower()+'.bin';(out/name).write_bytes(new)
    entries.append(dict(resource=key,caption=caption,file='assets/buttons/'+name,size=len(new),
                        sha256=hashlib.sha256(new).hexdigest(),source_cd_sha256=hashlib.sha256(old).hexdigest(),adaptation=adaptation))
entries.extend(e for e in local_entries if not any(x['resource']==e['resource'] for x in entries))
report=dict(source_md_version=manifest['version'],source_md_rom_sha256=manifest['rom_sha256'],
            pixel_policy='Exact Mega Drive pixels except two declared narrow labels using unchanged compact glyphs in two rows; no scaling or palette conversion',
            entries=entries,deferred=deferred)
(ROOT/'translation/buttons.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(f'Imported {len(entries)} native-size Russian labels; {len(deferred)} incompatible-width resources deferred')

# Keep the Sega CD-only harem labels when refreshing the shared Mega Drive assets.
from import_harem_buttons import build as build_harem_buttons
build_harem_buttons()
