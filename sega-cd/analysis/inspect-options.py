from pathlib import Path
import json,sys,capstone
r=Path(__file__).resolve().parents[1]
i=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'))
f=next(f for f in i['files'] if f['path']==sys.argv[1]+';1')
b=(r/'disc'/i['image']).read_bytes()[f['lba']*2048:][:f['size']]
start=int(sys.argv[2],16);end=int(sys.argv[3],16);load=int(sys.argv[4],16)
d=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000)
for x in d.disasm(b[start:end],start+load):print(f'{x.address:06x} {x.bytes.hex():20} {x.mnemonic:10} {x.op_str}')
