"""Standalone Russian manual with vector diagrams; no source scans embedded."""
from pathlib import Path
import re,json,hashlib
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader,PdfWriter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
TEXT=ROOT/'docs/manuals/manual-ru.md'
for name,file in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
W,H=595.28,841.89
BLUE=HexColor('#183d50');INK=HexColor('#202c33');GREY=HexColor('#63747b');PALE=HexColor('#edf3f5')
raw=TEXT.read_text('utf8');parts=re.split(r'^### (\d+) \| (.+)\n',raw,flags=re.M)
sections=[(int(parts[i]),parts[i+1],parts[i+2].strip()) for i in range(1,len(parts),3)]
assert [s[0] for s in sections]==list(range(64))
CJK=re.compile(r'[\u3000-\u30ff\u3400-\u9fff\uf900-\ufaff\uff61-\uff9f]')
assert not CJK.search(raw)
buf=BytesIO();c=canvas.Canvas(buf,pagesize=(W,H));report=[];expected=[];page_num=0
def para(text,x,y,width,size=11.5,leading=16):
    text=re.sub('[\u2010-\u2015]','-',text)
    assert all(ord(ch)<=32 or ord(ch) in pdfmetrics.getFont('Body').face.charToGlyph for ch in text)
    p=Paragraph(escape(text).replace('\n','<br/>'),ParagraphStyle('p',fontName='Body',fontSize=size,leading=leading,textColor=INK))
    _,h=p.wrap(width,H);assert y-h>42,(page_num,text[:60],y-h)
    p.drawOn(c,x,y-h);expected.append((page_num,text));return y-h-10
def start(title,subtitle='Руководство пользователя • Mega-CD'):
    global page_num
    page_num+=1;c.setFillColor(BLUE);c.rect(0,H-95,W,95,fill=1,stroke=0)
    p=Paragraph(escape(title),ParagraphStyle('title',fontName='Bold',fontSize=19,leading=23,textColor=HexColor('#ffffff')))
    _,h=p.wrap(W-72,70);p.drawOn(c,36,H-23-h)
    c.setFillColor(HexColor('#cfdee4'));c.setFont('Body',9);c.drawString(36,H-80,subtitle)
    c.setFillColor(GREY);c.setFont('Body',8);c.drawString(36,23,'Серый волк и белая лань • Тайная история Юань');c.drawRightString(W-36,23,str(page_num))
def diagram(items,y,title):
    rows=(len(items)+1)//2;height=rows*49+25
    if y-height<50:return y
    c.setFillColor(BLUE);c.setFont('Bold',10);c.drawString(36,y-12,title)
    width=(W-82)/2
    for n,item in enumerate(items):
        x=36+(n%2)*(width+10);top=y-25-(n//2)*49
        c.setFillColor(PALE);c.roundRect(x,top-40,width,40,5,fill=1,stroke=0)
        p=Paragraph(escape(item),ParagraphStyle('box',fontName='Body',fontSize=10,leading=13,textColor=BLUE,alignment=1))
        _,h=p.wrap(width-12,35);p.drawOn(c,x+6,top-20-h/2)
    return y-height
diagrams={
5:('Управление державой',['Правитель → столица','Наместники → провинции','Советник → управление','Полководцы → война и посольства']),
7:('Наследование',['Правитель → сыновья','Сын-полководец → правящая семья','Дочь + полководец → родство','Смерть правителя → выбор наследника']),
8:('Состав войска',['Армия: до 5 легионов','Легион: до 4 отрядов','Отряд: солдаты одного вида','Первый легион: главнокомандующий']),
10:('Цикл игры',['Управление и развитие','Подготовка похода','Походная карта','Тактическое сражение','Послевоенные решения','Возвращение к управлению']),
11:('Кнопки контроллера',['START: начало / меню','A: страницы и сведения','B: отмена / конец хода','C: подтверждение','Крестовина: выбор и движение']),
21:('Порядок стратегического хода',['Столица державы','Подчинённые провинции','Следующая держава','Все закончили → новый сезон']),
23:('Пять разделов политики',['Распределение жителей','Общий курс','Вложения','Военные приготовления','Дипломатия']),
29:('Купцы',['Уйгурские','Мусульманские','Китайские','Венецианские']),
32:('Шкалы ордо',['Силы правителя → расход на действия','Расположение супруги → успех встречи','Оранжевый: расположение растёт','Синий: расположение падает']),
34:('Экран провинции: первая страница',['1. Золото','2. Продовольствие','3. Население','4. Экономика','5. Сельское хозяйство','6. Лояльность','7. Культура','8. Климат']),
36:('Распределение труда: всего 100%',['Земледелие','Животноводство','Местные промыслы','Строительство городов']),
38:('Способности персонажа',['Политика → расход сил','Военное искусство → урон','Командование → действия и порядок','Харизма → верность и дипломатия']),
42:('Дополнительные условия победы',['Нападающий: занять все города и замки','Обороняющийся: продержаться 30 дней']),
50:('Стоимость тактических действий',['Движение: 2 или 3','Ближняя атака: 3','Обстрел: 3','Натиск: 5']),
51:('Команды и расход подвижности',['Личное руководство: 4','Восстановление порядка: 4','Сведения о своих: 0','Сведения о враге: 2'])}
start('Серый волк и белая лань','Тайная история Юань • Полностью русское издание');y=H-135
for t in ['Руководство пользователя Mega-CD','Полный русский текст руководства: управление, команды, устройство державы, войска, походы, сражения, события и сценарии.','Все страницы заново свёрстаны по-русски. Японские сканы, надписи и изображения с японским текстом исключены. Схемы перерисованы с русскими подписями.','Для навигации используйте содержание и закладки PDF. Названия кнопок контроллера и технические обозначения сохранены: они нужны для работы с игрой и аппаратурой.','Основой служит руководство KOEI 1993 года, T-76054. Редакторские примечания поясняют особенности русификации. Исторические очерки переданы как текст оригинального издания; спорная хронология не переносилась автоматически в биографии игры.','Правила и возрастные пороги описывают механики оригинальной игры. Исторические контакты поддержки приведены только как часть выходных данных.']:y=para(t,36,y,W-72,12,18)
diagram(['Стратегия','Дипломатия','Армия','Династия'],y-15,'От племени к империи');c.showPage()
for idx,title,body in sections:
    if idx==2:body='Мир игры и цели - стр. 5–12.\n\nУправление, запуск и сохранения - стр. 13–19.\n\nСправочник, музыка и настройки - стр. 20–22.\n\nСтратегические команды - стр. 23–35.\n\nПровинции, персонажи и войска - стр. 36–43.\n\nПоходы и сражения - стр. 44–54.\n\nСобытия - стр. 55–56.\n\nСценарии и доступные правители - стр. 57–62.\n\nМузыка и выходные данные - стр. 63–65.'
    body=body.replace('На рисунке:','Элементы экрана:').replace('Виды купцов на рисунке: сверху слева — уйгурские, сверху справа — мусульманские; снизу слева — китайские, снизу справа — венецианские.','Виды купцов: уйгурские, мусульманские, китайские и венецианские.').replace('Товары на рисунке, слева направо:','Виды товаров:').replace('; ниже —','; также —').replace('Реплика на рисунке:','Вопрос при выборе:').replace('; обозначения приведены на оригинальной странице.','; основные центры отмечены отдельно.')
    body=body.replace('на стр. 16 оригинала','на стр. 19')
    start(title);y=H-120;size,leading=(10.5,13.5) if idx==60 else (11.5,16)
    for p in body.split('\n\n'):y=para(p,36,y,W-72,size,leading)
    if idx in diagrams:caption,items=diagrams[idx];y=diagram(items,y-8,caption)
    report.append({'section':idx,'output_page':page_num,'bottom_y':round(y,2),'font_size':size});c.showPage()
c.save();reader=PdfReader(buf);writer=PdfWriter()
for p in reader.pages:writer.add_page(p)
for idx,title,body in sections:writer.add_outline_item(title,idx+1)
writer.add_metadata({'/Title':'Серый волк и белая лань. Руководство Mega-CD на русском','/Author':'Перевод руководства KOEI (1993)','/Subject':'Полностью русское издание с русскими схемами'})
dest=OUT/'Genchou-Hishi-Mega-CD-Manual-RU.pdf'
with dest.open('wb') as f:writer.write(f)
final=PdfReader(dest);norm=lambda s:re.sub(r'\s+','',s);texts=[p.extract_text() for p in final.pages]
assert len(texts)==65 and len(final.outline)==64
assert not any(CJK.search(t) for t in texts)
for n,text in expected:assert norm(text) in norm(texts[n-1]),(n,text[:80])
assert all(not list(p.images) for p in final.pages)
(OUT/'manual-ru-validation.json').write_text(json.dumps({'pages':65,'bookmarks':64,'japanese_characters':0,'raster_images':0,'all_written_paragraphs_verified':True,'translation_sha256':hashlib.sha256(TEXT.read_bytes()).hexdigest(),'layout':report},ensure_ascii=False,indent=2),'utf8')
print(dest);print('PASS: 65 Russian-only pages, 64 bookmarks, no CJK text, no raster images; all text verified')
