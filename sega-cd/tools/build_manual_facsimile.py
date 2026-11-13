"""Russian manual restoration, using original page artwork and explicit text areas.

Only reviewed page layouts are included. This is deliberately not a completed manual.
Coordinates refer to the 1100px source render, with the origin at the top left.
"""
from pathlib import Path
from io import BytesIO
from xml.sax.saxutils import escape
import json, re
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'
OUT.mkdir(parents=True, exist_ok=True)
for name, filename in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts') / filename)))
parts = re.split(r'^### (\d+) \| (.+)\n', (ROOT/'docs/manuals/manual-ru.md').read_text('utf8'), flags=re.M)
sections = {int(parts[i]): parts[i+2].strip().split('\n\n') for i in range(1,len(parts),3)}
OUTPUT = OUT/'Genchou-Hishi-Manual-RU-original-layout-preview.pdf'
C = canvas.Canvas(str(OUTPUT), pagesize=(600,600))
C.setTitle('Тайная история Юань - восстановление оригинальной вёрстки (образцы)')
C.setAuthor('Русский перевод руководства KOEI')
report=[]

def text(value, box, size=23, bold=False, color='#111111', align=0):
    x,y,w,h=box
    value=re.sub('[\u2010-\u2015]', '-', value)
    for fs in [size-i*.25 for i in range(40)]:
        p=Paragraph(escape(value).replace('\n','<br/>'),ParagraphStyle('p',fontName='Bold' if bold else 'Body',fontSize=fs,leading=fs*1.35,textColor=color,alignment=align))
        _,ph=p.wrap(w,h)
        if ph <= h: break
    else: raise ValueError(('Text overflow',value,box))
    p.drawOn(C,x,1100-y-ph)
    report.append({'page':PAGE,'text':value,'box':box,'font_size':fs})

def wipe(box, color='#ffffff'):
    x,y,w,h=box
    C.setFillColor(color);C.rect(x,1100-y-h,w,h,fill=1,stroke=0)

def patch_from_blank(box, sample):
    """Keep the scan's paper/halftone texture instead of adding a flat new style."""
    x,y,w,h=box
    fragment=SOURCE.crop(sample)
    tiled=Image.new('RGB',(int(w)+1,int(h)+1))
    for yy in range(0,tiled.height,fragment.height):
        for xx in range(0,tiled.width,fragment.width):tiled.paste(fragment,(xx,yy))
    C.drawImage(ImageReader(tiled),x,1100-y-h,w,h)

def start(index, sidebar, sidebox, sample):
    global PAGE,SOURCE
    PAGE=index
    SOURCE=Image.open(ROOT/f'tmp/pdfs/source-{index+1:02}.png').convert('RGB').resize((1100,1100))
    C.saveState();C.scale(600/1100,600/1100)
    C.drawImage(ImageReader(SOURCE),0,0,1100,1100)
    patch_from_blank(sidebox,sample)
    x,y,w,h=sidebox
    C.saveState();C.translate(x+w/2,1100-y-16);C.rotate(-90)
    C.setFillColor('#111111');C.setFont('Bold',20)
    C.drawString(0,-7,sidebar);C.restoreState()
    C.bookmarkPage(f'p{index}');C.addOutlineEntry(f'Страница {index-1}: {sidebar}',f'p{index}')

def finish():C.restoreState();C.showPage()

def gray(title,box,sample):
    patch_from_blank(box,sample);x,y,w,h=box
    text(title,(x+8,y+2,w-16,h-2),23,True)

def band(title,box,sample,color='#824c2d'):
    patch_from_blank(box,sample);x,y,w,h=box
    text(title,(x+8,y+8,w-16,h-12),29,True,color,1)

# Printed page 5. All five headings and paragraphs retain their original positions.
start(6,'Мир «Тайной истории Юань»',(998,550,38,480),(1000,900,1034,935))
for title,hy,by,bottom,p in [
    ('Наместник',77,115,328,0),('Советник',340,381,593,1),
    ('Полководец',607,648,826,2),('Свободный человек',839,881,937,3),
    ('Супруги',950,991,1035,4)]:
    gray(title,(99,hy,600,32),(480,hy+3,680,hy+28))
    wipe((319,hy+32,668,min(bottom+10,1038)-(hy+32)))
    text(sections[6][p],(325,by,649,bottom-by),23)
finish()

# Printed page 6. Original section separators and side ornament stay in place.
start(7,'Мир «Тайной истории Юань»',(64,552,40,485),(65,900,102,930))
for title,hy,by,bottom,p in [('Принц',77,116,180,0),('Принцесса',190,231,295,1)]:
    gray(title,(127,hy,600,32),(480,hy+3,700,hy+27))
    wipe((349,hy+32,662,bottom-(hy+32)+9));text(sections[7][p],(355,by,645,bottom-by+8),23)
band('Выбор наследника',(180,309,766,57),(200,315,380,358))
wipe((348,378,663,224));text(sections[7][2],(355,382,643,215),23)
band('Переход к мировой кампании',(180,615,766,57),(200,622,380,660))
wipe((348,682,663,341));text(sections[7][3],(355,690,643,326),25)
finish()

# Printed page 22. Original icons are not redrawn or replaced by generic boxes.
start(23,'Стратегические команды',(55,552,41,484),(56,900,94,930))
rows=[
    (79,113,215,'Общий курс','Определяет основное направление политики.', ['Хозяйство','Армия','Богатство','На усмотрение']),
    (272,307,408,'Вложения','Куда вкладывать средства. В провинции необходим советник.', ['Экономика','Сельское\nхозяйство','Укрепления','На усмотрение']),
    (464,496,599,'Военные приготовления','Выберите, на чём сосредоточить военные приготовления.', ['Численность','Виды войск','Оснащение','На усмотрение']),
    (655,686,791,'Дипломатия','Курс на завоевания допускает походы против других держав.', ['Завоевания','Давление','Равноправие','Покорность'])]
for hy,by,ly,title,body,labels in rows:
    wipe((375,hy-3,620,34));text(title,(375,hy-1,610,34),24,True,'#a73436')
    wipe((344,by-4,659,39));text(body,(347,by,645,35),21)
    wipe((346,ly-3,522,47))
    for j,label in enumerate(labels):text(label,(347+j*131,ly,121,46),18,align=1)
gray('Изменить политику - 5 сил',(117,840,607,33),(500,844,715,869))
wipe((344,878,661,33));text('Выберите раздел политики, который хотите изменить.',(347,880,645,31),21)
wipe((343,981,659,35))
for j,label in enumerate(['Труд жителей','Общий курс','Вложения','Армия','Дипломатия']):text(label,(345+j*131,983,124,29),18,align=1)
finish()

# Printed page 40. Preserve both the game buttons and the original unit illustrations.
start(41,'Провинции, персонажи и войска',(51,553,42,483),(52,950,92,980))
diamond=SOURCE.crop((344,79,370,107))
wipe((338,72,667,930))
for j,p in enumerate(sections[41]):
    name,body=p.split(' — ',1)
    culture,description=body.split('. ',1)
    y=[80,156,233,310,386,463,540,617,694,771,848,925][j]
    C.drawImage(ImageReader(diamond),344,1100-y-28,26,28)
    text(name,(373,y,628,29),23,True,'#a73436')
    text(culture+'. '+description,(344,y+30,657,46),18.5)
finish()

# Printed page 54. Retain the illustrated ribbon; replace only its lettering.
start(55,'Объединение Монголии',(59,552,40,485),(60,930,97,970))
patch_from_blank((137,98,842,61),(150,151,900,162))
text('Объединение Монголии',(160,103,560,48),35,True,'#fff8df')
text('Сценарий 1  •  1184',(735,119,239,36),22,True,'#fff8df')
wipe((558,188,453,336))
text('\n\n'.join(sections[55][:2]),(564,193,438,329),22)
wipe((344,526,667,499))
text('\n\n'.join(sections[55][2:]),(351,535,647,478),25)
wipe((127,203,408,310))
shot=Image.open(ROOT/'analysis/qa-province-only/s0-cold.png').convert('RGB')
C.drawImage(ImageReader(shot),128,1100-216-284,406,284)
finish()

C.save()
(OUT/'manual-facsimile-progress.json').write_text(json.dumps({'status':'layout_samples_not_complete_manual','source_pages': [6,7,23,41,55], 'total_source_pages':64,'output':str(OUTPUT),'text_blocks':report},ensure_ascii=False,indent=2),'utf8')
print(OUTPUT)
