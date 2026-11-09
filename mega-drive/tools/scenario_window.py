"""Add a 21-column scenario window without changing existing window types."""
def apply(rom,src):
    shape,widths,heights=0x106100,0x106140,0x106150
    rom[shape:shape+60]=src[0x48b58:0x48b94]
    rom[shape+60:shape+64]=bytes.fromhex('0015000a')
    rom[widths:widths+16]=src[0x48be0:0x48bef]+bytes([21])
    rom[heights:heights+16]=src[0x48bef:0x48bfe]+bytes([10])
    rom[0x106180:0x1061c0]=src[0x48b94:0x48bd0]+src[0x48b98:0x48b9c]
    rom[0x1061c0:0x1061d0]=src[0x48bd0:0x48bdf]+src[0x48bd1:0x48bd2]
    for location,old,new in [(0x9816,0x48b58,shape),(0x9826,0x48b5a,shape+2),(0x995e,0x48be0,widths),(0x9b34,0x48bfe,widths),(0x9b44,0x48c0d,heights),(0x9c68,0x48c1c,widths),(0x9c7c,0x48c2b,heights)]:
        assert src[location:location+4]==old.to_bytes(4,'big')
        rom[location:location+4]=new.to_bytes(4,'big')
    for location,old,new in [(0x9a36,0x48b94,0x106180),(0x9a44,0x48bd0,0x1061c0)]:
        assert src[location:location+4]==old.to_bytes(4,'big')
        rom[location:location+4]=new.to_bytes(4,'big')
    for location in (0x9989,0x99cf):
        assert src[location]==15
        rom[location]=16
