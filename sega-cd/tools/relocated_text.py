"""Redirect explicitly reviewed name/unit pointer tables; retain original strings."""
import struct

def validate(entry, source, files):
    file=entry['file'];off=int(entry['offset'],16)
    ending=entry.get('kind')=='ending_caption'
    dialogue=entry.get('kind') in ('dialogue_fragment','xxx_dialogue','battle_dialogue')
    if entry.get('kind')=='music_title': assert len(entry['ru'].split('\n'))<=3 and all(len(line)<=12 for line in entry['ru'].split('\n'))
    elif ending: assert len(entry['ru'])<=30 and '\n' not in entry['ru']
    elif dialogue:
        assert len(entry['ru'].split('\n'))<=4 and all((len(x)+1)//2*2<=22 for x in entry['ru'].split('\n'))
    else: assert len(entry['ru'])<=10 and '\n' not in entry['ru']
    if entry.get('kind')=='battle_dialogue':
        assert file=='HEX.PRG;1' and 0x13abc<=off<0x144d0
        load=0x66000;low,high=0x14b00,0x14e80
    elif entry.get('kind')=='xxx_dialogue':
        assert file=='XXX.PRG;1' and off in (0x443c,0x444a,0x4450,0x4456,0x445c)
        load=0x66000;low,high=(0xe8a,0xe8e) if off==0x443c else (0x47ea,0x47fa)
    elif entry.get('kind')=='catalog_group':
        assert file=='INIT.PRG;1' and 0x14f78<=off<=0x14f8a
        load=0x66000;low,high=0x1774e,0x17776
    elif entry.get('kind')=='music_title':
        assert file=='INIT.PRG;1' and 0x14fd4<=off<=0x1502c
        load=0x66000;low,high=0x1778a,0x177ae
    elif ending:
        assert file=='ENDING.PRG;1' and 0x5cac<=off<0x5e72
        load=0x66000;low,high=0x5e72,0x753a
    elif entry.get('kind')=='init_chronicle_prefix':
        assert file=='INIT.PRG;1' and off==0x4c5a
        load=0x66000;low,high=0x7ca,0x7ce
    elif file=='INIT.PRG;1':
        assert 0x4f00<=off<0x522a
        load=0x66000;low,high=0x16cc2,0x16f22
    elif entry.get('kind') in ('interface_label','dialogue_fragment'):
        assert file=='SMAIN.PRG;1' and (0x26f40<=off<0x2b100 or off in (0x4af4e,0x4ca46,0x4cd60))
        load=0xc000;low,high=0x4b000,0x4da00
    elif entry.get('kind')=='season':
        assert file=='SMAIN.PRG;1' and off in (0x26522,0x26526,0x2652a,0x2652e)
        load=0xc000;low,high=0x49c34,0x49c44
    else:
        assert file=='SMAIN.PRG;1' and 0x273e6<=off<=0x27500
        load=0xc000;low,high=0x4bb24,0x4bba4
    base=files[file]['lba']*2048
    raw=entry['ja'].encode('shift_jis')+b'\0'
    assert source[base+off:base+off+len(raw)]==raw
    assert entry['references']
    for ref in entry['references']:
        position=int(ref['offset'],16)
        assert ref['file']==file and position%2==0
        if entry.get('kind')=='battle_dialogue' and not low<=position<high:
            assert 0<=position<0x13abc and source[base+position-2:base+position]==bytes.fromhex('4879')
        elif entry.get('kind') in ('interface_label','dialogue_fragment') and not low<=position<high:
            assert 0<=position<0x264fe and (source[base+position-2:base+position]==bytes.fromhex('4879') or (off,position)==(0x296c2,0x1f0f4) and source[base+position-2:base+position]==bytes.fromhex('207c'))
        else: assert low<=position<high
        assert bytes.fromhex(ref['before'])==struct.pack('>I',load+off)
        assert source[base+position:base+position+4]==bytes.fromhex(ref['before'])

def apply(image,source,files,entries):
    seen=set()
    for entry in entries:
        validate(entry,source,files)
        for ref in entry['references']:
            address=files[ref['file']]['lba']*2048+int(ref['offset'],16)
            assert address not in seen;seen.add(address)
            image[address:address+4]=struct.pack('>I',0xc000+entry['storage_offset'])
