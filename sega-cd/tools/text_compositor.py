"""Build a paged pair dictionary and a 68000 compositor in unused font cells.

No new RAM bank or loader changes. A pair still consumes two bytes/two columns.
The only extra RAM is 32 bytes in the existing renderer's stack frame.
"""
import struct

FONT = 0x37490
LOAD = 0xc000
MAX_PAIRS = 13 * 188


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


def install(main, codes, unused, pairs, rows):
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
    # Allocate the longest contiguous objects before the scattered pages.
    hook = reserve(224, 'compositor')
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
    c.emit('70003002e048')               # D0 = left ID
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
    patches = [
        (0x4a1c, '4e56ff7c', '4e56ff5c'),  # local frame: 132 -> 164 bytes
        (0x4a28, '302e000a2f00', '4ef9'+f'{LOAD+hook:08x}'),
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
                extra_stack_bytes=32), {pair:pair_code(i) for i,pair in enumerate(pairs)}
