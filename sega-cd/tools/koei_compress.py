"""Optimal bit-cost encoder for the KOEI bit-reservoir LZ format used by both versions."""
def command(length,distance):
    # Length's low bit shares the first (otherwise zero) distance bit.
    if length==2: prefix='';flag=1
    else:
        for low,high,k in [(3,4,1),(5,8,2),(9,16,3),(17,32,4),(33,64,5),(65,128,6),(129,255,7)]:
            if low<=length<=high:
                value=length-low;flag=value&1
                prefix=('0'*k+'1' if k<7 else '0000000')+(format(value>>1,f'0{k-1}b') if k>1 else '')
                break
        else: raise ValueError(length)
    if distance<4: count,value=7,distance
    elif distance<8: count,value=8,distance+4
    elif distance<32: count,value=9,distance+16
    elif distance<128: count,value=10,distance+64
    elif distance<256: count,value=11,distance+256
    elif distance<512: count,value=12,distance+768
    elif distance<1024: count,value=13,distance+2048
    elif distance<2048: count,value=14,distance+5120
    elif distance<4096: count,value=15,distance+12288
    else: raise ValueError(distance)
    bits=format(value,f'0{count}b')
    assert bits[0]=='0'
    return prefix+str(flag)+bits[1:],len(prefix),count

def encode(data):
    choices={};cost=[0]*(len(data)+1)
    for pos in range(len(data)-1,-1,-1):
        best=(9+cost[pos+1],1,None)
        covered=1
        for previous in range(pos-1,max(-1,pos-4097),-1):
            length=0
            while length<255 and pos+length<len(data) and data[previous+length]==data[pos+length]: length+=1
            if length<=covered:continue
            for size in range(max(2,covered+1),length+1):
                bits,prefix,count=command(size,pos-previous-1)
                candidate=(len(bits)+1+cost[pos+size],size,(bits,prefix,count))
                if candidate[0]<best[0]:best=candidate
            covered=length
            if covered==min(255,len(data)-pos):break
        cost[pos]=best[0];choices[pos]=best
    tokens=[];pos=0
    while pos<len(data):
        _,length,reference=choices[pos]
        if reference:
            bits,prefix,count=reference;tokens.append((0,bits,(prefix,count)))
        else:tokens.append((1,data[pos],()))
        pos+=length
    tokens.append((0,'0000000111111100',()))
    bitstream=''.join(value for literal,value,_ in tokens if not literal)+'0'*48
    cursor=0
    def word():
        nonlocal cursor
        value=int(bitstream[cursor:cursor+16],2);cursor+=16
        return value.to_bytes(2,'little')
    out=bytearray(word());remaining=0
    for start in range(0,len(tokens),8):
        part=tokens[start:start+8]
        out.append(sum(literal<<(7-n) for n,(literal,_,_) in enumerate(part)))
        for literal,value,advances in part:
            if literal:out.append(value)
            else:
                for count in advances:
                    if not count:continue
                    if count>remaining:
                        count-=remaining;out.extend(word());remaining=16-count
                    else:remaining-=count
    return bytes(out)
