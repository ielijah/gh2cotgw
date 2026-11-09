from pathlib import Path
import json,struct,sys
r=Path('sega-cd');sys.path.insert(0,str(r/'tools'));from text_encoding import pieces
v=json.loads((r/'analysis/disc-inventory.json').read_text('utf8'));iso=(r/'disc'/v['image']).read_bytes();files={x['path']:iso[x['lba']*2048:x['lba']*2048+x['size']] for x in v['files']}
p=r/'translation/relocated-text.json';rel=json.loads(p.read_text('utf8'));added=[]
for key,ru in {'14FD4':'9: Далёкая звезда','14FE0':'8: Молитва','14FE8':'7: Волк в седле','14FF4':'6: Погребальный звон','14FFC':'5: Колыбельная','1500A':'4: Земля иноверцев','15024':'2: Дракон Китая','1502C':'1: Кочевой народ'}.items():
 b=files['INIT.PRG;1'];o=int(key,16);ptr=struct.pack('>I',0x66000+o);refs=[x for x in range(0x1778a,0x177ae,4) if b[x:x+4]==ptr];assert len(refs)==1
 e=dict(file='INIT.PRG;1',offset=key,ja=b[o:b.index(0,o)].decode('shift_jis'),ru=ru,kind='music_title',max_columns=22,max_lines=1,references=[dict(file='INIT.PRG;1',offset=f'{refs[0]:X}',before=ptr.hex())]);rel.append(e);added.append(e)
p.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+'\n','utf8')
p=r/'translation/gameplay-dialogue.json';es=json.loads(p.read_text('utf8'))
for fn,off,ru in [('SMAIN.PRG;1',0x4af5a,'Конец приказов'),('SMAIN.PRG;1',0x4bf50,'Не давать имя?'),('XXX.PRG;1',0x443c,'...\nМоя '),('XXX.PRG;1',0x444a,'милая'),('XXX.PRG;1',0x4450,'умница'),('XXX.PRG;1',0x4456,'шалун'),('XXX.PRG;1',0x445c,'знаток')]:
 b=files[fn];ja=b[off:b.index(0,off)].decode('shift_jis');sz=sum(len(v) if k=='raw' else 2 for k,v in pieces(ru))
 if sz>len(ja.encode('shift_jis')):print('defer',hex(off),ru);continue
 e=dict(file=fn,offset=f'{off:X}',ja=ja,ru=ru,kind='dialogue_fragment',max_columns=22,max_lines=2);assert not any(x['file']==fn and int(x['offset'],16)==off for x in es);es.append(e);added.append(e)
p.write_text(json.dumps(es,ensure_ascii=False,indent=2)+'\n','utf8');(r/'analysis/final-music-descriptors.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n','utf8')
for name in ('relocated_text.py','verify.py'):
 p=r/'tools'/name;s=p.read_text('utf8')
 if name=='relocated_text.py':
  s=s.replace("if ending: assert", "if entry.get('kind')=='music_title': assert len(entry['ru'])<=22 and '\\n' not in entry['ru']\n    elif ending: assert")
  s=s.replace("if ending:\n        assert", "if entry.get('kind')=='music_title':\n        assert file=='INIT.PRG;1' and 0x14fd4<=off<=0x1502c\n        load=0x66000;low,high=0x1778a,0x177ae\n    elif ending:\n        assert")
 else:
  s=s.replace("if entry.get('kind')=='ending_caption':\n        assert entry['file']", "if entry.get('kind')=='music_title':\n        assert entry['file']=='INIT.PRG;1' and 0x14fd4<=off<=0x1502c\n        load=0x66000;low,high=0x1778a,0x177ae\n    elif entry.get('kind')=='ending_caption':\n        assert entry['file']")
  s=s.replace("if entry.get('kind')=='ending_caption':\n        assert len", "if entry.get('kind')=='music_title':\n        assert len(entry['ru'])<=22 and '\\n' not in entry['ru']\n    elif entry.get('kind')=='ending_caption':\n        assert len")
 p.write_text(s,'utf8')
print('Added',len(added))
