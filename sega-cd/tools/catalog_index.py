"""Russian catalogue ordering; permute complete records and matching biographies."""
import struct
START,COUNT,STRIDE,BIO,COUNTS=0x15232,342,20,0x16fba,0x17776
GROUPS=['А-Б','В-Г','Д-З','И-К','Л-М','Н-П','Р-С','Т-У','Ф-Ч','Ш-Я']
WIFE_NAMES,WIFE_PORTRAITS,WIFE_BIOS,WIFE_COUNTS,WIFE_COUNT=0x16dc2,0x16f12,0x17512,0x17780,84

def wives_plan(source,files,entries,relocated):
 base=files['INIT.PRG;1']['lba']*2048
 translated={0x66000+int(e['offset'],16):e['ru'].strip() for e in entries+relocated if e['file']=='INIT.PRG;1'}
 pointers=struct.unpack_from('>84I',source,base+WIFE_NAMES)
 names=[translated[p] for p in pointers]
 keys=[n.upper().replace('Ё','Е') for n in names]
 order=sorted(range(WIFE_COUNT),key=lambda i:keys[i])
 counts=[sum(g[0]<=keys[i][0]<=g[-1] for i in order) for g in GROUPS]
 assert sum(counts)==WIFE_COUNT
 return order,counts,names
def plan(entries):
 names={int(e['offset'],16):e['ru'] for e in entries if e['file']=='INIT.PRG;1' and START<=int(e['offset'],16)<START+COUNT*STRIDE and (int(e['offset'],16)-START)%STRIDE==0}
 assert len(names)==COUNT and all(names.values())
 def key(i):return names[START+i*STRIDE].upper().replace('Ё','Е')
 order=sorted(range(COUNT),key=key);counts=[]
 for group in GROUPS:
  counts.append(sum(group[0]<=key(i)[0]<=group[-1] for i in order))
 assert sum(counts)==COUNT and all(0<n<256 for n in counts)
 return order,counts,names

def apply(image,source,files,entries,relocated=()):
 order,counts,names=plan(entries);base=files['INIT.PRG;1']['lba']*2048
 records=bytes(image[base+START:base+START+COUNT*STRIDE]);bios=bytes(image[base+BIO:base+BIO+COUNT*4])
 # Biography pointers have already been rebuilt by biography_bank.
 for dest,old in enumerate(order):
  image[base+START+dest*STRIDE:base+START+(dest+1)*STRIDE]=records[old*STRIDE:(old+1)*STRIDE]
  image[base+BIO+dest*4:base+BIO+(dest+1)*4]=bios[old*4:(old+1)*4]
 image[base+COUNTS:base+COUNTS+10]=bytes(counts)
 inverse={old:dest for dest,old in enumerate(order)}
 for e in entries:
  off=int(e['offset'],16)
  if e['file']=='INIT.PRG;1' and off in names:e['destination_offset']=f'{START+inverse[(off-START)//STRIDE]*STRIDE:X}'
 wo,wc,wn=wives_plan(source,files,entries,list(relocated))
 for table,stride in [(WIFE_NAMES,4),(WIFE_PORTRAITS,2),(WIFE_BIOS,4)]:
  original=bytes(image[base+table:base+table+WIFE_COUNT*stride])
  for dest,old in enumerate(wo):
   image[base+table+dest*stride:base+table+(dest+1)*stride]=original[old*stride:(old+1)*stride]
 image[base+WIFE_COUNTS:base+WIFE_COUNTS+10]=bytes(wc)
 return dict(order=order,counts=counts,groups=GROUPS,record_start=START,biography_table=BIO,
             wives=dict(order=wo,counts=wc,names=[wn[i] for i in wo]))
