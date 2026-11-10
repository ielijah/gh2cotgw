"""Independent patch boundaries, native glyph layout and source integrity checks."""
from pathlib import Path
import json, hashlib, struct, re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from koei_decode import decode
ROOT=Path(__file__).resolve().parents[1]
inventory=json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
manifest=json.loads((ROOT/'build/manifest.json').read_text('utf8'))
source=(ROOT/'disc'/inventory['image']).read_bytes()
image=(ROOT/'build/genchou-hishi-ru-experimental.iso').read_bytes()
assert hashlib.sha256(source).hexdigest()==inventory['sha256']==manifest['source_sha256']
assert hashlib.sha256(image).hexdigest()==manifest['iso_sha256']
assert len(source)==inventory['size'] and len(image)==manifest['harem_success']['expanded_size']
main_file=next(f for f in inventory['files'] if f['path']=='SMAIN.PRG;1')
base=main_file['lba']*2048
FONT,TABLE,COUNT=0x37490,0x47690,2064
assert source[base+TABLE:base+TABLE+COUNT*2]==image[base+TABLE:base+TABLE+COUNT*2]
codes=struct.unpack('>2064H',source[base+TABLE:base+TABLE+COUNT*2])
allowed=bytearray(len(image))
compositor=manifest['text_compositor']
for region in compositor['storage']:
    start=base+region['offset'];length=region['length']
    assert FONT<=region['offset'] and region['offset']+length<=TABLE
    allowed[start:start+length]=b'\1'*length
expected_patches={0x7312:('4eb900010af8','4eb9'+f"{0xc000+compositor['nameplate_draw']:08x}"),0x731a:('4eb90000ff58','4eb9'+f"{0xc000+compositor['nameplate_trim']:08x}"),
                  0x4a1c:('4e56ff7c','4e56ff5c'),
                  0x4a28:('302e000a2f00','4ef9'+f"{0xc000+compositor['single_letters']['dispatch']:08x}"),
                  0x4aee:('4cee1cfcff58','4cee1cfcff38')}
assert len(compositor['patches'])==5
for patch in compositor['patches']:
    offset=patch['offset'];old,new=expected_patches[offset]
    assert (patch['before'],patch['after'])==(old,new)
    start=base+offset;length=len(bytes.fromhex(old))
    assert source[start:start+length]==bytes.fromhex(old)
    assert image[start:start+length]==bytes.fromhex(new)
    allowed[start:start+length]=b'\1'*length
single=compositor['single_letters']
expected_single={0x4abc:('4878000430390005a11e','4ef9'+f"{0xc000+single['store']:08x}"+'4e714e71'),0x3fb6:('0c1000806506','4ef9'+f"{0xc000+single['width']:08x}"),0x4b54:('302eff748046','4ef9'+f"{0xc000+single['draw']:08x}"),0x115b6:('5280','7003'),0x11bf8:('0c020020','60000052')}
for i,key in enumerate(single['keys']):
    assert key['pointer']==0x4bbe6+4*i
    expected_single[key['pointer']]=(source[base+key['pointer']:base+key['pointer']+4].hex(),struct.pack('>I',0xc000+key['offset']).hex())
assert len(single['patches'])==95
for patch in single['patches']:
    off=patch['offset'];old,new=expected_single[off];a=base+off
    assert (patch['before'],patch['after'])==(old,new)
    assert source[a:a+len(bytes.fromhex(old))]==bytes.fromhex(old)
    assert image[a:a+len(bytes.fromhex(new))]==bytes.fromhex(new)
    allowed[a:a+len(bytes.fromhex(new))]=b'\1'*len(bytes.fromhex(new))
from generated_names import patches as generated_patches
for off,old,new in generated_patches(compositor['generated_names']):
    before=bytes.fromhex(old);after=bytes.fromhex(new);a=base+off
    assert source[a:a+len(before)]==before and image[a:a+len(after)]==after
    allowed[a:a+len(after)]=b'\1'*len(after)
from catalog_list import patches as catalog_list_patches
from music_titles import patches as music_patches
from chronicle_tables import patches as chronicle_patches
from battle_text import patches as battle_patches
from map_labels import patches as map_label_patches
from harem_options import patches as harem_option_patches
for file,off,old,new in map_label_patches(compositor['map_labels'])+harem_option_patches(compositor['harem_options'])+battle_patches(compositor['battle_text'])+chronicle_patches(compositor['chronicle_tables'])+music_patches(compositor['music_titles'])+catalog_list_patches(compositor['catalog_list']):
    a=next(f['lba']*2048 for f in inventory['files'] if f['path']==file)+off
    before=bytes.fromhex(old);after=bytes.fromhex(new)
    assert source[a:a+len(before)]==before and image[a:a+len(after)]==after
    allowed[a:a+len(after)]=b'\1'*len(after)
from menu_frame import PATCHES as MENU_PATCHES, prompt_patch
MENU_PATCHES = MENU_PATCHES + (prompt_patch(compositor['start_prompt']['offset']),)
menu_base=next(f['lba']*2048 for f in inventory['files'] if f['path']=='INIT.PRG;1')
assert source[base+0x499b8:base+0x499bc]==bytes.fromhex('0014000a')
for offset,before,after in MENU_PATCHES:
    start=menu_base+offset;length=len(bytes.fromhex(before))
    assert source[start:start+length]==bytes.fromhex(before)
    assert image[start:start+length]==bytes.fromhex(after)
    allowed[start:start+length]=b'\1'*length
from menu_frame import MAIN_PATCHES
from dialogue_buffers import PATCHES as REPORT_BUFFER_PATCHES
for offset,before,after in MAIN_PATCHES + REPORT_BUFFER_PATCHES:
    start=base+offset;length=len(bytes.fromhex(before))
    assert source[start:start+length]==bytes.fromhex(before)
    assert image[start:start+length]==bytes.fromhex(after)
    allowed[start:start+length]=b'\1'*length
assert 18*2*2<=128
from text_encoding import encode as encode_prompt
prompt = compositor['start_prompt']
assert prompt['ru'] == 'Выберите\nпункт меню'
prompt_bytes = encode_prompt(prompt['ru'], {k:bytes.fromhex(v) for k,v in manifest['paired_glyphs'].items()}) + b'\0'
assert prompt['length'] == len(prompt_bytes)
assert any(r['kind']=='start_prompt' and r['offset']==prompt['offset'] and r['length']>=len(prompt_bytes) for r in compositor['storage'])
assert image[base+prompt['offset']:base+prompt['offset']+len(prompt_bytes)] == prompt_bytes
assert image[menu_base+0x1dc6:menu_base+0x1dcc] == bytes.fromhex('4879') + struct.pack('>I',0xc000+prompt['offset'])
assert image[menu_base+0x1df4:menu_base+0x1df8]==bytes.fromhex('4878000c')
for entry in manifest['applied']:
    if entry['file']=='INIT.PRG;1' and entry['offset'] in ('4E64','4E76','4E86','4E98'):
        assert max((len(line)+1)//2*2 for line in entry['ru'].split('\n'))<=18
assert 11+20<=32 and 15+10<=28
# Independently check relocated short fields and every changed pointer.
seen_refs=set()
for entry in compositor.get('relocated_texts',[]):
    f=next(x for x in inventory['files'] if x['path']==entry['file'])
    origin=f['lba']*2048;off=int(entry['offset'],16)
    if entry.get('kind')=='battle_dialogue':
        assert entry['file']=='HEX.PRG;1' and 0x13abc<=off<0x144d0
        load=0x66000;low,high=0x14b00,0x14e80
    elif entry.get('kind')=='xxx_dialogue':
        assert entry['file']=='XXX.PRG;1' and off in (0x443c,0x444a,0x4450,0x4456,0x445c)
        load=0x66000;low,high=(0xe8a,0xe8e) if off==0x443c else (0x47ea,0x47fa)
    elif entry.get('kind')=='catalog_group':
        assert entry['file']=='INIT.PRG;1' and 0x14f78<=off<=0x14f8a
        load=0x66000;low,high=0x1774e,0x17776
    elif entry.get('kind')=='music_title':
        assert entry['file']=='INIT.PRG;1' and 0x14fd4<=off<=0x1502c
        load=0x66000;low,high=0x1778a,0x177ae
    elif entry.get('kind')=='ending_caption':
        assert entry['file']=='ENDING.PRG;1' and 0x5cac<=off<0x5e72
        load=0x66000;low,high=0x5e72,0x753a
    elif entry.get('kind')=='init_chronicle_prefix':
        assert entry['file']=='INIT.PRG;1' and off==0x4c5a
        load=0x66000;low,high=0x7ca,0x7ce
    elif entry.get('kind')=='catalog_confirmation':
        assert entry['file']=='INIT.PRG;1' and off in (0x14f1a,0x14f1c)
        load=0x66000;low,high=(0x2728,0x272c) if off==0x14f1a else (0x2708,0x270c)
    elif entry['file']=='INIT.PRG;1':
        assert 0x4f00<=off<0x522a
        load=0x66000;low,high=0x16cc2,0x16f22
    elif entry.get('kind') in ('interface_label','dialogue_fragment'):
        assert entry['file']=='SMAIN.PRG;1' and (0x26f40<=off<0x2b100 or off in (0x4af4e,0x4ca46,0x4cd60))
        load=0xc000;low,high=0x4b000,0x4da00
    elif entry.get('kind')=='season':
        assert entry['file']=='SMAIN.PRG;1' and off in (0x26522,0x26526,0x2652a,0x2652e)
        load=0xc000;low,high=0x49c34,0x49c44
    else:
        assert entry['file']=='SMAIN.PRG;1' and 0x273e6<=off<=0x27500
        load=0xc000;low,high=0x4bb24,0x4bba4
    old=entry['ja'].encode('shift_jis')+b'\0'
    assert source[origin+off:origin+off+len(old)]==old
    assert image[origin+off:origin+off+len(old)]==old
    from text_encoding import encode_stream, stream_tokens
    if entry.get('native_stream'): assert stream_tokens(entry['ja'])==stream_tokens(entry['ru'])
    encoder=encode_stream if entry.get('native_stream') else encode_prompt
    encoded=encoder(entry['ru'],{k:bytes.fromhex(v) for k,v in manifest['paired_glyphs'].items()})+b'\0'
    if entry.get('kind')=='music_title':
        assert len(entry['ru'].split('\n'))<=3 and all(len(line)<=12 for line in entry['ru'].split('\n'))
    elif entry.get('kind')=='ending_caption':
        assert len(entry['ru'])<=30 and '\n' not in entry['ru']
    elif entry.get('kind') in ('dialogue_fragment','xxx_dialogue','battle_dialogue'):
        assert len(entry['ru'].split('\n'))<=4 and all((len(x)+1)//2*2<=22 for x in entry['ru'].split('\n'))
    else: assert len(entry['ru'])<=10 and '\n' not in entry['ru']
    dest=entry['storage_offset']
    assert entry['storage_length']==len(encoded)
    assert any(r['kind']=='relocated_text' and r['offset']==dest and len(encoded)<=r['length'] for r in compositor['storage'])
    assert image[base+dest:base+dest+len(encoded)]==encoded
    for ref in entry['references']:
        ptr=int(ref['offset'],16)
        assert ref['file']==entry['file'] and ptr%2==0
        if entry.get('kind')=='battle_dialogue' and not low<=ptr<high:
            assert 0<=ptr<0x13abc and source[origin+ptr-2:origin+ptr]==bytes.fromhex('4879')
        elif entry.get('kind') in ('interface_label','dialogue_fragment') and not low<=ptr<high:
            assert 0<=ptr<0x264fe and (source[origin+ptr-2:origin+ptr]==bytes.fromhex('4879') or (off,ptr)==(0x296c2,0x1f0f4) and source[origin+ptr-2:origin+ptr]==bytes.fromhex('207c'))
        else: assert low<=ptr<high
        address=origin+ptr
        assert address not in seen_refs;seen_refs.add(address)
        assert source[address:address+4]==struct.pack('>I',load+off)==bytes.fromhex(ref['before'])
        target=address
        if ref['file']=='INIT.PRG;1' and 0x16dc2<=ptr<0x16f12:
            old_index=(ptr-0x16dc2)//4
            target=origin+0x16dc2+manifest['catalog_index']['wives']['order'].index(old_index)*4
        assert image[target:target+4]==struct.pack('>I',0xc000+dest)
        allowed[address:address+4]=b'\1'*4
print(f'PASS: {len(seen_refs)} relocated name/unit pointers, original fields retained, full strings in disjoint storage')
from catalog_graphics import FIELDS,BANKS,LOAD_BASE as CAT_LOAD,pixels as catalog_pixels
catalog=manifest['catalog_graphics'];catalog_base=next(f['lba']*2048 for f in inventory['files'] if f['path']==catalog['file'])
assert [(e['offset'],e['length'],e['caption']) for e in catalog['labels']]==FIELDS
assert catalog['ranges']==[[a,n] for start,end,ptr,fields in BANKS for a,n in [(start,end-start),(ptr,4*len(fields))]]
for e in catalog['labels']:
    a=catalog_base+e['offset'];length=e['length'];assert hashlib.sha256(source[a:a+length]).hexdigest()==e['source_sha256']
    start,end,table,fields=next(b for b in BANKS if any(x[0]==e['offset'] for x in b[3]))
    index=[x[0] for x in fields].index(e['offset']);assert e['pointer_offset']==table+index*4
    assert struct.unpack_from('>I',source,catalog_base+table+index*4)[0]+CAT_LOAD==e['offset']
    ptr=struct.unpack_from('>I',image,catalog_base+table+index*4)[0]+CAT_LOAD
    assert ptr==e['new_offset'] and start<=ptr<ptr+e['compressed_size']<=end
    raw,_=decode(image[catalog_base+ptr:catalog_base+ptr+e['compressed_size']]);assert raw==catalog_pixels(e['caption']) and len(raw)==256
    assert hashlib.sha256(raw).hexdigest()==e['raw_sha256']
for off,length in catalog['ranges']:allowed[catalog_base+off:catalog_base+off+length]=b'\1'*length
assert image[catalog_base+0x30971c:catalog_base+0x309728]==source[catalog_base+0x30971c:catalog_base+0x309728]
from title_graphics import patches as title_graphic_patches
for file,off,raw in title_graphic_patches(source,{f['path']:f for f in inventory['files']}):
    start=next(f['lba']*2048 for f in inventory['files'] if f['path']==file)+off
    assert image[start:start+len(raw)]==raw
    allowed[start:start+len(raw)]=b'\1'*len(raw)
print('PASS: Russian title, subtitle and blinking prompt; relocated pointers and all five blink bounds')
from ending_graphics import patches as ending_graphic_patches
ending_base=next(f['lba']*2048 for f in inventory['files'] if f['path']=='G2GRPOE.DAT;1')
ending_ranges=list(ending_graphic_patches(source,ending_base))
assert len(ending_ranges)==10 and manifest['ending_graphics']['variants']==5
for off,raw in ending_ranges:
    start=ending_base+off
    assert image[start:start+len(raw)]==raw
    allowed[start:start+len(raw)]=b'\1'*len(raw)
print('PASS: Russian final caption in all five ending banks; native map, tile count and palette retained')
opening=manifest['opening_text']
opening_base=next(f['lba']*2048 for f in inventory['files'] if f['path']=='G2GRPOE.DAT;1')
opening_ranges={(0xf0,14*2*2),(0x128,24*3*2),(0x1b8,28*2*2),
                (0x356,0x17e*32),(7*2048,28*22*2),(7*2048+0x354c,0x263*32)}
assert {(e['offset'],e['length']) for e in opening['ranges']}==opening_ranges
for entry in opening['ranges']:
    start=opening_base+entry['offset'];length=entry['length']
    assert hashlib.sha256(source[start:start+length]).hexdigest()==entry['source_sha256']
    actual=image[start:start+length]
    assert hashlib.sha256(actual).hexdigest()==entry['sha256']
    assert actual==(ROOT/entry['asset']).read_bytes()
    allowed[start:start+length]=b'\1'*length
# Original card layout and bounds; verify paper survives outside the new ink.
from opening_text import canvas
card_offset=opening_base+7*2048
before=canvas(source,card_offset,28,22,source[card_offset+0x354c:card_offset+0x81ac],0x200)
after=canvas(image,card_offset,28,22,image[card_offset+0x354c:card_offset+0x81ac],0x200)
assert all(b==3 or b==(6 if a==3 else a) for ar,br in zip(before,after) for a,b in zip(ar,br))
# No tiles used by the unchanged publisher logo/animation maps are touched.
caption_positions={p for off,w,h in ((0xf0,14,2),(0x128,24,3),(0x1b8,28,2)) for p in range(off,off+w*h*2,2)}
for pos in range(0,0x356,2):
    if pos in caption_positions: continue
    tile=int.from_bytes(source[opening_base+pos:opening_base+pos+2],'big')&0x7ff
    if 0x2c0<=tile<0x43e:
        start=opening_base+0x356+(tile-0x2c0)*32
        assert source[start:start+32]==image[start:start+32]
print('PASS: wider start-menu bounds, opening graphic ranges, parchment background and unchanged logo tiles')
buttons=manifest['buttons']
graphic_file=next(f for f in inventory['files'] if f['path']==buttons['file'])
graphic_base=graphic_file['lba']*2048
start=graphic_base+buttons['allowed_offset'];length=buttons['allowed_length']
allowed[start:start+length]=b'\1'*length
button_reference=json.loads((ROOT/'translation/buttons.json').read_text('utf8'))
modified={int(e['resource'],16):e for e in button_reference['entries']}
compact=json.loads((ROOT/'assets/button-compact-font.json').read_text('utf8'))
adapted_count=0
for n in range(255):
    before=struct.unpack_from('>I',source,graphic_base+0x939c+n*4)[0]-0xb2800
    after=struct.unpack_from('>I',image,graphic_base+0x939c+n*4)[0]-0xb2800
    old,_=decode(source[graphic_base+before:]);new,_=decode(image[graphic_base+after:])
    if n in modified:
        assert new==(ROOT/modified[n]['file']).read_bytes(),n
        assert len(new)==len(old),n
        if modified[n].get('disabled_keyboard_tab'):
            assert n in (5,6) and new==bytes([0x99])*128
        else: assert {v for b in new for v in(b>>4,b&15)}=={v for b in old for v in(b>>4,b&15)},n
        adaptation=modified[n].get('adaptation')
        if adaptation:
            adapted_count+=1
            assert len(new)==128 and adaptation['layout']=='two-line native 16x16'
            def pixel(blob,x,y):
                offset=(y//8*2+x//8)*32+y%8*4+x%8//2
                return (blob[offset]>>(4 if x%2==0 else 0))&15
            assert all(pixel(old,0,y)==pixel(new,0,y) for y in range(16))
            assert all(pixel(old,x,15)==pixel(new,x,15) for x in range(16))
            for top,line in zip((0,8),adaptation['lines']):
                width=sum(len(compact[ch][0]) for ch in line)+len(line)-1
                assert width<=15
                left=1+(15-width)//2
                for ch in line:
                    for y,row in enumerate(compact[ch]):
                        assert all(pixel(new,left+x,top+y)==(14 if bit=='1' else 9) for x,bit in enumerate(row))
                    left+=len(compact[ch][0])+1
    else:assert new==old,n
assert len(modified)==buttons['modified_count']
from catalog_index import START as CAT_REC, COUNT as CAT_COUNT, STRIDE as CAT_STRIDE, BIO as CAT_BIO, COUNTS as CAT_COUNTS, plan as catalog_plan
order,counts,names=catalog_plan(manifest['applied']);assert manifest['catalog_index']['order']==order and manifest['catalog_index']['counts']==counts
assert sorted(order)==list(range(342))
cat_base=menu_base
bank=manifest['biography_bank']
assert (bank['start'],bank['end'])==(0x522a,0x14f1a)
bio_entries={int(e['offset'],16):e for e in manifest['applied'] if e['file']=='INIT.PRG;1'}
original_bios=struct.unpack_from('>453I',source,cat_base+0x16fba)
assert len(bank['records'])==453 and len(set(original_bios))==453
cursor=0x522a
bio_pointers=[]
for ptr,record in zip(original_bios,bank['records']):
    assert record['source_offset']==ptr-0x66000 and record['offset']==cursor
    entry=bio_entries[ptr-0x66000]
    raw=encode_prompt(entry['ru'],{k:bytes.fromhex(v) for k,v in manifest['paired_glyphs'].items()})+b'\0'
    assert record['length']==len(raw) and int(entry['destination_offset'],16)==cursor
    assert image[cat_base+cursor:cat_base+cursor+len(raw)]==raw
    bio_pointers.append(0x66000+cursor)
    cursor+=len(raw)
assert cursor<=0x14f1a and bank['free']==0x14f1a-cursor and bank['used']==cursor-0x522a
traits=manifest['women_traits']
assert cursor<=traits['table']<traits['helper']<traits['end']<=0x14f1a
assert image[cat_base+traits['end']:cat_base+0x14f1a]==bytes(0x14f1a-traits['end'])
from women_traits import texts as inheritance_texts
assert len(traits['records'])==84
for record,text in zip(traits['records'],inheritance_texts()):
    raw=encode_prompt(text,{k:bytes.fromhex(v) for k,v in manifest['paired_glyphs'].items()})+b'\0'
    assert record['text']==text and record['length']==len(raw)
    assert image[cat_base+record['offset']:cat_base+record['offset']+len(raw)]==raw
for dest,old in enumerate(manifest['catalog_index']['wives']['order']):
    assert struct.unpack_from('>I',image,cat_base+traits['table']+dest*4)[0]==0x66000+traits['records'][old]['offset']
for off,old,new in traits['patches']:
    assert source[cat_base+off:cat_base+off+len(bytes.fromhex(old))]==bytes.fromhex(old)
    assert image[cat_base+off:cat_base+off+len(bytes.fromhex(new))]==bytes.fromhex(new)
    allowed[cat_base+off:cat_base+off+len(bytes.fromhex(new))]=b'\1'*len(bytes.fromhex(new))
assert image[cat_base+traits['helper']:cat_base+traits['end']]==bytes.fromhex(traits['code'])
allowed[cat_base+0x522a:cat_base+0x14f1a]=b'\1'*(0x14f1a-0x522a)
allowed[cat_base+0x16fba:cat_base+0x176ce]=b'\1'*(453*4)
assert struct.unpack_from('>27I',image,cat_base+0x17662)==tuple(bio_pointers[426:])
print(f'PASS: all 453 biographies repacked, {bank["free"]} bytes spare; children retain matching pointers')
for dest,old in enumerate(order):
    a=cat_base+CAT_REC+dest*20;b=cat_base+CAT_REC+old*20
    assert image[a+16:a+20]==source[b+16:b+20], 'Portrait and attributes changed'
    assert struct.unpack_from('>I',image,cat_base+CAT_BIO+dest*4)[0]==bio_pointers[old], 'Biography mismatch'
assert image[cat_base+CAT_COUNTS:cat_base+CAT_COUNTS+10]==bytes(counts)
for off,size in [(CAT_REC,CAT_COUNT*20),(CAT_BIO,CAT_COUNT*4),(CAT_COUNTS,10)]:allowed[cat_base+off:cat_base+off+size]=b'\1'*size
from catalog_index import wives_plan, WIFE_NAMES, WIFE_PORTRAITS, WIFE_BIOS, WIFE_COUNTS, WIFE_COUNT
wo,wc,wn=wives_plan(source,{f['path']:f for f in inventory['files']},manifest['applied'],compositor['relocated_texts'])
assert manifest['catalog_index']['wives']==dict(order=wo,counts=wc,names=[wn[i] for i in wo])
assert sorted(wo)==list(range(84))
expected_names=bytearray(source[cat_base+WIFE_NAMES:cat_base+WIFE_NAMES+336])
for entry in compositor['relocated_texts']:
    for ref in entry['references']:
        off=int(ref['offset'],16)
        if ref['file']=='INIT.PRG;1' and WIFE_NAMES<=off<WIFE_NAMES+336:
            struct.pack_into('>I',expected_names,off-WIFE_NAMES,0xc000+entry['storage_offset'])
for table,stride in [(WIFE_NAMES,4),(WIFE_PORTRAITS,2),(WIFE_BIOS,4)]:
    original=expected_names if table==WIFE_NAMES else struct.pack('>84I',*bio_pointers[342:426]) if table==WIFE_BIOS else source[cat_base+table:cat_base+table+84*stride]
    for dest,old in enumerate(wo):
        assert image[cat_base+table+dest*stride:cat_base+table+(dest+1)*stride]==original[old*stride:(old+1)*stride]
    allowed[cat_base+table:cat_base+table+84*stride]=b'\1'*(84*stride)
assert image[cat_base+WIFE_COUNTS:cat_base+WIFE_COUNTS+10]==bytes(wc)
allowed[cat_base+WIFE_COUNTS:cat_base+WIFE_COUNTS+10]=b'\1'*10
print('PASS: all 84 wives sorted in Russian groups; name, portrait and biography identities preserved')
for entry in manifest['applied']:
    item=next(f for f in inventory['files'] if f['path']==entry['file'])
    offset=item['lba']*2048+int(entry.get('destination_offset',entry['offset']),16)
    length=(entry['translated_bytes'] if entry['file']=='INIT.PRG;1' and 0x522a<=int(entry['offset'],16)<0x14f1a else entry['original_bytes'])+1
    allowed[offset:offset+length]=b'\1'*length
    assert image[offset+entry['translated_bytes']]==0
    if entry.get('native_stream'):
        from text_encoding import encode_stream
        pattern=r'\x1b[CB][0-9A-F]|%[0-9]*[ds]'
        assert re.findall(pattern,entry['ja'])==re.findall(pattern,entry['ru'])
        expected=encode_stream(entry['ru'],{k:bytes.fromhex(v) for k,v in manifest['paired_glyphs'].items()})
        assert image[offset:offset+entry['translated_bytes']]==expected
        assert re.findall(rb'\x1b[CB][0-9A-F]|%[0-9]*[ds]',expected)==[t.encode('ascii') for t in re.findall(pattern,entry['ja'])]
        continue
    encoded=[]
    formatted=entry.get('native_decimal_format',False)
    if formatted:
        assert re.findall(r'%[0-9]*d',entry['ja'])==re.findall(r'%[0-9]*d',entry['ru'])
        assert '%' not in re.sub(r'%[0-9]*d','',entry['ru'])
    for line in entry['ru'].split('\n'):
        parts=[]
        chunks=re.split(r'(%[0-9]*d)',line) if formatted else [line]
        for k,chunk in enumerate(chunks):
            if formatted and re.fullmatch(r'%[0-9]*d',chunk):
                parts.append(chunk.encode('ascii'));continue
            tail=''
            if len(chunk)%2:
                if formatted and chunk[-1] in '0123456789/ ?,CIVX-!.:;()':chunk,tail=chunk[:-1],chunk[-1]
                else:
                    assert not formatted or k==len(chunks)-1
                    chunk+=' '
            for n in range(0,len(chunk),2):
                pair=chunk[n:n+2]
                parts.append(pair.encode('ascii') if all(c in '0123456789/ ?,CIVX-!.:;()' for c in pair)
                             else bytes.fromhex(manifest['paired_glyphs'][pair]))
            parts.append(tail.encode('ascii'))
        encoded.append(b''.join(parts))
    expected=b'\n'.join(encoded)
    if entry.get('native_prefix'):
        assert entry['native_prefix']=='1b4232' and entry['ja'].startswith('\x1bB2')
        expected=b'\x1bB2'+expected
    if entry['ja'].endswith('\x1bW'): expected+=b'\x1bW'
    assert image[offset:offset+entry['translated_bytes']]==expected,entry

from harem_cards import verify as verify_harem_success
verify_harem_success(source,image,{f['path']:f for f in inventory['files']},manifest['harem_success'])
for off,length in manifest['harem_success']['ranges']:
    allowed[off:off+length]=b'\1'*length
assert all(old==new or permit for old,new,permit in zip(source,image,allowed))
assert all(allowed[len(source):]), 'Unaccounted ISO extension'
font=(ROOT/'assets/cyrillic-8x16.bin').read_bytes()
alphabet=''.join(chr(ord('А')+n) for n in range(64))+'Ёё'
rows={ch:font[n*16:(n+1)*16] for n,ch in enumerate(alphabet)}
rows[' ']=bytes(16)
# Independent explicit native indices, including all supported punctuation.
for ch,index in {',':0xe8,'?':0xee,'!':0xe1,'.':0x06,':':0xe9,';':0xea,
                 '(':0x01,')':0x02,'/':0x07,'-':0x05,'C':0x14,'I':0x1a,'V':0x27,'X':0x29,
                 **{str(n):0x08+n for n in range(10)}}.items():
    rows[ch]=source[base+0x36490+index*16:base+0x36490+(index+1)*16]
changed_codes={codes[(offset-FONT)//32]
               for region in compositor['storage']
               for offset in range(region['offset'],region['offset']+region['length'],32)}
# Independently check that repurposed codes have no static references in
# retained program bytes. Also reject overlapping text patches.
programs=[]
for item in inventory['files']:
    if not item['path'].endswith('.PRG;1'): continue
    origin=item['lba']*2048
    program=bytearray(source[origin:origin+item['size']])
    spans=[]
    for entry in manifest['applied']:
        if entry['file']!=item['path']: continue
        start=int(entry['offset'],16);end=start+entry['original_bytes']+1
        padding=entry.get('original_padding_bytes',0)
        raw=entry['ja'].encode('shift_jis')
        if padding:
            if item['path']=='INIT.PRG;1':
                assert 0x15232<=start<0x16ce6 and (start-0x15232)%20==0
                limit=entry.get('name_capacity',10);assert limit in (10,14)
                assert padding==limit-len(raw)>0
                assert program[start:start+limit+1]==raw+bytes(limit+1-len(raw))
                assert program[start:start+14]==raw+bytes(14-len(raw))
            else:
                from scenario_names import valid_offset, valid_country_offset, valid_province_offset
                country=entry.get('kind')=='scenario_country'
                limit=16 if country else 14
                assert item['path']=='SMAIN.PRG;1' and (valid_country_offset(start) if country else valid_province_offset(start) if entry.get('kind')=='province' else valid_offset(start))
                assert padding==limit-len(raw)>0 and len(entry['ru'])<=limit
                assert program[start:start+limit+1]==raw+bytes(limit+1-len(raw))
                assert image[origin+start+limit+1:origin+start+limit+2]==program[start+limit+1:start+limit+2]
        assert program[start:end]==raw+b'\0'+bytes(padding)
        spans.append((start,end))
        if 'max_lines' in entry:
            assert len(entry['ru'].split('\n'))<=entry['max_lines']
        if 'max_columns' in entry:
            assert all((len(line)+1)//2*2<=entry['max_columns'] for line in entry['ru'].split('\n'))
    spans.sort()
    assert all(a[1]<=b[0] for a,b in zip(spans,spans[1:])),item['path']
    for start,end in spans: program[start:end]=bytes(end-start)
    if item['path']=='SMAIN.PRG;1': program[0x36490:TABLE+COUNT*2]=bytes(TABLE+COUNT*2-0x36490)
    programs.append(program)
retained=b''.join(programs)
assert all(code.to_bytes(2,'big') not in retained for code in changed_codes)
print('PASS: retained static font references, disjoint text slots and declared menu widths')
for n,code in enumerate(codes):
    offset=base+FONT+n*32
    if code not in changed_codes: assert source[offset:offset+32]==image[offset:offset+32]
for ch,address in zip(compositor['alphabet'],compositor['character_addresses']):
    if ch in rows: assert image[base+address:base+address+16]==rows[ch],ch
from test_text_compositor import check
check(ROOT,source,image,base,manifest)
for track in inventory['tracks']:
    path=ROOT/'disc'/track['name']
    with path.open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==track['sha256'],track['name']
assert manifest['audio_tracks_modified']==0
print('PASS: allowed patch ranges, verified ISO directory extension and code outside verified renderer/menu patches, native font table, original Japanese glyphs outside declared substitutions, exact Cyrillic pixels, all source-track hashes')
print(f'PASS: {len(modified)} translated graphics, including {sum(e.get("origin")=="sega-cd-harem" for e in modified.values())} native harem labels and {adapted_count} two-line adaptations; all {255-len(modified)} other resources unchanged')

# Validate the actual launch packages, not only the patched ISO.
import re
for mode in ('japanese-audio','dub'):
    folder=ROOT/'build'/('playable-'+mode)
    if not folder.exists(): continue
    records=json.loads((folder/'tracks.json').read_text('utf8'))
    cue=(folder/'game.cue').read_text('ascii')
    names=re.findall(r'FILE "([^"]+)"',cue)
    assert len(names)==len(records)==90
    assert re.findall(r'TRACK (\d+)',cue)==[f'{n:02}' for n in range(1,91)]
    originals=[t for t in inventory['tracks'] if t['name'].lower().endswith(('.iso','.wav'))]
    for n,(name,record,original) in enumerate(zip(names,records,originals),1):
        assert Path(name).name==name and name==record['file']
        with (folder/name).open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
        assert digest==record['sha256']
        if n==1: assert digest==manifest['iso_sha256']
        elif mode=='dub' and (n<=79 or n==90):
            with (ROOT/f'build/audio-ru/track{n:02}-ru.wav').open('rb') as stream:
                assert digest==hashlib.file_digest(stream,'sha256').hexdigest()
        else: assert digest==original['sha256']
    print(f'PASS: {mode}: 90 flat CUE files, package hashes, unchanged approved audio')

# Narration replaces only the spoken intro section, without moving CD boundaries.
import wave
intro=json.loads((ROOT/'build/audio-ru/intro-manifest.json').read_text('utf8'))
original=next((ROOT/'disc').glob('*(Track 90 of*wav'))
translated=ROOT/'build/audio-ru/track90-ru.wav'
assert hashlib.sha256(original.read_bytes()).hexdigest()==intro['source_sha256']
assert hashlib.sha256(translated.read_bytes()).hexdigest()==intro['sha256']
with wave.open(str(original)) as a, wave.open(str(translated)) as b:
    assert a.getparams()==b.getparams()
    assert b.getnframes()%588==0 and b.getnframes()==intro['frames']
    start,end=(round(t*44100) for t in intro['modified_seconds'])
    assert a.readframes(start)==b.readframes(start)
    a.setpos(end);b.setpos(end)
    assert a.readframes(a.getnframes()-end)==b.readframes(b.getnframes()-end)
assert all(x['end']<=y['start'] for x,y in zip(intro['cues'],intro['cues'][1:]))
assert intro['peak']<1
print('PASS: intro CD frames unchanged; PCM outside narration unchanged; no clipping or overlapping clauses')

from dialogue_buffers import PATCHES as REPORT_BUFFER_PATCHES
main_base=next(f['lba']*2048 for f in inventory['files'] if f['path']=='SMAIN.PRG;1')
for off,before,after in REPORT_BUFFER_PATCHES:
    assert image[main_base+off:main_base+off+len(bytes.fromhex(after))]==bytes.fromhex(after)
print('PASS: resource-report stack buffers and saved-register offsets')
