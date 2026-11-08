"""KOEI 68000 graphics codec, ported from ROM routines 003376/0033F0.

Control words are little endian, flag bytes are MSB first, and literal
bytes share the input cursor with refills of the control-word reservoir.
"""
def decode(data, limit=65536):
    pos=0; window=0; remaining=0; reservoir=0; out=bytearray()
    def advance(n):
        nonlocal pos,window,remaining,reservoir
        window=(window<<n)&65535
        if n>remaining:
            n-=remaining
            window|=(reservoir&((1<<remaining)-1))<<n
            reservoir=int.from_bytes(data[pos:pos+2],'little');pos+=2
            remaining=16-n
        else: remaining-=n
        window|=(reservoir>>remaining)&((1<<n)-1)
    advance(16)
    while pos<len(data):
        flags=data[pos];pos+=1
        for bit in range(7,-1,-1):
            if flags&(1<<bit): out.append(data[pos]);pos+=1
            else:
                if window&0x8000: length=1
                elif window&0x4000: length=(window&0x6000)>>13;advance(2)
                elif window&0x2000: length=(window&0x3800)>>11;advance(4)
                elif window&0x1000: length=(window&0x1e00)>>9;advance(6)
                elif window&0x800: length=(window&0xf80)>>7;advance(8)
                elif window&0x400: length=(window&0x7e0)>>5;advance(10)
                elif window&0x200: length=(window&0x3f8)>>3;advance(12)
                else:
                    length=((window&0x1fc)>>2)+128
                    if length==255: return bytes(out),pos
                    advance(13)
                window&=0x7fff
                if window<0x800: distance=(window&0x600)>>9;advance(7)
                elif window<0xc00: distance=((window&0x300)>>8)+4;advance(8)
                elif window<0x1800: distance=(((window-0xc00)&0xf80)>>7)+8;advance(9)
                elif window<0x3000: distance=(((window-0x1800)&0x1fc0)>>6)+32;advance(10)
                else:
                    shift=5 if window<0x4000 else 4 if window<0x5000 else 3 if window<0x6000 else 2 if window<0x7000 else 1
                    distance=((window&0x1fff)|0x1000)>>shift;advance(16-shift)
                for _ in range(length+1): out.append(out[-distance-1])
            if len(out)>limit: raise ValueError('Invalid decompression size')
    raise ValueError('Missing end marker')

def encode_literals(data):
    """Valid lossless stream; compression is intentionally unnecessary."""
    out=bytearray(b'\xfc\x01')
    for i in range(0,len(data),8):
        part=data[i:i+8];out.append(((1<<len(part))-1)<<(8-len(part)));out.extend(part)
    if len(data)%8==0: out.append(0)
    assert decode(out)[0]==data
    return bytes(out)
