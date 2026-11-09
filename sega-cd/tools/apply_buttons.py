"""Repack the original graphic bank and update its native pointer table in place."""
from pathlib import Path
import json,hashlib,struct
from koei_decode import decode
from koei_compress import encode
ROOT=Path(__file__).resolve().parents[1]
START,TABLE,LOAD,COUNT=0x1800,0x939c,0xb2800,255

def apply(image,source,files):
    f=files['GH2GRP.DAT;1'];base=f['lba']*2048
    bank=source[base:base+f['size']]
    pointers=list(struct.unpack_from('>255I',bank,TABLE))
    assert pointers==sorted(pointers) and pointers[0]-LOAD==START
    report=json.loads((ROOT/'translation/buttons.json').read_text('utf8'))
    changes={int(e['resource'],16):e for e in report['entries']}
    packed=bytearray();new_pointers=[];resources=[]
    for n,pointer in enumerate(pointers):
        old_offset=pointer-LOAD
        old_end=pointers[n+1]-LOAD if n+1<COUNT else TABLE
        original,_=decode(bank[old_offset:old_end])
        raw=original
        if n in changes:
            entry=changes[n];raw=(ROOT/entry['file']).read_bytes()
            assert len(raw)==len(original)==entry['size']
            assert hashlib.sha256(original).hexdigest()==entry['source_cd_sha256']
            assert hashlib.sha256(raw).hexdigest()==entry['sha256']
        compressed=encode(raw)
        assert decode(compressed)[0]==raw
        if n not in changes and len(compressed)>=old_end-old_offset:
            compressed=bank[old_offset:old_end]
        new_offset=START+len(packed);new_pointers.append(LOAD+new_offset)
        packed.extend(compressed)
        if len(packed)%2:packed.append(0)
        resources.append(dict(resource=f'{n:02X}',old_offset=old_offset,new_offset=new_offset,
                              raw_size=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),
                              modified=n in changes,compressed_size=len(compressed)))
    assert START+len(packed)<=TABLE, 'New bank exceeds the original allocation'
    image[base+START:base+TABLE]=packed+bytes(TABLE-START-len(packed))
    struct.pack_into('>255I',image,base+TABLE,*new_pointers)
    # Decode every resource through its new native pointer: the translated
    # labels are exact copies, and all unrelated resources retain their pixels.
    for resource,pointer in zip(resources,new_pointers):
        raw,_=decode(image[base+pointer-LOAD:])
        assert hashlib.sha256(raw).hexdigest()==resource['raw_sha256']
    return dict(file=f['path'],source_md_rom_sha256=report['source_md_rom_sha256'],
                modified_count=len(changes),native_pointer_count=COUNT,
                allowed_offset=START,allowed_length=TABLE+COUNT*4-START,
                used_bytes=len(packed),available_bytes=TABLE-START,
                resources=resources,deferred=report['deferred'])
