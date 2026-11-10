"""Pack catalogue biographies into their original INIT bank, without growing the overlay."""
import struct

START, END, TABLE, COUNT, LOAD = 0x522a, 0x14f1a, 0x16fba, 453, 0x66000

def offsets(source, files):
    base = files['INIT.PRG;1']['lba'] * 2048
    result = [p-LOAD for p in struct.unpack_from('>453I', source, base+TABLE)]
    assert len(set(result)) == COUNT and min(result) == START
    assert all(START <= p < END for p in result)
    return result

def apply(image, source, files, entries, encode):
    base = files['INIT.PRG;1']['lba'] * 2048
    old_offsets = offsets(source, files)
    by_offset = {int(e['offset'],16): e for e in entries if e['file']=='INIT.PRG;1'}
    assert all(p in by_offset for p in old_offsets)
    pos = START
    image[base+START:base+END] = bytes(END-START)
    records = []
    for i, old in enumerate(old_offsets):
        e = by_offset[old]
        raw = encode(e['ru']) + b'\0'
        assert pos+len(raw) <= END, 'Catalogue biography bank overflow'
        image[base+pos:base+pos+len(raw)] = raw
        struct.pack_into('>I', image, base+TABLE+4*i, LOAD+pos)
        e['destination_offset'] = f'{pos:X}'
        records.append(dict(source_offset=old, offset=pos, length=len(raw)))
        pos += len(raw)
    return dict(start=START, end=END, used=pos-START, free=END-pos, records=records)
