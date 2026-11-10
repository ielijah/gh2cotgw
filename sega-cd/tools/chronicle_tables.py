"""Expanded city/season tables used by unification chronicles and scenario summaries."""
import struct
BANKS=[
 ('missions',12,['Поход','Переход','Доставка']),
 ('cities',16,['Хираидзуми','Кисо','Фукухара','Камакура']),
 ('seasons',12,['Весна','Лето','Осень','Зима']),
 ('shogunates',24,['Сёгунат Камакура','Сёгунат Фукухара','Сёгунат Кисо','Сёгунат Хираидзуми']),
]
TEXTS=[dict(ru=s) for _,_,rows in BANKS for s in rows]

def allocate(reserve,put,pairs):
 from text_encoding import encode
 result={'banks':[]}
 for name,stride,rows in BANKS:
  address=reserve(stride*len(rows),'chronicle_'+name)
  data=b''
  for text in rows:
   raw=encode(text,pairs)+b'\0';assert len(raw)<=stride
   data+=raw+bytes(stride-len(raw))
  put(address,data);result['banks'].append(dict(name=name,offset=address,stride=stride,ru=rows))
 helper=reserve(16,'init_city_copy');put(helper,bytes.fromhex('224d12d866fc4e75'))
 result['copy_helper']=helper
 return result

def patches(data):
 banks={x['name']:x['offset']+0xc000 for x in data['banks']}
 def ptr(value):return struct.pack('>I',value).hex()
 result=[('SMAIN.PRG;1',0x199d4,'c0fc0005','c0fc000c'),
 ('SMAIN.PRG;1',0x199da,'00058e4a',ptr(banks['missions'])),
 ('SMAIN.PRG;1',0x15564,'c0fc0003','c0fc000c'),
 ('SMAIN.PRG;1',0x1556a,'0005832a',ptr(banks['seasons'])),
 ('SMAIN.PRG;1',0x155b0,'c0fc0005','c0fc0010'),
 ('SMAIN.PRG;1',0x155b6,'00058316',ptr(banks['cities'])),
 ('SMAIN.PRG;1',0x155ce,'c0fc0003','c0fc000c'),
 ('SMAIN.PRG;1',0x155d4,'0005832a',ptr(banks['seasons'])),
 ('INIT.PRG;1',0x29c,'224d22d812d8','4eb9'+ptr(data['copy_helper']+0xc000)),
 # Russian country names already contain their title where applicable.
 ('INIT.PRG;1',0x24c,'422bfffc','4e714e71')]
 for i,(p,old) in enumerate(((0x298,0x6ab9a),(0x290,0x6aba0),(0x288,0x6aba6),(0x280,0x6abac))):
  result.append(('INIT.PRG;1',p,ptr(old),ptr(banks['shogunates']+i*24)))
 return result

def apply(image,source,files,data):
 for file,off,old,new in patches(data):
  a=files[file]['lba']*2048+off;before=bytes.fromhex(old);after=bytes.fromhex(new)
  assert len(before)==len(after) and source[a:a+len(before)]==before,(file,hex(off))
  image[a:a+len(after)]=after
