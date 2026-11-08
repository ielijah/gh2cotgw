"""Serif end caption using the original E, palette, baseline and shadow."""
from graphics_codec import decode,encode_literals
MAP=0xc8678
BANK=0x12b000

def artwork(src):
    old,_=decode(src[int.from_bytes(src[0xce9ec:0xce9f0],'big'):])
    original=[[0]*80 for _ in range(16)]
    for i in range(20):
        t=int.from_bytes(src[MAP+i*2:MAP+i*2+2],'big')&2047
        raw=old[(t-0x280)*32:(t-0x280+1)*32]
        for y in range(8):
            for x in range(8):original[i//10*8+y][i%10*8+x]=(raw[y*4+x//2]>>(4 if x%2==0 else 0))&15
    glyphs={
      'К':['111100001111','011000000110','011000001100','011000011000','011000110000','011001100000','011111000000','011001100000','011000110000','011000011000','011000001100','111100001111'],
      'О':['000111111000','001100001100','011000000110','011000000110','110000000011','110000000011','110000000011','110000000011','011000000110','011000000110','001100001100','000111111000'],
      'Н':['111100001111','011000000110','011000000110','011000000110','011000000110','011000000110','011111111110','011000000110','011000000110','011000000110','011000000110','111100001111'],
      'Ц':['111100011110','011000001100','011000001100','011000001100','011000001100','011000001100','011000001100','011000001100','011000001100','011000001100','011000001100','111111111111','000000000011','000000000001'],
    }
    glyphs['Е']=[''.join('1' if v==7 else '0' for v in row[17:29]) for row in original[:12]]
    out=[[0]*80 for _ in range(16)];ink=[]
    for i,ch in enumerate('КОНЕЦ'):
        for y,row in enumerate(glyphs[ch]):
            for x,v in enumerate(row):
                if v=='1':ink.append((8+i*13+x,y))
    ink += [(x,11) for x in list(range(0,5))+list(range(75,80))]
    for x,y in ink:
        for dx,dy in [(-1,0),(-1,1),(0,1)]:
            if 0<=x+dx<80 and y+dy<16:out[y+dy][x+dx]=1
    for x,y in ink:out[y][x]=7
    return old,out

def apply(rom,src):
    old,px=artwork(src);bank=bytearray(old)
    for i in range(20):
        tile=0x280+len(bank)//32;assert tile<0x6c0
        raw=bytes((px[i//10*8+y][i%10*8+x]<<4)|px[i//10*8+y][i%10*8+x+1] for y in range(8) for x in range(0,8,2))
        bank.extend(raw);rom[MAP+i*2:MAP+i*2+2]=(0xc000|tile).to_bytes(2,'big')
    packed=encode_literals(bank);assert BANK+len(packed)<=len(rom)
    rom[BANK:BANK+len(packed)]=packed;rom[0xce9ec:0xce9f0]=BANK.to_bytes(4,'big')
