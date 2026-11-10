"""Bounded native-result transliteration. Original random generators remain intact."""
import struct
from generated_names_data import mappings,required_pairs
LOAD=0xc000

def allocate(reserve,put,Code,alphabet,pair_codes):
 addresses={k:reserve(n,'generated_'+k) for k,n in [('convert',224),('match',224),('encode',224),('female',96),('family',128),('country',64)]}
 # Variable-sized tokens in linked pages; zero mask ends a page.
 pages=[];payloads=[];current=bytearray()
 for raw,mask,ru in mappings():
  data=struct.pack('>IBB',mask,len(raw),len(ru))+raw+bytes(alphabet.index(c) for c in ru)
  if len(data)%2:data+=b'\0'
  if len(current)+len(data)+4>60:payloads.append(current);current=bytearray()
  current.extend(data)
 if current:payloads.append(current)
 for data in payloads:pages.append(reserve(64,'generated_tokens'))
 for i,(a,data) in enumerate(zip(pages,payloads)):put(a,struct.pack('>I',LOAD+pages[i+1] if i+1<len(pages) else 0)+data+bytes(60-len(data)))
 reverse=[]
 for pair in required_pairs():
  code=pair_codes.get(pair,pair.encode('ascii') if pair.isascii() else None);assert code is not None,pair
  reverse.append(bytes(alphabet.index(c) for c in pair)+code)
 revpages=[reserve(32,'generated_reverse') for i in range(0,len(reverse),7)]
 for i,a in enumerate(revpages):
  data=b''.join(reverse[i*7:(i+1)*7]);put(a,struct.pack('>I',LOAD+revpages[i+1] if i+1<len(revpages) else 0)+data+bytes([255])*(28-len(data)))
 def save(key,c):
  b=c.finish();limit=next(x[1] for x in [('convert',224),('match',224),('encode',224),('female',96),('family',128),('country',64)] if x[0]==key);assert len(b)<=limit,(key,len(b));put(addresses[key],b)
 def jsr(c,key):c.emit('4eb9'+f'{LOAD+addresses[key]:08x}')
 def jump(c,target):c.emit('4ef9'+f'{LOAD+target:08x}')
 # C ABI (destination, culture, limit): 15 female, 16 male, 32 country.
 c=Code();c.emit('4e56ffb048e73f3c206e000841eeffb0') # A0 source, A1 input copy (corrected below)
 # LEA destination uses A1, not A0.
 c.data[-4:]=bytes.fromhex('43eeffb0')
 c.emit('701f');c.label('copy');c.emit('12d8');c.branch('67','copied');pos=len(c.data);c.emit('51c80000');struct.pack_into('>h',c.data,pos+2,c.labels['copy']-(pos+2));c.emit('4229ffff')
 c.label('copied');c.emit('45eeffb047eeffd07e007a007c003c2e000e02460007')
 c.emit('0cae0000000f0010');c.branch('66','country_mode');c.emit('5046')
 c.label('country_mode');c.emit('0cae000000200010');c.branch('66','loop');c.emit('06460010')
 c.label('loop');c.emit('4a12');c.branch('67','finish');c.emit('0c470020');c.branch('64','finish');c.emit('0c12001b');c.branch('66','match');c.emit('548a');c.branch('60','loop')
 c.label('match');jsr(c,'match');c.branch('60','loop')
 c.label('finish');c.emit('45eeffd0')
 c.label('trim');c.emit('4a47');c.branch('67','encode');c.emit('0c2b0042ffff');c.branch('66','capital');c.emit('538b5347');c.branch('60','trim')
 c.label('capital');c.emit('1012020000ff0c000020');c.branch('65','encode');c.emit('0c00003f');c.branch('62','yo');c.emit('04120020');c.branch('60','encode');c.label('yo');c.emit('0c000041');c.branch('66','encode');c.emit('14bc0040')
 c.label('encode');c.emit('266e0008');jsr(c,'encode');c.emit('20054cdf3cfc4e5e4e75');save('convert',c)
 # Token matcher advances source; all output is capped at 32 character IDs.
 c=Code();c.emit('4bf9'+f'{LOAD+pages[0]:08x}');c.label('page');c.emit('49ed0004')
 c.label('entry');c.emit('2014');c.branch('67','nextpage');c.emit('0d00');c.branch('67','next') # BTST D6,D0
 c.emit('7000102c000441ec0006224a')
 c.label('compare');c.emit('b308');c.branch('66','next');c.emit('5340');c.branch('66','compare')
 c.emit('7000102c0004d4c0') # advance A2 by raw length
 c.emit('43ec0006d2c07000102c0005') # A1=output IDs, D0=count
 c.label('output');c.emit('4a40');c.branch('67','return');c.emit('0c470020');c.branch('64','return');c.emit('16d952475340');c.branch('60','output')
 c.label('next');c.emit('7000102c00047200122c0005d0415e400240fffe d8c0');c.branch('60','entry') # total 6+raw+out aligned: +7 then &~1
 c.label('nextpage');c.emit('2015');c.branch('67','unknown');c.emit('2a40');c.branch('60','page');c.label('unknown');c.emit('5245101a0c000080');c.branch('65','return');c.emit('0c0000a0');c.branch('65','skip');c.emit('0c0000e0');c.branch('65','return');c.label('skip');c.emit('528a')
 c.label('return');c.emit('4e75');save('match',c)
 # Encode IDs as pairs, using the exact build dictionary. Single letters are FC codes.
 c=Code();c.emit('7c00');c.label('loop');c.emit('4a47');c.branch('67','done');c.emit('0c46000e');c.branch('64','done');c.emit('0c470002');c.branch('65','single')
 c.emit('74001412e14a142a00014bf9'+f'{LOAD+revpages[0]:08x}');c.label('page');c.emit('41ed00047206');c.label('entry');c.emit('b450');c.branch('67','found');c.emit('5888');pos=len(c.data);c.emit('51c90000');struct.pack_into('>h',c.data,pos+2,c.labels['entry']-(pos+2));c.emit('2015');c.branch('67','single');c.emit('2a40');c.branch('60','page')
 c.label('found');c.emit('36e800025446548a5547');c.branch('60','loop')
 c.label('single');c.emit('7000101a53470c000042');c.branch('66','dash');c.emit('16fc00205246');c.branch('60','loop');c.label('dash');c.emit('0c00'+f'{alphabet.index("-"):04x}');c.branch('66','letter');c.emit('16fc002d5246');c.branch('60','loop')
 c.label('letter');c.emit('0c46000d');c.branch('64','done');c.emit('16fc00fc0c00003f');c.branch('65','trail');c.emit('5240');c.label('trail');c.emit('0640004016c05446');c.branch('60','loop');c.label('done');c.emit('42134e75');save('encode',c)
 # Caller bridges preserve the original stack contracts and uniqueness checks.
 c=Code();c.emit('2f2f00082f2f00082f2f0008');jsr(c,'convert');c.emit('4fef00182f0a4eb9000176f0588f4a40');c.branch('67','retry');jump(c,0xbcd6);c.label('retry');jump(c,0xbc64);save('female',c)
 c=Code();c.emit('2f0428122f2f000c2f2f000c2f2f000c');jsr(c,'convert');c.emit('4fef000c2f0a4eb9000176f0588f4a40');c.branch('66','ok');c.emit('2484241f4fef000c');jump(c,0xbe78);c.label('ok');c.emit('241f4fef000c');jump(c,0xbeec);save('family',c)
 # The first two scenarios override the caller's culture in the native generator.
 c=Code();c.emit('700010390007fd1e');c.branch('67','selected');c.emit('0c000001');c.branch('66','culture');c.emit('7003');c.branch('60','selected');c.label('culture');c.emit('202e000c');c.label('selected');c.emit('487800202f002f2e0008');jsr(c,'convert');c.emit('4fef000c246efffc4e5e');jump(c,0xc108);save('country',c)
 return dict(**addresses,token_pages=pages,reverse_pages=revpages,token_count=len(mappings()),required_pairs=len(reverse),max_bytes=14)

def patches(d):
 return [(0xbab0,'6100ffc62f0a','4eb9'+f'{LOAD+d["convert"]:08x}'),(0xbaba,'4fef0014','4fef0010'),(0xbcce,'6100fda84fef000c','4ef9'+f'{LOAD+d["female"]:08x}'+'4e71'),(0xbee4,'6100fb924fef000c','4ef9'+f'{LOAD+d["family"]:08x}'+'4e71'),(0xc102,'246efffc4e5e','4ef9'+f'{LOAD+d["country"]:08x}')]

def apply(main,d):
 for off,old,new in patches(d):
  a=bytes.fromhex(old);b=bytes.fromhex(new);assert main[off:off+len(a)]==a;main[off:off+len(b)]=b
