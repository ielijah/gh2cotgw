"""Bound list names to ten cells; full records remain available on biography cards."""
import struct

def allocate(reserve,put,Code):
 a=reserve(96,'catalog_list_name');c=Code()
 c.emit('48e7c0c04feffff0206f0028700a')
 c.label('scan');c.emit('4a18');c.branch('67','short')
 # DBRA D0,scan, encoded separately because Code.branch expects byte branches.
 pos=len(c.data);c.emit('51c80000');struct.pack_into('>h',c.data,pos+2,c.labels['scan']-(pos+2))
 c.emit('206f00282e902f68000400043f7c2e2e0008422f000a41d7');c.branch('60','print')
 c.label('short');c.emit('206f0028')
 c.label('print');c.emit('2f082f2f00284eb9000110344fef00184cdf03034e75')
 code=c.finish();assert len(code)<=96;put(a,code)
 return dict(helper=a,size=len(code),columns=10)

def patches(data):
 return [('INIT.PRG;1',0x32c4,'4eb900011034','4eb9'+struct.pack('>I',0xc000+data['helper']).hex())]

def apply(image,source,files,data):
 for file,off,old,new in patches(data):
  a=files[file]['lba']*2048+off;before=bytes.fromhex(old);after=bytes.fromhex(new)
  assert source[a:a+len(before)]==before;image[a:a+len(after)]=after
