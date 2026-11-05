"""Build experimental Cyrillic renderer and reviewed in-place translations."""
from pathlib import Path
import hashlib,json,struct,re,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from graphics_codec import decode,encode_literals
from menu_graphics import render as render_caption, address as graphic_address
from import_font import pack_static,REFERENCE_SHA
from name_keyboard import apply as apply_name_keyboard
from title_logo import apply as apply_title_logo
from title_prompt import apply as apply_title_prompt
from scenario_window import apply as apply_scenario_window
EXPECTED='94efa72e970266710995b489a1d6b88e1a03635a230b41d9a5cd2268757f25d4'

# Both Russian font faces are imported from the user-provided reference ROM.

def encode(s):
    assert all(0<ord(c)<128 or 'А'<=c<='я' or c in 'Ёё' for c in s),f'Unsupported character in {s!r}'
    return bytes(0x1c if c=='Ё' else 0x7f if c=='ё' else ord(c) if ord(c)<128 else 0xa0+ord(c)-ord('А') for c in s)

def check_format(en,ru):
    pattern=r'%(?:[-+0 #]|\d|\.)*[a-zA-Z]'
    assert re.findall(pattern,en)==re.findall(pattern,ru),(en,ru,'format specifiers differ')

class Code:
    def __init__(self,base): self.base=base; self.data=bytearray(); self.labels={}; self.fix=[]
    def emit(self,s): self.data.extend(bytes.fromhex(s))
    def label(self,s): self.labels[s]=self.base+len(self.data)
    def branch(self,op,label):
        self.emit(op+'000000'); self.fix.append((len(self.data)-2,label))
    def jump(self,addr): self.emit('4ef9'+f'{addr:08x}')
    def finish(self):
        for off,label in self.fix: self.data[off:off+2]=struct.pack('>h',self.labels[label]-(self.base+off))
        return self.data

def main():
    src=(ROOT/'rom/original.gen').read_bytes()
    assert hashlib.sha256(src).hexdigest()==EXPECTED,'Unexpected source ROM'
    rom=bytearray(src)+bytearray(0x28000)
    reference=next((ROOT/'rom/reference').glob('*.md')).read_bytes()
    assert hashlib.sha256(reference).hexdigest()==REFERENCE_SHA,'Unexpected font reference ROM'
    font,alternate,font_tiles,latin_map,cyr_map=pack_static(reference,src)
    alphabet=''.join(chr(ord('А')+i) for i in range(64))+'Ёё'
    for i,ch in enumerate(alphabet):
        rom[0x103000+i*16:0x103010+i*16]=font[ch]
        rom[0x103500+i*16:0x103510+i*16]=alternate[ch]
    rom[0x104000:0x105800]=font_tiles
    rom[0x105800:0x105b00]=b''.join(struct.pack('>HH',*pair) for pair in latin_map)
    rom[0x105b00:0x105c08]=b''.join(struct.pack('>HH',*pair) for pair in cyr_map)
    c=Code(0x100400)
    c.emit('0c03001c'); c.branch('67','upper_yo')
    c.emit('0c03007f'); c.branch('67','lower_yo')
    c.emit('0c0300a0'); c.branch('65','old')
    c.emit('0c0300df'); c.branch('62','old')
    c.emit('7800180306040020'); c.jump(0x5e78)
    c.label('old'); c.emit('0c030080'); c.branch('65','ascii'); c.jump(0x5e44)
    c.label('ascii'); c.jump(0x5e4a)
    c.label('upper_yo'); c.emit('7800383c0100'); c.branch('60','yo_call')
    c.label('lower_yo'); c.emit('7800383c0101')
    c.label('yo_call'); c.emit('486eff742f044eb900005cf8'); c.jump(0x5e84)
    rom[c.base:c.base+len(c.finish())]=c.finish()
    d=Code(0x100e00)
    d.emit('426effbc')
    d.emit('0c84000000c0'); d.branch('65','original')
    d.emit('4a3900ff7d13'); d.branch('66','cyr_dynamic'); d.jump(0x100b00)
    d.label('cyr_dynamic')
    d.jump(0x100600)
    d.label('original'); d.emit('4a3900ff7d13'); d.branch('66','dynamic'); d.jump(0x100b80)
    d.label('dynamic'); d.jump(0x5d12)
    rom[d.base:d.base+len(d.finish())]=d.finish()
    e=Code(0x100500)
    e.emit('0c8200000c00'); e.branch('65','latin')
    e.emit('4a7900ff7b06'); e.branch('66','alternate')
    e.emit('0682001024004e75')
    e.label('alternate'); e.emit('0682001029004e75')
    e.label('latin'); e.emit('0682000462444e75')
    rom[e.base:e.base+len(e.finish())]=e.finish()
    # Tags at FFD000..FFD7FF identify cached glyph pairs by physical VRAM tile.
    # Only ephemeral, coloured text uses the ring. Persistent static text
    # uses the permanent packed bank and can never be evicted by a menu.
    # Uploads, pool changes and font-face switches invalidate dynamic tags.
    cache=Code(0x100600)
    cache.emit('4eb900100d003a04044500c05245')
    cache.emit('7000103900ff5978e9487200123900ff2d6e8041ef488a4000458000')
    cache.emit('343900ff57f0')
    cache.label('search')
    cache.emit('247c00ffd000d4c2ba52'); cache.branch('67','found')
    cache.emit('5442b47900ff3004'); cache.branch('65','search')
    cache.emit('3d45ffbc'); cache.jump(0x5d12)
    cache.label('found'); cache.emit('38c252423882'); cache.jump(0x5e0c)
    rom[cache.base:cache.base+len(cache.finish())]=cache.finish()
    invalidate=Code(0x100800)
    invalidate.emit('48e7c0807000302f00167200122f0017')
    # Above offsets include the 12 bytes saved by MOVEM: dest low word +22.
    invalidate.emit('028100000001d2af0018024007fe207c00ffd000d0c0')
    invalidate.emit('4a81'); invalidate.branch('67','done')
    invalidate.label('clear'); invalidate.emit('425054885581'); invalidate.branch('6e','clear')
    invalidate.label('done'); invalidate.emit('4cdf01032f02242f0010'); invalidate.jump(0x3e64)
    rom[invalidate.base:invalidate.base+len(invalidate.finish())]=invalidate.finish()
    reset=Code(0x100900)
    reset.emit('48e78080207c00ffd000303c03ff')
    reset.label('clear'); reset.emit('42585340'); reset.branch('6a','clear')
    reset.emit('4cdf010148e73000242f000c'); reset.jump(0x5b32)
    rom[reset.base:reset.base+len(reset.finish())]=reset.finish()
    post=Code(0x100a00)
    post.emit('4fef00104a6effbc'); post.branch('67','done')
    post.emit('302cfffc024007fe207c00ffd000d0c030aeffbc')
    post.label('done'); post.jump(0x5e0c)
    rom[post.base:post.base+len(post.finish())]=post.finish()
    for address,base,subtract in [(0x100b00,0x105b00,True),(0x100b80,0x105800,False)]:
        lookup=Code(address)
        if subtract: lookup.emit('044400c0')
        lookup.emit('024400ffe54c207c'+f'{base:08x}'+'d0c4')
        lookup.emit('7200123900ff5804700de1693010804138c03028000280413880')
        lookup.jump(0x5e0c)
        rom[address:address+len(lookup.finish())]=lookup.finish()
    preload=Code(0x100c00)
    preload.emit('487800c0487800404879001040004eb900003e5e4fef000c')
    preload.emit('4878004042a74879000457c44eb900003ddc4fef000c4e75')
    rom[preload.base:preload.base+len(preload.finish())]=preload.finish()
    face=Code(0x100d00)
    face.emit('303900ff7b06b07900ffd800'); face.branch('67','done')
    face.emit('33c000ffd800207c00ffd000303c03ff')
    face.label('clear'); face.emit('42585340'); face.branch('6a','clear')
    face.label('done');face.emit('4e75')
    rom[face.base:face.base+len(face.finish())]=face.finish()
    for addr,expected,patch in [(0x5e3e,'0c0300806506','4ef900100400'),(0x5d08,'4a3900ff7d13','4ef900100e00'),(0x5d18,'068200046244','4eb900100500')]:
        assert src[addr:addr+6].hex()==expected
        rom[addr:addr+6]=bytes.fromhex(patch)
    assert src[0x3e5e:0x3e64].hex()=='2f02242f0010'
    rom[0x3e5e:0x3e64]=bytes.fromhex('4ef900100800')
    assert src[0x5b2a:0x5b32].hex()=='48e73000242f000c'
    rom[0x5b2a:0x5b32]=bytes.fromhex('4ef9001009004e71')
    assert src[0x5dca:0x5dd0].hex()=='4fef0010603c'
    rom[0x5dca:0x5dd0]=bytes.fromhex('4ef900100a00')
    assert src[0x5d14:0x5d16].hex()=='1404'
    rom[0x5d14:0x5d16]=bytes.fromhex('3404')
    # Pass the full cleared glyph index; MOVE.B leaves stale upper bits in D0.
    assert src[0x5e7c:0x5e7e].hex()=='1004'
    rom[0x5e7c:0x5e7e]=bytes.fromhex('2004')
    assert src[0x5c10:0x5c18].hex()=='4e56ffb848e73f38'
    rom[0x5c10:0x5c18]=bytes.fromhex('4ef900100c004e71')
    applied=[]
    translations=json.loads((ROOT/'translation/reviewed.json').read_text(encoding='utf-8'))
    for source in sorted((ROOT/'translation').glob('batch-*.json')):
        extra=json.loads(source.read_text(encoding='utf-8'))
        assert not translations.keys() & extra.keys(), f'Duplicate translations in {source}'
        translations.update(extra)
    for en,ru in translations.items():
        check_format(en,ru)
        old=en.encode('ascii'); new=encode(ru)
        assert len(new)<=len(old),(en,ru,len(new),len(old))
        hits=[]
        for begin,end in [(0x3947a,0x3dabc),(0x4a000,0x4a500),(0x4b700,0x4ce00)]:
            start=begin
            while True:
                candidates=[p for suffix in (b'\0',b'\n') if (p:=src.find(old+suffix,start,end))>=0]
                pos=min(candidates) if candidates else -1
                if pos<0: break
                start=pos+len(old)+1
                if 0x20<=src[pos-1]<=0x7e: continue
                hits.append(pos)
        assert hits, en
        for pos in hits:
            rom[pos:pos+len(old)]=new+b' '*(len(old)-len(new))
            applied.append(dict(offset=f'{pos:06X}',en=en,ru=ru))
    for item in json.loads((ROOT/'translation/inline.json').read_text(encoding='utf-8')):
        pos=int(item['offset'],16); en=item['source']; ru=item['ru']; new=encode(ru)
        assert src[pos:pos+len(en)]==en.encode('ascii'),item
        check_format(en,ru)
        assert len(new)<=len(en),item
        padding=len(en)-len(new)
        if item.get('terminate'):
            assert padding>0
            rom[pos:pos+len(en)]=new+bytes(padding)
        else: rom[pos:pos+len(en)]=new+b' '*padding
        applied.append(dict(offset=f'{pos:06X}',en=en,ru=ru,terminate=item.get('terminate',False)))
    fields=json.loads((ROOT/'translation/fields.json').read_text(encoding='utf-8'))
    for group,capacity in [('people',12),('countries',22)]:
        for en,ru in fields[group].items():
            old=en.encode('ascii'); new=encode(ru)
            assert len(new)<=capacity if group=='people' else len(new)<capacity,(en,ru)
            start=0x3db1e; hits=[]
            while (pos:=src.find(old+b'\0',start,0x457c4))>=0:
                start=pos+len(old)+1
                assert src[pos+len(old):pos+capacity]==bytes(capacity-len(old)),(en,hex(pos),'field padding differs')
                if len(new)==capacity: assert src[pos+capacity]==0,(en,'Missing external terminator')
                rom[pos:pos+capacity]=new+bytes(capacity-len(new))
                applied.append(dict(offset=f'{pos:06X}',en=en,ru=ru,capacity=capacity,kind='field'))
                hits.append(pos)
            assert hits,('Missing name',en)
    for item in json.loads((ROOT/'translation/geography.json').read_text(encoding='utf-8')):
        pos=int(item['offset'],16); en=item['source']; ru=item['ru']; cap=item['capacity']
        assert src[pos:pos+cap]==en.encode('ascii')+bytes(cap-len(en)),item
        new=encode(ru); assert len(new)<cap,item
        rom[pos:pos+cap]=new+bytes(cap-len(new))
        applied.append(dict(offset=item['offset'],en=en,ru=ru,kind='field',capacity=cap))
    for item in json.loads((ROOT/'translation/relocations.json').read_text(encoding='utf-8')):
        source=int(item['source_offset'],16);target=int(item['target'],16)
        en=item['source'];ru=item['ru'];new=encode(ru)
        assert src[source:source+len(en)+1]==en.encode('ascii')+b'\0',item
        assert len(new)<0x40,item
        rom[target:target+len(new)+1]=new+b'\0'
        for ref in item['references']:
            address=int(ref,16);assert int.from_bytes(src[address:address+4],'big')==source,item
            rom[address:address+4]=struct.pack('>I',target)
        applied.append(dict(offset=f'{target:06X}',en=en,ru=ru,kind='relocated',source_offset=item['source_offset'],references=item['references']))
    # Widen and move the scenario selector left for full historical titles.
    for address,old,new in [(0x2642c,15,11),(0x2643a,15,11),(0x26450,11,15),(0x26458,14,10),(0x2646e,10,15),(0x26476,14,10),(0x264b4,15,19),(0x264bc,15,11)]:
        assert int.from_bytes(src[address:address+2],'big')==old,hex(address)
        rom[address:address+2]=struct.pack('>H',new)
    # Highlighting copies two tile rows. The original 64-byte stack buffer
    # supports only 16 columns; the translated 19-column menu needs 76 bytes.
    # Enlarge both the frame and buffer, and adjust the MOVEM restore offset.
    for address,old,new in [(0x9762,'ffc0','ffb0'),(0x977a,'ffc0','ffb0'),(0x97f8,'ffa4','ff94')]:
        assert src[address:address+2].hex()==old,hex(address)
        rom[address:address+2]=bytes.fromhex(new)
    # Raw 4bpp title subtitle, 15 consecutive 8x8 tiles. Located by matching
    # all tile colour patterns against the original emulator capture.
    subtitle=0x0d12c2
    pixels=[[0]*120 for _ in range(8)]
    for x in range(120):
        for y in range(8):
            value=src[subtitle+(x//8)*32+y*4+(x%8)//2]
            colour=(value>>(4 if x%2==0 else 0))&15
            pixels[y][x]=9 if colour in (12,14,15) else colour
    caption='КЛАН СЕРОГО ВОЛКА'
    subtitle_font=json.loads((ROOT/'translation/subtitle-font.json').read_text(encoding='utf-8'))
    caption_width=sum(4 if ch==' ' else 7 for ch in caption)-1
    x=(120-caption_width)//2
    for ch in caption:
        if ch!=' ':
            for y in range(7):
                for dx,bit in enumerate(subtitle_font[ch][y]):
                    if bit=='1':pixels[y][x+dx]=pixels[y][x+dx+1]=15
        x+=4 if ch==' ' else 7
    for x in range(0,120,2):
        for y in range(8):
            rom[subtitle+(x//8)*32+y*4+(x%8)//2]=(pixels[y][x]<<4)|pixels[y][x+1]
    # Buttons B9/BA are compressed resources, not plain text or raw tiles.
    graphics=json.loads((ROOT/'translation/graphics.json').read_text(encoding='utf-8'))
    buttons=[(0xb9,'Да',0x102000),(0xba,'Нет',0x102200)]
    buttons += [(int(key,16),caption,graphic_address(i,int(key,16))) for i,(key,caption) in enumerate(graphics.items())]
    for resource,caption,address in buttons:
        pointer=0xa663c+resource*4
        original_address=int.from_bytes(src[pointer:pointer+4],'big')
        raw,_=decode(src[original_address:])
        changed=render_caption(raw,resource,caption,font,src)
        packed=encode_literals(changed)
        assert len(packed)<=(0x400 if resource in (0xed,0xee) else 0x200)
        assert address+len(packed)<=len(rom)
        if address>=0x111000: assert address+len(packed)<=0x116000,'Graphics overlap name keyboard bank'
        rom[address:address+len(packed)]=packed
        rom[pointer:pointer+4]=struct.pack('>I',address)
    rom[0x1a4:0x1a8]=struct.pack('>I',len(rom)-1)
    apply_name_keyboard(rom,src,encode)
    apply_scenario_window(rom,src)
    title_tiles=apply_title_logo(rom,src)
    apply_title_prompt(rom,src,alternate)
    checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(0x200,len(rom),2))&65535
    rom[0x18e:0x190]=struct.pack('>H',checksum)
    dest=ROOT/'build'; dest.mkdir(exist_ok=True)
    (dest/'genghis2-ru-experimental.gen').write_bytes(rom)
    # IPS supports a ROM extension and carries no unmodified ROM content.
    ips=bytearray(b'PATCH'); i=0
    while i<len(rom):
        if i<len(src) and rom[i]==src[i]: i+=1; continue
        start=i; data=bytearray()
        while i<len(rom) and len(data)<65535 and (i>=len(src) or rom[i]!=src[i]): data.append(rom[i]); i+=1
        ips.extend(start.to_bytes(3,'big')+len(data).to_bytes(2,'big')+data)
    ips.extend(b'EOF'); (dest/'genghis2-ru-experimental.ips').write_bytes(ips)
    (dest/'applied.json').write_text(json.dumps(applied,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=dict(version='0.5.5',source_sha256=EXPECTED,font_reference_sha256=REFERENCE_SHA,rom_sha256=hashlib.sha256(rom).hexdigest(),ips_sha256=hashlib.sha256(ips).hexdigest(),rom_size=len(rom),text_replacements=len(applied),graphics_resources=['Russian title logo','Press Start prompt','title subtitle','Yes button B9','No button BA']+list(graphics),title_logo_unique_tiles=title_tiles,checksum=f'{checksum:04X}')
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Built {len(applied)} replacements; checksum {checksum:04X}; {len(rom)} bytes')

if __name__=='__main__': main()
