"""Single Cyrillic letters for editable names; FC codes have one-cell width.

Ordinary translated strings keep their existing pair encoding. The keyboard's
native byte-length guard and per-keystroke undo stack remain in force.
"""
import struct
ALPHABET=''.join(chr(ord('А')+i) for i in range(64))+'Ёё'
UPPER='АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
KEYS=UPPER+UPPER.lower()+'0123456789'+" -.,'!?():;/+_"
assert len(KEYS)==90

def code(ch):
 i=ALPHABET.index(ch);trail=0x40+i+(i>=63)
 return bytes((0xfc,trail))

def prepare(reserve):
 return {k:reserve(n,'single_'+k) for k,n in (('dispatch',96),('width',64),('draw',64),('store',128))}

def finish(main,reserve,put,addresses,Code,font,font_table,pair_hook,pair_render):
 load=0xc000
 c=Code();c.emit('7000302e000a');c.emit('0c40fc40');c.branch('65','pair');c.emit('0c40fc82');c.branch('62','pair')
 c.emit('024000ff04400040');c.emit('0c40003f');c.branch('65','index');c.emit('5340');c.label('index')
 c.emit('3400e14a00420042') # left ID, right blank ID 66
 c.emit('43f9'+f'{load+font:08x}'+'45f9'+f'{load+font_table:08x}')
 c.emit('4ef9'+f'{load+pair_render:08x}');c.label('pair');c.emit('4ef9'+f'{load+pair_hook:08x}')
 dispatch=c.finish();assert len(dispatch)<=96;put(addresses['dispatch'],dispatch)
 c=Code();c.emit('0c1000fc');c.branch('66','native');c.emit('52885202');c.emit('4ef9'+f'{load+0x3fd4:08x}')
 c.label('native');c.emit('0c100080');c.branch('65','ascii');c.emit('4ef9'+f'{load+0x3fbc:08x}');c.label('ascii');c.emit('4ef9'+f'{load+0x3fc2:08x}')
 width=c.finish();assert len(width)<=64;put(addresses['width'],width)
 c=Code();c.emit('30050240ff000c40fc00');c.branch('66','native')
 c.emit('4ef9'+f'{load+0x4c8a:08x}') # bottom-left tile -> native 8px lower tile
 c.label('native');c.emit('302eff748046');c.emit('4ef9'+f'{load+0x4b5a:08x}')
 draw=c.finish();assert len(draw)<=64;put(addresses['draw'],draw)
 c=Code();c.emit('302e000a0240ff000c40fc00');c.branch('66','native')
 c.emit('41eeffc043eeffa07007');c.label('copy');c.emit('22d8');c.emit('51c8fffc')
 c.emit('4878000230390005a11e2f00486eff804eb90000e7ac')
 c.emit('30390005a11e38c0524038c0487800024eb9000107aa4ef900010aee')
 c.label('native');c.emit('4878000430390005a11e4ef900010ac6')
 store=c.finish();assert len(store)<=128;put(addresses['store'],store)
 records=[];patches=[(0x4abc,'4878000430390005a11e','4ef9'+f"{load+addresses['store']:08x}"+'4e714e71'),(0x3fb6,'0c1000806506','4ef9'+f"{load+addresses['width']:08x}"),(0x4b54,'302eff748046','4ef9'+f"{load+addresses['draw']:08x}")]
 # Original keyboard pointer table remains contiguous. Key strings use tiny
 # fixed slots in three banks; no 360-byte contiguous font allocation needed.
 for page in range(3):
  a=reserve(90,'keyboard_keys')
  for slot,ch in enumerate(KEYS[page*30:page*30+30]):
   raw=(code(ch) if ch in ALPHABET else ch.encode('ascii'))+b'\0';dest=a+slot*3;put(dest,raw)
   ptr=0x4bbe6+(page*30+slot)*4;before=main[ptr:ptr+4].hex();patches.append((ptr,before,struct.pack('>I',load+dest).hex()));records.append(dict(character=ch,offset=dest,encoded=raw.hex(),pointer=ptr,before=before))
 # Only Cyrillic and the original Latin keyboard are cycled. Old kana/kanji
 # conversion screens are unreachable; no Japanese mode escapes in names.
 patches += [(0x115b6,'5280','7003'),(0x11bf8,'0c020020','60000052')]
 for off,old,new in patches:
  assert main[off:off+len(bytes.fromhex(old))]==bytes.fromhex(old),(hex(off),old)
  put(off,bytes.fromhex(new))
 return dict(**addresses,dispatch_size=len(dispatch),width_size=len(width),draw_size=len(draw),store_size=len(store),keys=records,patches=[dict(offset=o,before=b,after=a) for o,b,a in patches],alphabet=ALPHABET,maximum_name_bytes=15)
