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
assert len(source)==len(image)==inventory['size']
main_file=next(f for f in inventory['files'] if f['path']=='SMAIN.PRG;1')
base=main_file['lba']*2048
FONT,TABLE,COUNT=0x37490,0x47690,2064
assert source[base+TABLE:base+TABLE+COUNT*2]==image[base+TABLE:base+TABLE+COUNT*2]
codes=struct.unpack('>2064H',source[base+TABLE:base+TABLE+COUNT*2])
allowed=bytearray(len(source))
compositor=manifest['text_compositor']
for region in compositor['storage']:
    start=base+region['offset'];length=region['length']
    assert FONT<=region['offset'] and region['offset']+length<=TABLE
    allowed[start:start+length]=b'\1'*length
expected_patches={0x4a1c:('4e56ff7c','4e56ff5c'),
                  0x4a28:('302e000a2f00','4ef9'+f"{0xc000+compositor['hook']:08x}"),
                  0x4aee:('4cee1cfcff58','4cee1cfcff38')}
assert len(compositor['patches'])==3
for patch in compositor['patches']:
    offset=patch['offset'];old,new=expected_patches[offset]
    assert (patch['before'],patch['after'])==(old,new)
    start=base+offset;length=len(bytes.fromhex(old))
    assert source[start:start+length]==bytes.fromhex(old)
    assert image[start:start+length]==bytes.fromhex(new)
    allowed[start:start+length]=b'\1'*length
from menu_frame import PATCHES as MENU_PATCHES
menu_base=next(f['lba']*2048 for f in inventory['files'] if f['path']=='INIT.PRG;1')
assert source[base+0x499b8:base+0x499bc]==bytes.fromhex('0014000a')
for offset,before,after in MENU_PATCHES:
    start=menu_base+offset;length=len(bytes.fromhex(before))
    assert source[start:start+length]==bytes.fromhex(before)
    assert image[start:start+length]==bytes.fromhex(after)
    allowed[start:start+length]=b'\1'*length
from menu_frame import MAIN_PATCHES
for offset,before,after in MAIN_PATCHES:
    start=base+offset;length=len(bytes.fromhex(before))
    assert source[start:start+length]==bytes.fromhex(before)
    assert image[start:start+length]==bytes.fromhex(after)
    allowed[start:start+length]=b'\1'*length
assert 18*2*2<=128
assert image[menu_base+0x1df4:menu_base+0x1df8]==bytes.fromhex('4878000c')
for entry in manifest['applied']:
    if entry['file']=='INIT.PRG;1' and entry['offset'] in ('4E64','4E76','4E86','4E98'):
        assert max((len(line)+1)//2*2 for line in entry['ru'].split('\n'))<=18
assert 11+20<=32 and 15+10<=28
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
        assert {v for b in new for v in(b>>4,b&15)}=={v for b in old for v in(b>>4,b&15)},n
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
for entry in manifest['applied']:
    item=next(f for f in inventory['files'] if f['path']==entry['file'])
    offset=item['lba']*2048+int(entry['offset'],16)
    length=entry['original_bytes']+1
    allowed[offset:offset+length]=b'\1'*length
    assert image[offset+entry['translated_bytes']]==0
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

assert all(old==new or permit for old,new,permit in zip(source,image,allowed))
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
            assert item['path']=='INIT.PRG;1' and 0x15232<=start<0x16cc2 and (start-0x15232)%20==0
            assert padding==10-len(raw)>0
            assert program[start:start+14]==raw+bytes(14-len(raw))
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
print('PASS: allowed patch ranges, unchanged ISO metadata and code outside verified renderer/menu patches, native font table, original Japanese glyphs outside declared substitutions, exact Cyrillic pixels, all source-track hashes')
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
