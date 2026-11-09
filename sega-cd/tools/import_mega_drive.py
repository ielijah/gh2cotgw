"""Import established Mega Drive editorial decisions with reproducible provenance."""
from pathlib import Path
import hashlib, json, shutil, re
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent
possible=[ROOT.parent/'mega-drive',WORKSPACE]
MD=next(path for path in possible if (path/'translation/fields.json').is_file())
sources={}
def read(relative):
    raw=(MD/relative).read_bytes()
    sources[relative]=hashlib.sha256(raw).hexdigest()
    return raw
fields=json.loads(read('translation/fields.json'))
geography=json.loads(read('translation/geography.json'))
glossary=read('translation/GLOSSARY.md')
scenarios={}
terms={}
for section,body in re.findall(r'## ([^\n]+)\n(.*?)(?=\n## |\Z)',glossary.decode('utf8'),re.S):
    target=scenarios if section.strip()=='Сценарии' else terms if section.strip()=='Игровые термины' else None
    if target is None: continue
    for line in body.splitlines():
        if not line.startswith('|'): continue
        columns=[value.strip() for value in line.strip('|').split('|')]
        if columns[0] in ('Оригинал','---') or set(columns[0])<=set('-: '): continue
        target[columns[0]]=columns[1]
reference=dict(people=fields['people'],countries=fields['countries'],
               geography={item['source']:item['ru'] for item in geography},
               terms=terms,scenarios=scenarios,
               policy='Mega Drive canonical spellings; Japanese identity links are reviewed separately. ROM field abbreviations are not automatically full historical names.')
(ROOT/'translation/mega-drive-reference.json').write_text(json.dumps(reference,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(ROOT/'translation/mega-drive-glossary-reference.md').write_bytes(glossary)
(ROOT/'assets').mkdir(exist_ok=True)
fonts={}
for face,source in [('regular','translation/reference-cyrillic.bin'),('alternate','translation/reference-cyrillic-alt.bin')]:
    raw=read(source)
    assert len(raw)==66*16
    name='cyrillic-8x16'+('-alternate' if face=='alternate' else '')+'.bin'
    (ROOT/'assets'/name).write_bytes(raw)
    fonts[face]=dict(file=name,sha256=hashlib.sha256(raw).hexdigest(),source=source,glyphs=66,width=8,height=16,
                     order='А..я, Ё, ё')
provenance=read('analysis/font-provenance.json')
(ROOT/'analysis/mega-drive-reuse.json').write_text(json.dumps(dict(source_files=sources,fonts=fonts,
    original_font_provenance=json.loads(provenance),counts={key:len(reference[key]) for key in ('people','countries','geography','terms','scenarios')},
    attribution='http://chief-net.ru/forum/topic.php?forum=4&topic=35&p=1'),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Imported:',', '.join(f'{len(reference[key])} {key}' for key in ('people','countries','geography','terms','scenarios')),'and both 66-glyph font faces')
