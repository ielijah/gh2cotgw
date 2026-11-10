"""Build a paged pair dictionary and a 68000 compositor in unused font cells.

No new RAM bank or loader changes. A pair still consumes two bytes/two columns.
The only extra RAM is 32 bytes in the existing renderer's stack frame.
"""
import struct

FONT = 0x37490
LOAD = 0xc000
MAX_PAIRS = 12 * 188


def pair_code(index):
    assert 0 <= index < MAX_PAIRS
    trail = 0x40 + index % 188
    if trail >= 0x7f:
        trail += 1
    return bytes((0xf0 + index // 188, trail))


class Code:
    def __init__(self):
        self.data = bytearray()
        self.labels = {}
        self.refs = []
    def emit(self, value):
        self.data.extend(bytes.fromhex(value))
    def label(self, name):
        self.labels[name] = len(self.data)
    def branch(self, op, name):
        self.emit(op + '000000')
        self.refs.append((len(self.data)-2, name))
    def finish(self):
        for pos, name in self.refs:
            struct.pack_into('>h', self.data, pos, self.labels[name]-pos)
        return bytes(self.data)


def install(main, codes, unused, pairs, rows, start_prompt=None, relocated=()):
    assert len(pairs) <= MAX_PAIRS
    # The chosen codes belong to the native two-byte path, but no original
    # font entry uses the private F0..FC range.
    assert all(c < 0xf000 for c in codes)
    free = {FONT+i*32 for i,c in enumerate(codes) if c in unused and i*32 < 65536}
    used = []
    def reserve(size, kind):
        cells = (size+31)//32
        for address in sorted(free):
            span = [address+n*32 for n in range(cells)]
            if all(p in free for p in span):
                free.difference_update(span)
                used.append(dict(offset=address, length=cells*32, kind=kind))
                main[address:address+cells*32] = bytes(cells*32)
                return address
        raise AssertionError(('No contiguous font storage',kind,size))
    def put(address, data):
        main[address:address+len(data)] = data
    def rel(address):
        assert 0 <= address-FONT < 65536
        return address-FONT
    def words(values):
        return struct.pack('>'+str(len(values))+'H', *values)
    # Nameplates measure pair padding as a real column. Trim only the final
    # blank half of a Cyrillic pair, after drawing and before restoring the map.
    padded_codes = [pair_code(i).hex() for i,p in enumerate(pairs) if p[1]==' ' and p[0]!=' ']
    hook = reserve(224, 'compositor')
    from single_letters import prepare as prepare_singles, finish as finish_singles
    singles = prepare_singles(reserve)
    from music_titles import allocate as allocate_music
    music_titles=allocate_music(reserve,put)
    from catalog_list import allocate as allocate_catalog_list
    catalog_list=allocate_catalog_list(reserve,put,Code)
    name_trim = reserve(96 + 2*(len(padded_codes)+1), 'nameplate_trim')
    n = Code()
    n.emit('2f2f00044eb90000ff58588f')  # original width function, same argument
    n.emit('48e740c0')                 # preserve D1/A0/A1
    n.emit('0c400002'); n.branch('65','done')
    n.emit('206f0010')                 # original string argument
    n.label('scan'); n.emit('4a18'); n.branch('66','scan')
    n.emit('72001228fffde1491228fffe') # final two bytes, no unaligned word read
    n.emit('43f9'+f'{LOAD+name_trim+96:08x}')
    n.label('compare'); n.emit('b259'); n.branch('67','trim')
    n.emit('4a51'); n.branch('66','compare')
    n.branch('60','done')
    n.label('trim'); n.emit('5340537900059eac')
    n.label('done'); n.emit('4cdf03024e75')
    trim_code = n.finish()
    assert len(trim_code) <= 96
    put(name_trim, trim_code)
    put(name_trim+96, bytes.fromhex(''.join(padded_codes)+'0000'))
    from generated_names import allocate as allocate_generated, apply as apply_generated
    generated_names=allocate_generated(reserve,put,Code,list(rows),{p:pair_code(i) for i,p in enumerate(pairs)})
    apply_generated(main,generated_names)
    # Allocate the longest contiguous objects before the scattered pages.
    alphabet = list(rows)
    font_table = reserve(len(alphabet)*2, 'character_offsets')
    helper = reserve(32, 'copy_character')
    root = reserve(32, 'dictionary_root')
    font_addresses = []
    for ch in alphabet:
        address = reserve(16, 'character')
        put(address, rows[ch])
        font_addresses.append(address)
    put(font_table, words([rel(a) for a in font_addresses]))
    dictionary = bytes(v for pair in pairs for v in (alphabet.index(pair[0]), alphabet.index(pair[1])))
    pages = []
    for offset in range(0, len(dictionary), 32):
        address = reserve(32, 'dictionary_pairs')
        put(address, dictionary[offset:offset+32])
        pages.append(address)
    directory = []
    for offset in range(0, len(pages), 16):
        address = reserve(32, 'dictionary_directory')
        put(address, words([rel(a) for a in pages[offset:offset+16]]))
        directory.append(address)
    assert len(directory) <= 16
    put(root, words([rel(a) for a in directory]))
    prompt_record = None
    if start_prompt is not None:
        from text_encoding import encode
        data = encode(start_prompt, {pair:pair_code(i) for i,pair in enumerate(pairs)}) + b'\0'
        address = reserve(len(data), 'start_prompt')
        put(address, data)
        prompt_record = dict(offset=address, length=len(data), ru=start_prompt)


    relocated_records = []
    for entry in relocated:
        from text_encoding import encode, encode_stream
        encoder = encode_stream if entry.get('native_stream') else encode
        data = encoder(entry['ru'], {pair:pair_code(i) for i,pair in enumerate(pairs)}) + b'\0'
        address = reserve(len(data), 'relocated_text')
        put(address, data)
        relocated_records.append(dict(**entry, storage_offset=address, storage_length=len(data)))

    from battle_text import allocate as allocate_battle_text
    battle_text=allocate_battle_text(reserve,put,{pair:pair_code(i) for i,pair in enumerate(pairs)})
    from chronicle_tables import allocate as allocate_chronicles
    chronicle_tables=allocate_chronicles(reserve,put,{pair:pair_code(i) for i,pair in enumerate(pairs)})

    # Helper input: D0 character index, A0 output, A1 font base, A2 offsets.
    # Copy upper 8 rows, skip the adjacent character, then lower 8 rows.
    h = bytes.fromhex('d04076003632000047f1380020db20db508820db20db4e75')
    assert len(h) <= 32
    put(helper, h)

    c = Code()
    c.emit('7000302e000a')                 # D0 = unsigned argument
    c.emit('0c40f040'); c.branch('65','native')
    c.emit('0c40fcfc'); c.branch('62','native')
    c.emit('3200e049044100f0c2fc00bc')     # D1 = (lead-F0)*188
    c.emit('024000ff04400040')            # D0 = trail-40
    c.emit('0c40003f'); c.branch('65','trail')
    c.emit('5340')                       # skip the SJIS 7F hole
    c.label('trail'); c.emit('d041')
    c.emit('0c40'+f'{len(pairs):04x}'); c.branch('64','native')
    c.emit('3400')                       # D2 = pair index
    c.emit('43f9'+f'{LOAD+FONT:08x}')     # A1 = font/data base
    c.emit('45f9'+f'{LOAD+font_table:08x}')
    c.emit('e048d040')                   # root index = (pair>>8)*2
    c.emit('41f9'+f'{LOAD+root:08x}')
    c.emit('76003630000041f13800')        # A0 = directory page
    c.emit('3002e8480240000fd040')        # middle 4 bits * 2
    c.emit('76003630000041f13800')        # A0 = pair page
    c.emit('30020240000fd040')            # low 4 bits * 2
    c.emit('34300000')                   # D2 = left/right character IDs
    c.label('render_pair'); c.emit('70003002e048')               # D0 = left ID
    c.emit('41eeff5c')                   # A0 = private 32-byte scratch
    c.emit('4eb9'+f'{LOAD+helper:08x}')
    c.emit('70001002')                   # D0 = right ID
    c.emit('41eeff64')                   # scratch + 8
    c.emit('4eb9'+f'{LOAD+helper:08x}')
    c.emit('47eeff5c')                   # A3 = composed 16x16 bitmap
    c.emit('4ef9'+f'{LOAD+0x4a44:08x}')
    c.label('native')
    c.emit('302e000a2f00')               # replay displaced instructions
    c.emit('4ef9'+f'{LOAD+0x4a2e:08x}')
    code = c.finish()
    assert len(code) <= 224, len(code)
    put(hook, code)
    assert alphabet[:67]==list(''.join(chr(ord('А')+i) for i in range(64))+'Ёё ')
    singles=finish_singles(main,reserve,put,singles,Code,FONT,font_table,hook,hook+c.labels['render_pair'])
    patches = [
        (0x731a, '4eb90000ff58', '4eb9'+f'{LOAD+name_trim:08x}'),
        (0x4a1c, '4e56ff7c', '4e56ff5c'),  # local frame: 132 -> 164 bytes
        (0x4a28, '302e000a2f00', '4ef9'+f"{LOAD+singles['dispatch']:08x}"),
        (0x4aee, '4cee1cfcff58', '4cee1cfcff38'),  # saved registers move by -32
    ]
    for offset, old, new in patches:
        assert main[offset:offset+len(bytes.fromhex(old))] == bytes.fromhex(old)
        put(offset, bytes.fromhex(new))
    return dict(version=1, capacity=MAX_PAIRS, pair_count=len(pairs), alphabet=alphabet,
                character_table=font_table, character_addresses=font_addresses,
                dictionary_root=root, hook=hook, hook_size=len(code), helper=helper,
                helper_size=len(h), storage=used,
                patches=[dict(offset=o, before=b, after=a) for o,b,a in patches],
                extra_stack_bytes=32, single_letters=singles, generated_names=generated_names, battle_text=battle_text, music_titles=music_titles, catalog_list=catalog_list, chronicle_tables=chronicle_tables, nameplate_trim=name_trim, nameplate_trim_size=len(trim_code), start_prompt=prompt_record, relocated_texts=relocated_records), {pair:pair_code(i) for i,pair in enumerate(pairs)}
