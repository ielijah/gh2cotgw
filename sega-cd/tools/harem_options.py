"""Eighth Start-menu item: optional generated portraits, saved in unused bit 6."""
import struct,sys
from pathlib import Path
from text_encoding import encode
TEXTS=[dict(ru='Новые карточки:')]
ROOT=Path(__file__).resolve().parents[1]

def allocate(reserve,put,pairs,Code):
 text=reserve(32,'harem_option_text');put(text,encode(TEXTS[0]['ru'],pairs)+b'\0')
 label=reserve(256,'harem_option_label')
 sys.path.insert(0,str(ROOT.parent/'mega-drive/tools'))
 from menu_graphics import render
 put(label,render(bytes([0x99])*256,0xdc,'Образы',{},b''))
 handler=reserve(64,'harem_option_toggle')
 # Native boolean dialog uses positive bits. Invert only our bit around it,
 # so the saved zero/default means generated cards ON, including old saves.
 toggle=bytes.fromhex('0a3900400007fd584879'+f'{0xc000+text:08x}'+'487800404eb900031d16508f0a3900400007fd5870004e75')
 put(handler,toggle)
 table=reserve(32,'harem_option_dispatch')
 put(table,struct.pack('>8I',0x31fc6,0x321fe,0x31dd8,0x31dec,0x31e14,0x31e00,0x322c6,0xc000+handler))
 draw=reserve(192,'harem_option_draw')
 c=Code();c.emit('48e7fffe2f2f00442f2f00444eb90001485a508f')
 c.emit('0caf000550060044');c.branch('66','done')
 c.emit('4fef ffe0 2f0f 48780004 48780008 48780312 4879'+f'{0xc000+label:08x}')
 c.emit('4eb90000e8324fef0014')
 c.emit('2f0f4878000248780004487800154878001942a74878001b4eb90000c0f44fef001c4fef0020')
 c.label('done');c.emit('4cdf7fff4e75')
 raw=c.finish();assert len(raw)<=192;put(draw,raw)
 return dict(text=text,label=label,handler=handler,handler_size=len(toggle),table=table,draw=draw,draw_size=len(raw),caption='Образы',option='Новые карточки',bit=6,default_enabled=True)

def patches(d):
 return [('SMAIN.PRG;1',0x4b949,'07','08'),
         ('SMAIN.PRG;1',0x26396,'0005990c',f'{0xc000+d["table"]:08x}'),
         ('SMAIN.PRG;1',0xf7d0,'4eb90001485a','4eb9'+f'{0xc000+d["draw"]:08x}')]

def apply(image,source,files,d):
 for file,off,before,after in patches(d):
  a=files[file]['lba']*2048+off;old=bytes.fromhex(before);new=bytes.fromhex(after)
  assert source[a:a+len(old)]==old,(file,hex(off))
  image[a:a+len(new)]=new
