"""Verify IPS replay, ROM header, renderer hooks and translated payloads."""
from pathlib import Path
import struct,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import encode,EXPECTED
from import_font import pack_static,REFERENCE_SHA
from graphics_codec import decode,encode_literals
from menu_graphics import address as graphic_address
src=(ROOT/'rom/original.gen').read_bytes()
assert hashlib.sha256(src).hexdigest()==EXPECTED
rom=(ROOT/'build/genghis2-ru-experimental.gen').read_bytes()
patch=(ROOT/'build/genghis2-ru-experimental.ips').read_bytes()
assert patch.startswith(b'PATCH')
rebuilt=bytearray(src); pos=5; records=0
while patch[pos:pos+3]!=b'EOF':
    off=int.from_bytes(patch[pos:pos+3],'big'); count=int.from_bytes(patch[pos+3:pos+5],'big'); pos+=5
    assert count>0
    if len(rebuilt)<off+count: rebuilt.extend(bytes(off+count-len(rebuilt)))
    rebuilt[off:off+count]=patch[pos:pos+count];pos+=count;records+=1
assert bytes(rebuilt)==rom,'IPS replay differs from built ROM'
assert int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
assert sum(int.from_bytes(rom[i:i+2],'big') for i in range(0x200,len(rom),2))&65535==int.from_bytes(rom[0x18e:0x190],'big')
applied=json.loads((ROOT/'build/applied.json').read_text(encoding='utf-8'))
for item in applied:
    off=int(item['offset'],16); text=encode(item['ru'])
    assert rom[off:off+len(text)]==text,item
    if item.get('terminate'): assert rom[off+len(text)]==0,item
    if item.get('kind')=='field':
        assert rom[off+len(text):off+item['capacity']]==bytes(item['capacity']-len(text))
        following=off+item['capacity']
        next_field=next((entry for entry in applied if int(entry['offset'],16)==following),None)
        assert rom[following]==(encode(next_field['ru'])[0] if next_field else src[following])
    elif item.get('kind')=='relocated':
        assert rom[off+len(text)]==0
        old=int(item['source_offset'],16)
        assert src[old:old+len(item['en'])+1]==item['en'].encode('ascii')+b'\0'
        for ref in item['references']:assert int.from_bytes(rom[int(ref,16):int(ref,16)+4],'big')==off
    else: assert rom[off+len(item['en'])]==src[off+len(item['en'])]
assert rom[0x5e3e:0x5e44].hex()=='4ef900100400'
assert rom[0x5d08:0x5d0e].hex()=='4ef900100e00'
assert rom[0x5c10:0x5c18].hex()=='4ef900100c004e71'
assert rom[0xd12c2:0xd14a2]!=src[0xd12c2:0xd14a2]
assert rom[0x5e7c:0x5e7e].hex()=='2004','Glyph index must replace all of D0'
graphics=json.loads((ROOT/'translation/graphics.json').read_text(encoding='utf-8'))
resources=[(0xb9,0x102000),(0xba,0x102200)]+[(int(key,16),graphic_address(i,int(key,16))) for i,key in enumerate(graphics)]
for resource,address in resources:
    table=0xa663c+resource*4
    assert int.from_bytes(rom[table:table+4],'big')==address
    decoded,_=decode(rom[address:])
    original,_=decode(src[int.from_bytes(src[table:table+4],'big'):])
    assert len(decoded)==len(original)
    assert decoded!=original
    if 0x9a<=resource<=0x9f:
        def pixel(data,x,y):
            return (data[(y//8*4+x//8)*32+y%8*4+x%8//2]>>(4 if x%2==0 else 0))&15
        assert {v for byte in decoded for v in (byte>>4,byte&15)}=={8,10,15}
        for y in range(16): assert pixel(decoded,0,y)==pixel(original,0,y)
        for x in range(32): assert pixel(decoded,x,15)==pixel(original,x,15)

for size in (0,1,7,8,9,255,256):
    data=bytes(i%256 for i in range(size))
    assert decode(encode_literals(data))[0]==data
reference=next((ROOT/'rom/reference').glob('*.md')).read_bytes()
assert hashlib.sha256(reference).hexdigest()==REFERENCE_SHA
font,alternate,packed,latin,cyr=pack_static(reference,src)
assert rom[0x104000:0x105800]==packed
alphabet=''.join(chr(ord('А')+i) for i in range(64))+'Ёё'
for index,ch in enumerate(alphabet):
    assert rom[0x103000+index*16:0x103010+index*16]==font[ch]
    assert rom[0x103500+index*16:0x103510+index*16]==alternate[ch]
    pair=struct.unpack('>HH',rom[0x105b00+index*4:0x105b04+index*4]);assert list(pair)==cyr[index]
    rebuilt=bytearray()
    for tile in pair:
        assert 0x40<=tile<0x100
        raw=rom[0x104000+(tile-0x40)*32:0x104020+(tile-0x40)*32]
        for y in range(8):
            row=0
            for x in range(8):
                nibble=(raw[y*4+x//2]>>(4 if x%2==0 else 0))&15
                assert nibble in (0,15)
                if nibble:row|=128>>x
            rebuilt.append(row)
    assert bytes(rebuilt)==font[ch],ch
assert encode('Ёё')==bytes([0x1c,0x7f])
print(f'PASS: IPS replay ({records} records), hashes, checksum, {len(applied)} translations, relocations, both reference fonts, 66 permanent glyphs, compressed buttons')

# Every province and every generator table entry now points to translated text.
for start,count,stride in ((0x48dd2,14,15),(0x48fc1,33,15)):
    for i in range(count):
        value=rom[start+i*stride:start+(i+1)*stride].split(b'\0')[0]
        assert value and not any(65<=c<=90 or 97<=c<=122 for c in value),(hex(start+i*stride),value)
for address in range(0x49cee,0x4a0be,4):
    old=int.from_bytes(src[address:address+4],'big')
    if not 0x39544<=old<=0x39a06 or src[old] in (0,32): continue
    target=int.from_bytes(rom[address:address+4],'big')
    assert 0x10c000<=target<0x110000,hex(address)
    value=rom[target:target+32].split(b'\0')[0]
    assert value and not any(65<=c<=90 or 97<=c<=122 for c in value),(hex(address),value)
assert rom[0x394ae:0x394b2]==encode('Осн')+b'\0'
assert rom[0x49c20:0x49c30].split(b'\0')[0]==encode('Вы закончили')
print('PASS: 47 province labels, generator pointer tables, Osn season, single-question prompt')
