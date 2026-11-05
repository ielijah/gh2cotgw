"""Seven rows of ten keys, shared by rendering and name entry."""
UPPER = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
KEYS = UPPER + UPPER.lower() + '.,- '
TABLE = 0x116000
STRINGS = 0x116200

def apply(rom, src, encode):
    assert len(KEYS) == 70
    for location in (0x227fc, 0x22b4a):
        assert src[location:location+4] == bytes.fromhex('0004b614')
        rom[location:location+4] = TABLE.to_bytes(4,'big')
    assert src[0x22818:0x2281a] == bytes.fromhex('003c')
    rom[0x22818:0x2281a] = bytes.fromhex('0046')
    assert src[0x22962:0x22964] == bytes.fromhex('7815')
    rom[0x22962:0x22964] = bytes.fromhex('7817')
    # The legacy display-width helper treats DE/DF as Japanese marks.
    # In Russian they are ю/я: each key is one byte and one character.
    for location in (0x22648, 0x22b60):
        assert src[location:location+4] == bytes.fromhex('000053ac')
        rom[location:location+4] = bytes.fromhex('00005398')
    for index, char in enumerate(KEYS):
        pointer = STRINGS + index*2
        rom[TABLE+index*4:TABLE+index*4+4] = pointer.to_bytes(4,'big')
        rom[pointer:pointer+2] = encode(char) + b'\0'
