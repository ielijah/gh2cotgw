"""Russian catalogue ordering; permute complete records and matching biographies."""
import struct
START,COUNT,STRIDE,BIO,COUNTS=0x15232,342,20,0x16fba,0x17776
GROUPS=['А-Б','В-Г','Д-З','И-К','Л-М','Н-П','Р-С','Т-У','Ф-Ч','Ш-Я']
def plan(entries):
 names={int(e['offset'],16):e['ru'] for e in entries if e['file']=='INIT.PRG;1' and START<=int(e['offset'],16)<START+COUNT*STRIDE and (int(e['offset'],16)-START)%STRIDE==0}
 assert len(names)==COUNT and all(names.values())
 def key(i):return names[START+i*STRIDE].upper().replace('Ё','Е')
 order=sorted(range(COUNT),key=key);counts=[]
 for group in GROUPS:
  counts.append(sum(group[0]<=key(i)[0]<=group[-1] for i in order))
 assert sum(counts)==COUNT and all(0<n<256 for n in counts)
 return order,counts,names

def apply(image,source,files,entries):
 order,counts,names=plan(entries);base=files['INIT.PRG;1']['lba']*2048
 records=bytes(image[base+START:base+START+COUNT*STRIDE]);bios=bytes(image[base+BIO:base+BIO+COUNT*4])
 assert bios==source[base+BIO:base+BIO+COUNT*4]
 for dest,old in enumerate(order):
  image[base+START+dest*STRIDE:base+START+(dest+1)*STRIDE]=records[old*STRIDE:(old+1)*STRIDE]
  image[base+BIO+dest*4:base+BIO+(dest+1)*4]=bios[old*4:(old+1)*4]
 image[base+COUNTS:base+COUNTS+10]=bytes(counts)
 inverse={old:dest for dest,old in enumerate(order)}
 for e in entries:
  off=int(e['offset'],16)
  if e['file']=='INIT.PRG;1' and off in names:e['destination_offset']=f'{START+inverse[(off-START)//STRIDE]*STRIDE:X}'
 return dict(order=order,counts=counts,groups=GROUPS,record_start=START,biography_table=BIO)
