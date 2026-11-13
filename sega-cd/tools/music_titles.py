"""Draw only the selected music title in the native allocation window (half-width cells 100..175)."""
import struct

def allocate(reserve,put):
 a=reserve(128,'music_title_draw')
 # The replaced JSR receives eight caller-owned arguments; leave them intact.
 # A fixed clear replaces the old one-row copy from the Japanese title atlas.
 # Clear the full 13x6-tile title area, including rows left by longer titles.
 code=bytes.fromhex('2f3c00008000487800064878000d487800134878000242a74878001a4eb90000c0f44fef001c'
 '3f3900059f4c33fc000200059f4c48780013487800024eb90001047c508f3002e548207c0007d78a2f300000'
 '48790007b0384eb900011034508f33df00059f4c4e75')
 assert len(code)<=128;put(a,code)
 return dict(helper=a,helper_size=len(code),columns=12,lines=3,cell_first=100,cell_last=175,tile_capacity=150)

def patches(data):
 return [('INIT.PRG;1',0x408e,'42423002','60000038'),
         ('INIT.PRG;1',0x4118,'4eb90000efee','4eb9'+struct.pack('>I',0xc000+data['helper']).hex())]

def apply(image,source,files,data):
 for file,off,old,new in patches(data):
  a=files[file]['lba']*2048+off;before=bytes.fromhex(old);after=bytes.fromhex(new)
  assert source[a:a+len(before)]==before;image[a:a+len(after)]=after
