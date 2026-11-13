"""Draw only province number and name in the map information footer."""
def allocate(reserve,put,Code):
 h=reserve(192,'map_country_label');c=Code()
 # Caller: format, country, number, province. Preserve caller-owned arguments.
 # The original format at 0x330BA is %-13s%d:%s; skip its country field.
 c.emit('2f2f00102f2f00104879000330bf4eb9000110344fef000c4e75')
 raw=c.finish();put(h,raw);return dict(helper=h,size=len(raw),country_hidden=True)

def patches(d):return [('SMAIN.PRG;1',0xf5f2,'000f','0008'),('SMAIN.PRG;1',0xec98,'4eb900011034','4eb9'+f'{0xc000+d["helper"]:08x}')]

def apply(image,source,files,d):
 for file,off,old,new in patches(d):
  a=files[file]['lba']*2048+off;b=bytes.fromhex(old);assert source[a:a+len(b)]==b;image[a:a+len(b)]=bytes.fromhex(new)
