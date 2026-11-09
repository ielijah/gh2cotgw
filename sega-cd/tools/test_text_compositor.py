"""Static compositor checks only: no CPU core or game emulator is executed."""
from pathlib import Path
import json
import struct
import capstone


def check(root, source, image, base, manifest):
    c = manifest['text_compositor']
    main = image[base:]
    font = 0x37490
    load = 0xc000
    def word(address):
        return struct.unpack_from('>H', main, address)[0]
    spans = sorted((r['offset'],r['offset']+r['length']) for r in c['storage'])
    assert all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))
    def stored(address, size):
        assert any(a<=address and address+size<=b for a,b in spans),(address,size)
    stored(c['hook'],c['hook_size'])
    stored(c['helper'],c['helper_size'])
    for ch,addr in zip(c['alphabet'],c['character_addresses']):
        stored(addr,16)
    assert len(c['alphabet'])<=256 and c['capacity']==2444
    # Independently check all legal code round trips, including both sides of
    # 7F and every lead-byte boundary. These are native two-byte SJIS tokens.
    for index in range(c['capacity']):
        lead=0xf0+index//188
        trail=list(range(0x40,0x7f))+list(range(0x80,0xfd))
        low=trail[index%188]
        decoded=(lead-0xf0)*188+low-0x40-(low>=0x80)
        assert decoded==index and 0xf0<=lead<=0xfc
        assert low not in (0,10,13,27,0x7f)
    # Traverse the on-disc two-level directory; compare every composited tile
    # with its two imported character bitmaps, not with the old pair font.
    for pair,code in manifest['paired_glyphs'].items():
        high,low=bytes.fromhex(code)
        assert 0xf0<=high<=0xfc and 0x40<=low<=0xfc and low!=0x7f
        index=(high-0xf0)*188+low-0x40-(low>=0x80)
        assert index<c['pair_count']
        directory=font+word(c['dictionary_root']+(index>>8)*2)
        stored(directory,32)
        page=font+word(directory+((index>>4)&15)*2)
        stored(page,32)
        ids=main[page+(index&15)*2:page+(index&15)*2+2]
        assert ''.join(c['alphabet'][i] for i in ids)==pair
        scratch=bytearray(32)
        expected=[]
        for column,ident in enumerate(ids):
            address=font+word(c['character_table']+ident*2)
            assert address==c['character_addresses'][ident]
            rows=main[address:address+16]
            expected.append(rows)
            # The hook performs four longword moves, at these exact offsets.
            for n,offset in enumerate((0,4,16,20)):
                scratch[column*8+offset:column*8+offset+4]=rows[n*4:n*4+4]
        assert scratch==expected[0][:8]+expected[1][:8]+expected[0][8:]+expected[1][8:]
    assert c['pair_count']==len(manifest['paired_glyphs'])
    # Verify native byte classification in width counting, formatted copying,
    # and rendering remains identical. All three already accept F0..FC.
    for a,b in ((0x3fb6,0x3fd2),(0x439c,0x43bc),(0x4b20,0x4b46)):
        assert main[a:b]==source[base+a:base+b]
    # Private bitmap is [-164,-132), original pixel buffer [-128,0).
    # MOVEM saves 9 longs below LINK's frame, restored at -200, not -168.
    assert main[0x4a1c:0x4a24]==bytes.fromhex('4e56ff5c48e73f38')
    assert main[0x4aee:0x4af8]==bytes.fromhex('4cee1cfcff384e5e4e75')
    assert c['extra_stack_bytes']==32
    assert -200+9*4==-164 and -164+32==-132 and -132<=-128
    helper=main[c['helper']:c['helper']+c['helper_size']]
    assert helper==bytes.fromhex('d04076003632000047f1380020db20db508820db20db4e75')
    md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000)
    lines=[]
    for name in ('hook','helper'):
        start=c[name];data=main[start:start+c[name+'_size']]
        instructions=list(md.disasm(data,load+start))
        assert sum(x.size for x in instructions)==len(data)
        assert all(x.mnemonic not in ('dc.w','.byte','illegal') for x in instructions)
        if name=='hook':
            boundaries={x.address for x in instructions}
            for x in instructions:
                if x.mnemonic in ('bcs.w','bhi.w','bcc.w'):
                    assert int(x.op_str[1:],16) in boundaries
            calls=[int(x.op_str.split('.')[0][1:],16) for x in instructions if x.mnemonic=='jsr']
            assert calls==[load+c['helper']]*2
            jumps=[int(x.op_str.split('.')[0][1:],16) for x in instructions if x.mnemonic=='jmp']
            assert jumps==[load+0x4a44,load+0x4a2e]
            assert instructions[-3].mnemonic=='move.w' and instructions[-3].op_str=='$a(a6), d0'
            assert instructions[-2].mnemonic=='move.l' and instructions[-2].op_str=='d0, -(a7)'
            assert 'cmpi.w #$'+format(c['pair_count'],'x')+', d0' in [x.mnemonic+' '+x.op_str for x in instructions]
        lines.extend(f'{x.address:06X}: {x.bytes.hex():<22} {x.mnemonic} {x.op_str}' for x in instructions)
    (root/'analysis/text-compositor.asm').write_text('\n'.join(lines)+'\n',encoding='utf8')
    (root/'analysis/text-compositor-check.json').write_text(json.dumps(dict(
        pairs=c['pair_count'],capacity=c['capacity'],extra_stack_bytes=32,
        checks=['all code boundaries','paged dictionary','every composed bitmap','native width/copy paths',
                'stack and saved registers','68000 disassembly and branch targets'],
        emulator_run=False,limitation='Static validation; in-game runtime not tested'),indent=2)+'\n',encoding='utf8')
    print('PASS: compositor dictionary, all tile pixels, 2444 code boundaries, stack layout and static 68000 control flow')


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    inv=json.loads((root/'analysis/disc-inventory.json').read_text('utf8'))
    manifest=json.loads((root/'build/manifest.json').read_text('utf8'))
    base=next(f['lba']*2048 for f in inv['files'] if f['path']=='SMAIN.PRG;1')
    check(root,(root/'disc'/inv['image']).read_bytes(),(root/'build/genchou-hishi-ru-experimental.iso').read_bytes(),base,manifest)
