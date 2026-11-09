"""Experimental, size-preserving SEGA CD patch. Source images remain local."""
from pathlib import Path
import hashlib, json, struct, re, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_buttons import apply as apply_buttons

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
OUT = ROOT/'build'
OUT.mkdir(exist_ok=True)
inventory = json.loads((ROOT/'analysis/disc-inventory.json').read_text('utf8'))
source = (ROOT/'disc'/inventory['image']).read_bytes()
assert hashlib.sha256(source).hexdigest() == inventory['sha256']
image = bytearray(source)
files = {f['path']: f for f in inventory['files']}
def payload(name):
    f = files[name]
    return source[f['lba']*2048:f['lba']*2048+f['size']]

# SMAIN loads at C000: the renderer at file 4A1C searches the sorted
# Shift-JIS table at CPU 53690 and reads four 1bpp tiles at CPU 43490.
main = bytearray(payload('SMAIN.PRG;1'))
assert main[0x4a34:0x4a3a] == bytes.fromhex('263c00043490')
assert main[0x49fc:0x4a02] == bytes.fromhex('207c00053690')
FONT, TABLE, COUNT = 0x37490, 0x47690, 2064
codes = list(struct.unpack('>'+str(COUNT)+'H', main[TABLE:TABLE+COUNT*2]))
assert codes == sorted(set(codes))
# Conservative static exclusion: candidate codes must not occur anywhere in
# retained executable/overlay bytes outside replaced text and the font tables. This is not
# a proof for dynamically assembled text or resource banks; emulator QA remains required.
alphabet = ''.join(chr(ord('А')+n) for n in range(64))+'Ёё'
font_path = ROOT/'assets'/'cyrillic-8x16.bin'
font = font_path.read_bytes()
assert len(font)==66*16
reuse = json.loads((ROOT/'analysis/mega-drive-reuse.json').read_text('utf8'))
assert hashlib.sha256(font).hexdigest()==reuse['fonts']['regular']['sha256'], 'Mega Drive font provenance mismatch'
md_reference=json.loads((ROOT/'translation/mega-drive-reference.json').read_text('utf8'))
translations = json.loads((ROOT/'translation/interface.json').read_text('utf8'))
translations.extend(json.loads((ROOT/'translation/harem-screen.json').read_text('utf8')))
translations.extend(json.loads((ROOT/'translation/harem-ui.json').read_text('utf8')))
translations.extend(json.loads((ROOT/'translation/gameplay-dialogue.json').read_text('utf8')))
# Do not reserve Japanese glyphs solely referenced by text slots that are
# replaced in this very build. Keep every byte of other text/code in the scan.
search_parts=[]
for name in files:
    if not name.endswith('.PRG;1'): continue
    part=bytearray(payload(name))
    for entry in translations:
        if entry['file']!=name: continue
        offset=int(entry['offset'],16)
        original=entry['ja'].encode('shift_jis')+b'\0'+bytes(entry.get('original_padding_bytes',0))
        assert part[offset:offset+len(original)]==original, entry
        part[offset:offset+len(original)]=bytes(len(original))
    if name=='SMAIN.PRG;1':
        part[0x36490:TABLE+COUNT*2]=bytes(TABLE+COUNT*2-0x36490)
    search_parts.append(part)
search=b''.join(search_parts)
unused=[code for code in codes if code>=0x889f and code.to_bytes(2,'big') not in search]
assert len(unused)>=len(alphabet)
for entry in translations:
    if 'md_key' in entry:
        assert entry['ru']==md_reference[entry['md_section']][entry['md_key']], entry
letter_rows = {ch:font[n*16:(n+1)*16] for n,ch in enumerate(alphabet)}
letter_rows[' '] = bytes(16)
# Reuse the original half-width punctuation/digits. Native table indices are
# defined by the ASCII branch at SMAIN 4B96..4C7C, not by Unicode values.
for ch in ',?!.:;()0123456789/CIVX-':
    value=ord(ch)
    delta = 0xc0 if 0x21<=value<=0x27 else 0xd9 if 0x28<=value<=0x2b else 0xbc if ch==',' else 0xaf if 0x3a<=value<=0x3f else 0xd1 if ch in 'CIVX' else 0xd8
    index = (value+delta)&255
    letter_rows[ch] = bytes(main[0x36490+index*16:0x36490+(index+1)*16])
# Digits, slash and spaces already have the same native half-width pixels.
# Two native bytes occupy the same 16px as a paired glyph, without consuming
# another Japanese font slot. Keep Cyrillic pairs on the imported font.
from text_encoding import pieces, encode, decimal_tokens
native_pair = lambda pair: all(ch in '0123456789/ ?,CIVX-!.:;()' for ch in pair)
pairs = []
for entry in translations:
    formatted=entry.get('native_decimal_format',False)
    if formatted: assert decimal_tokens(entry['ja'])==decimal_tokens(entry['ru']),entry
    else: assert '%' not in entry['ru']
    if 'max_lines' in entry:
        assert len(entry['ru'].split('\n'))<=entry['max_lines'], entry
    if 'max_columns' in entry:
        assert all((len(line)+1)//2*2<=entry['max_columns'] for line in entry['ru'].split('\n')), entry
    for kind,value in pieces(entry['ru'],formatted):
        if kind=='pair':
            assert all(ch in letter_rows for ch in value),value
            if value not in pairs:pairs.append(value)
from text_compositor import install
compositor, pair_codes = install(main, codes, unused, pairs, letter_rows)
replaced = []

def encode_text(text, formatted=False):
    return encode(text,pair_codes,formatted)
start = files['SMAIN.PRG;1']['lba']*2048
image[start:start+len(main)] = main
applied = []
for entry in translations:
    f = files[entry['file']]
    original = payload(entry['file'])
    old = entry['ja'].encode('shift_jis')
    padding=entry.get('original_padding_bytes',0)
    if padding:
        position=int(entry['offset'],16)
        assert entry['file']=='INIT.PRG;1' and 0x15232<=position<0x16cc2 and (position-0x15232)%20==0
        assert padding==10-len(old)>0
        assert original[position:position+14]==old+bytes(14-len(old)), entry
        old+=bytes(padding)
    new = encode_text(entry['ru'],entry.get('native_decimal_format',False))
    controls = re.findall(b'\x1b(.)',old)
    if entry.get('native_prefix'):
        prefix=bytes.fromhex(entry['native_prefix'])
        assert prefix==b'\x1bB2' and old.startswith(prefix) and controls.count(b'B')==1, entry
        new=prefix+new
        controls.remove(b'B')
    assert all(code in (b'K',b'H',b'W') for code in controls), entry
    if b'W' in controls:
        assert old.endswith(b'\x1bW') and controls.count(b'W')==1, entry
        new += b'\x1bW'  # Preserve the original wait command, not just its text.
    offset = int(entry['offset'],16)
    assert original[offset:offset+len(old)+1] == old+b'\0', entry
    assert len(new)<=len(old), (entry,len(new),len(old))
    address = f['lba']*2048+offset
    image[address:address+len(old)+1] = new+bytes(len(old)+1-len(new))
    applied.append(dict(**entry, original_bytes=len(old), translated_bytes=len(new)))
from menu_frame import apply as apply_menu_frame
menu_frame=apply_menu_frame(image,source,files)
from opening_text import apply as apply_opening
opening_text=apply_opening(image,source,files)
buttons=apply_buttons(image,source,files)
assert len(image)==len(source)
# Encode and replay standard IPS. No source file is included in the patch.
patch = bytearray(b'PATCH')
pos = 0
while pos<len(source):
    if source[pos]==image[pos]: pos+=1; continue
    start=pos
    while pos<len(source) and source[pos]!=image[pos] and pos-start<65535: pos+=1
    patch += start.to_bytes(3,'big')+(pos-start).to_bytes(2,'big')+image[start:pos]
patch += b'EOF'
replayed=bytearray(source);pos=5
while patch[pos:pos+3]!=b'EOF':
    address=int.from_bytes(patch[pos:pos+3],'big');size=int.from_bytes(patch[pos+3:pos+5],'big');pos+=5
    replayed[address:address+size]=patch[pos:pos+size];pos+=size
assert replayed==image
stem='genchou-hishi-ru-experimental'
(OUT/(stem+'.iso')).write_bytes(image)
(OUT/(stem+'.ips')).write_bytes(patch)
report=dict(version='0.0.5-experimental', source_sha256=inventory['sha256'],
            iso_sha256=hashlib.sha256(image).hexdigest(), ips_sha256=hashlib.sha256(patch).hexdigest(),
            iso_size=len(image), audio_tracks_modified=0, applied=applied, glyph_replacements=replaced,
            paired_glyphs={pair:code.hex() for pair,code in pair_codes.items()},buttons=buttons,
            text_compositor=compositor, menu_frame=menu_frame, opening_text=opening_text,
            limitations=['8px glyphs packed in native 16px cells; UI width must be checked.',
                         'Compositor and font data occupy statically unused glyph cells; dynamic/resource usage not proven.',
                         'Partial interface and harem dialogue translation.'])
(OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(f'PASS: IPS replay, fixed ISO size, {len(applied)} strings, 66 source Cyrillic glyphs, {len(pairs)} pairs; CDDA unchanged')

from package_disc import package
package('japanese-audio')
if all((OUT/f'audio-ru/track{n:02}-ru.wav').is_file() for n in range(2,80)):
    package('dub')
for old_name in ('genchou-hishi-ru-experimental.cue','genchou-hishi-ru-dub.cue'):
    old=OUT/old_name
    if old.exists(): old.replace(OUT/(old_name+'.disabled'))
