"""Regression for the wide menu's palette-highlight stack overwrite."""
from pathlib import Path
import json, struct

r=Path(__file__).resolve().parents[1]
inventory=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'))
source=(r/'disc'/inventory['image']).read_bytes()
patched=(r/'build/genchou-hishi-ru-experimental.iso').read_bytes()
base=next(f['lba']*2048 for f in inventory['files'] if f['path']=='SMAIN.PRG;1')
init=next(f['lba']*2048 for f in inventory['files'] if f['path']=='INIT.PRG;1')
assert source[base+0x8a04:base+0x8a08]==bytes.fromhex('4e56ffc0')
# Original two-row read writes 72 bytes from A6-64 through A6+7:
# saved frame pointer and return address are both overwritten.
old_start=struct.unpack_from('>h',source,base+0x8a06)[0]
columns=struct.unpack_from('>H',patched,init+0x1e4a)[0]
assert columns==18 and old_start+columns*2*2==8
assert patched[base+0x8a04:base+0x8a08]==bytes.fromhex('4e56ff80')
assert patched[base+0x8a1c:base+0x8a20]==bytes.fromhex('47eeff80')
assert patched[base+0x8a98:base+0x8a9e]==bytes.fromhex('4cee0c7cff64')
new_start=struct.unpack_from('>h',patched,base+0x8a06)[0]
restore=struct.unpack_from('>h',patched,base+0x8a9c)[0]
assert restore+7*4==new_start
for width in range(1,33):
    assert new_start+width*2*2<=0
# The newline origin is an X coordinate, independently of highlight width.
assert patched[init+0x1df4:init+0x1df8]==bytes.fromhex('4878000c')
assert patched[init+0x1e02:init+0x1e06]==bytes.fromhex('4878000c')
print('PASS: reproduced 8-byte stack overwrite; 1..32 columns fit; saved registers and newline origin match')
