"""Reproducible static inventory; requires capstone==5.0.6."""
from pathlib import Path
import json, re, hashlib
from capstone import Cs, CS_ARCH_M68K, CS_MODE_BIG_ENDIAN, CS_MODE_M68K_000

ROOT = Path(__file__).resolve().parents[1]
rom = (ROOT / 'rom/original.gen').read_bytes()
out = ROOT / 'analysis'
out.mkdir(exist_ok=True)
md = Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN | CS_MODE_M68K_000)
md.skipdata = True
lines = ['; Linear disassembly: data mixed with code; NOT a rebuildable source.',
         '; Addresses are ROM offsets / 68000 addresses.']
for ins in md.disasm(rom[0x200:0x3947a], 0x200):
    lines.append(f'{ins.address:06X}: {ins.bytes.hex():<24} {ins.mnemonic:10} {ins.op_str}')
(out / 'm68k-linear.asm').write_text('\n'.join(lines), encoding='utf-8')
entries=[]
for m in re.finditer(rb'[\x20-\x7e]{2,}\x00',rom[0x39470:0x40000]):
    off=0x39470+m.start()
    raw=m.group()[:-1]
    entries.append(dict(offset=f'{off:06X}',source=raw.decode('ascii'),ru='',capacity=len(raw)))
(ROOT/'translation/strings.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
report=dict(sha256=hashlib.sha256(rom).hexdigest(),size=len(rom),initial_sp=f'{int.from_bytes(rom[:4],"big"):08X}',reset=f'{int.from_bytes(rom[4:8],"big"):06X}',stored_checksum=f'{int.from_bytes(rom[0x18e:0x190],"big"):04X}',computed_checksum=f'{sum(int.from_bytes(rom[i:i+2],"big") for i in range(0x200,len(rom),2))&65535:04X}',strings=len(entries))
(out/'rom.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
refs=[]
for off in range(0x200,0x39478,2):
    address=int.from_bytes(rom[off:off+4],'big')
    if 0x3947a<=address<0x457c4:
        refs.append(dict(operand_offset=f'{off:06X}',target=f'{address:06X}'))
(out/'text-pointer-candidates.json').write_text(json.dumps(refs,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
