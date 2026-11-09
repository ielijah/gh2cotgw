"""Reviewed fixed-record name fields in the scenario data bank.

Names occupy the first 16 bytes; only the first 14 plus NUL are writable.
The last name byte and all following numeric fields remain untouched.
"""
# (first name, stride, number of records). Short subranges intentionally exclude
# mixed-format child records and the surrounding province/country tables.
BLOCKS=[(0x2b1f6,26,100),(0x2d1f6,26,100),(0x2f1f6,26,100),
        (0x3149a,26,100),(0x3373e,26,100),
        (0x2c772,26,30),(0x2e772,26,30),(0x30772,26,30),
        (0x32a16,26,30),(0x34cba,26,30),
        (0x2cca0,22,12),(0x2ecb6,22,12),(0x30f9c,22,30),
        (0x331d2,22,30),(0x3548c,22,30)]
def valid_offset(offset):
    return offset in EXTRA_NAME_SLOTS or any(start<=offset<start+stride*count and (offset-start)%stride==0
               for start,stride,count in BLOCKS)

COUNTRY_BASES=(0x2c3bc,0x2e3bc,0x303bc,0x32660,0x34904)
def valid_country_offset(offset):
    return any(base<=offset<base+33*28 and (offset-base)%28==0 for base in COUNTRY_BASES)

PROVINCE_BASES=(0x49d0a,0x49f1a,0x4a12a)
def valid_province_offset(offset):
    return any(base<=offset<base+33*16 and (offset-base)%16==0 for base in PROVINCE_BASES)

# Individually checked later scenario records: 14 name bytes plus NUL.
# The next byte is a preserved flag, not available string padding.
EXTRA_NAME_SLOTS = (182936, 182988, 183118, 183144, 183170, 183196, 183248, 183274, 183326, 208370)
