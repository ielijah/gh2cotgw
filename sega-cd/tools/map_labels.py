"""Bound country labels in the map footer without changing full country names."""
def allocate(reserve,put,Code):
 h=reserve(192,'map_country_label');c=Code()
 c.emit('48e7f0e04fefffe02f2f00444eb90000ff58588f246f00440c40000d');c.branch('63','draw')
 c.emit('204a43d7240f7400') # A0 source, A1 scratch; D2 is reset below
 c.emit('244f7400')
 c.label('scan');c.emit('70001010');c.branch('67','suffix')
 c.emit('72010c000080');c.branch('65','fits');c.emit('72020c0000fc');c.branch('66','fits');c.emit('7201')
 c.label('fits');c.emit('3602d6410c43000a');c.branch('62','suffix')
 c.emit('12d80c000080');c.branch('65','next');c.emit('12d8')
 c.label('next');c.emit('3403');c.branch('60','scan')
 c.label('suffix');c.emit('12fc002e12fc002e4211')
 c.label('draw');c.emit('2f2f004c2f2f004c2f0a2f2f004c4eb9000110344fef00104fef00204cdf070f4e75')
 raw=c.finish();assert len(raw)<=192;put(h,raw);return dict(helper=h,size=len(raw),columns=13)
def patches(d):return [('SMAIN.PRG;1',0xec98,'4eb900011034','4eb9'+f'{0xc000+d["helper"]:08x}')]
def apply(image,source,files,d):
 for file,off,old,new in patches(d):
  a=files[file]['lba']*2048+off;b=bytes.fromhex(old);assert source[a:a+len(b)]==b;image[a:a+len(b)]=bytes.fromhex(new)
