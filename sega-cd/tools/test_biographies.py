"""Audit the entire contiguous biography pool, including tabbed source strings."""
from pathlib import Path
import json
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_encoding import pieces

ROOT = Path(__file__).resolve().parents[1]
START, END, EXPECTED = 0x522A, 0x14F1A, 453
inventory = json.loads((ROOT / 'analysis/disc-inventory.json').read_text('utf-8'))
record = next(x for x in inventory['files'] if x['path'] == 'INIT.PRG;1')
image = (ROOT / 'disc' / inventory['image']).read_bytes()
raw = image[record['lba'] * 2048:record['lba'] * 2048 + record['size']]
entries = {}
for name in ('interface', 'harem-screen', 'harem-ui', 'gameplay-dialogue'):
    for entry in json.loads((ROOT / f'translation/{name}.json').read_text('utf-8')):
        if entry['file'] == 'INIT.PRG;1':
            offset = int(entry['offset'], 16)
            assert offset not in entries, f'Duplicate INIT entry {offset:X}'
            entries[offset] = entry

position, count, tabbed, packed_size = START, 0, 0, 0
while position < END:
    if raw[position] == 0:
        position += 1
        continue
    end = raw.index(0, position)
    assert end < END
    original = raw[position:end].decode('shift_jis')
    assert position in entries, f'Untranslated biography {position:X}: {original}'
    entry = entries[position]
    assert entry['ja'] == original, f'Source mismatch {position:X}'
    ru = entry['ru']
    assert ru.strip() and not re.search(r'[\u3040-\u30ff\u3400-\u9fff\uff61-\uff9f]', ru)
    lines = ru.split('\n')
    assert len(lines) <= 7, f'Too many lines {position:X}'
    assert all((len(line) + 1) // 2 * 2 <= 22 for line in lines), f'Too wide {position:X}'
    encoded_size = sum(len(value) if kind == 'raw' else 2 for kind, value in pieces(ru))
    packed_size += encoded_size+1
    count += 1
    tabbed += '\t' in original
    position = end + 1
assert count == EXPECTED, (count, EXPECTED)
assert packed_size <= END-START, 'Shared biography bank overflow'
print(f'PASS: all {count} biographies translated; {tabbed} tabbed originals; exact source bytes, shared bank capacity, 7 lines and 22 columns')
