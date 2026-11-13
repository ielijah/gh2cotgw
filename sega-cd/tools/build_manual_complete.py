"""64-page Russian manual, original artwork/layout, one body size per page.

All text rectangles are planned before painting. The smallest fitting size is applied
to every body paragraph on a page; headings/captions have their own fixed styles.
"""
from pathlib import Path
from io import BytesIO
from xml.sax.saxutils import escape
import re,json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/pdf';OUT.mkdir(exist_ok=True,parents=True)
for name,file in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
raw=(ROOT/'docs/manuals/manual-ru.md').read_text('utf8')
parts=re.split(r'^### (\d+) \| (.+)\n',raw,flags=re.M)
T={int(parts[i]):parts[i+2].strip().split('\n\n') for i in range(1,len(parts),3)}
titles={int(parts[i]):parts[i+1] for i in range(1,len(parts),3)}
plans={i:[] for i in range(64)};page=0
sources={}
def src(i):
    if i not in sources:
        p=ROOT/f'tmp/pdfs/hi-source-{i+1:02}.png'
        if not p.exists():p=ROOT/f'tmp/pdfs/source-{i+1:02}.png'
        sources[i]=Image.open(p).convert('RGB').resize((2200,2200))
    return sources[i]
def put(kind,**args):plans[page].append({'kind':kind,**args})
def B(s,y,h,x=345,w=650):put('text',s=s,box=[x,y,w,h],role='body')
def L(s,x,y,w=130,h=50,size=18,align=1):put('text',s=s,box=[x,y,w,h],role='label',size=size,align=align)
def H(s,y,style='gray',x=115,w=None):put('heading',s=s,y=y,style=style,x=x,w=w or (600 if style=='gray' else 880))
def G(box,target=None,source=None):put('crop',box=box,target=target,source=page if source is None else source)
ICON_BOXES={
26:[[95,y,209,y+56] for y in [118,500,615]],
32:[[95,149,209,205]],
22:[[95,534,208,592]],27:[[117,y,230,y+56] for y in [117,233,422,539,769,884]],
28:[[95,y,209,y+56] for y in [118,388,615,807]],
30:[[143,y,257,y+56] for y in [310,388,464,541,617,694,770,847]],
31:[[159,80,273,135],[111,501,225,556],[111,696,225,752],[111,814,225,870],[111,930,225,988]],
34:[[96,y,209,y+57] for y in [554,709,861]],
}
def I(y,dest=None):
    xx=115 if page%2 else 95
    b=min(ICON_BOXES[page],key=lambda b:abs(b[1]-y)) if page in ICON_BOXES else [xx,y,xx+115,y+56]
    G(b,[115,y if dest is None else dest,123,62])
def S(file,box):put('screen',file=file,box=box)
def Q(s,x,y,w,h):put('diagram',s=s,box=[x,y,w,h])
def seq(paragraphs,start=165,end=1020,heads=None,icons=None):
    # Allocate room by translated length; keep a substantial minimum for short items.
    weights=[Paragraph(escape(p).replace('\n','<br/>'),ParagraphStyle('measure',fontName='Body',fontSize=21,leading=26.46)).wrap(650,2000)[1] for p in paragraphs];total=sum(weights)
    avail=end-start-48*len(paragraphs);y=start
    for j,p in enumerate(paragraphs):
        height=avail*weights[j]/total
        heading=(heads[j] if heads else re.split(r'[.:]| — ',p,maxsplit=1)[0])
        H(heading,y)
        if icons and j<len(icons) and icons[j] is not None:I(icons[j],y+40)
        B(p,y+40,height)
        y+=height+48
def allbody(i,y=165,h=850):B('\n\n'.join(T[i]),y,h)
def figure_labels(labels,x,y,step=132,w=125):
    for j,label in enumerate(labels):L(label,x+j*step,y,w)
def command_rows(rows):
    for y,end,head,par,iy in rows:
        H(head,y)
        if iy is not None:I(iy,y+40)
        B(par,y+40,end-y-48)
def chapter(i):
    if i<11:return 'Мир «Тайной истории Юань»','#8c5739','#d8bd91'
    if i<21:return 'Перед началом игры','#3e87ad','#a7c9d7'
    if i<34:return 'Стратегические команды','#548358','#bfd0a7'
    if i<42:return 'Провинции, персонажи и войска','#66628c','#b9b9d6'
    if i<53:return 'Походы и сражения','#4d7655','#bdc8aa'
    if i<55:return 'События','#90741e','#d6c68c'
    if i<61:return 'Сценарии','#8d2029','#d78391'
    return 'Музыка игры','#a66b36','#dcba91'

# Covers, contents, preliminary instructions.
page=0
put('cover')
page=1
H('MEGA-CD: обращение с диском',65,'ribbon',x=75,w=950)
put('frame',box=[70,150,955,450],color='#253f73')
L('Бережное обращение',95,170,415,40,25,0);B(T[1][0],220,340,95,420)
L('Чистка диска',560,170,415,40,25,0);B(T[1][1],220,340,560,420)
put('frame',box=[70,625,475,350],color='#253f73')
L('Здоровье и безопасность',90,640,435,40,25,0);B(T[1][2].replace('Предупреждение оригинального руководства: ',''),687,275,90,435)
put('frame',box=[570,625,455,350],color='#a44971',fill='#d594b0')
B(T[1][3],650,310,590,415);B(T[1][4],990,75,75,950)
page=2
L('Содержание',100,70,900,65,37)
for j,(title,detail,num) in enumerate([
('Мир «Тайной истории Юань»','Сценарии, цели, персонажи, наследование, армия и ход игры',2),
('Перед началом игры','Управление, память, запуск, сохранение, справочник и музыка',10),
('Стратегические команды','Политика, приказы, кадры, война, хозяйство, дипломатия и ордо',20),
('Провинции, персонажи и войска','Показатели, родство и виды отрядов',33),
('Походы и сражения','Победа, подготовка, походная карта, поле боя и последствия',41),
('События','Сезонные события и случайные происшествия',52),
('Сценарии','Исторические вступления пяти сценариев',54),
('Доступные правители','Державы и правители для выбора в каждом сценарии',59),
('Музыка игры','Музыкальный мир игры и композитор Митиру Осима',60),
('Поддержка','Обслуживание и выходные данные оригинального издания',61)]):
    y=180+j*82;L(title,115,y,810,35,24,0);L(str(num),940,y,60,35,24,2);B(detail,y+36,40,135,830)
page=3
H('Мир «Тайной истории Юань»',80,'ribbon');B('\n\n'.join(T[3]),190,550)
H('Пять сценариев и конечная цель',770,'band')
B('В игре представлены пять сценариев.',840,45)
H('Сценарий 1: объединение Монголии',900)
B('Начало - 1184 год. Цель - объединить Монгольское нагорье.',945,80)
page=4
B(T[4][0].split('Если это',1)[1].join(['Если это','']),70,250)
command_rows([(335,665,'Сценарий 2: война Гэмпэй',T[4][1],None),(680,785,'Сценарий 3: возвышение Чингисхана',T[4][2],None),(800,905,'Сценарий 4: основание Юань',T[4][3],None),(920,1030,'Сценарий 5: путь к мировой империи',T[4][4],None)])
page=5
H('Поражение',80,'band');B(T[5][0],155,120)
H('Персонажи и их отношения',300,'band');H('Устройство державы',382)
put('state_relationships')
H('Правитель',740);B('\n\n'.join(T[5][1:]),790,240)
page=6
command_rows([(77,325,'Наместник',T[6][0],None),(330,575,'Советник',T[6][1],None),(580,810,'Полководец',T[6][2],None),(815,945,'Свободный человек',T[6][3],None),(950,1040,'Супруги',T[6][4],None)])
page=7
H('Принц',77);B(T[7][0],116,75)
H('Принцесса',205);B(T[7][1],248,86)
H('Выбор наследника',350,'band');B(T[7][2],425,235)
H('Переход к мировой кампании',680,'band');B(T[7][3],755,275)
page=8
H('Устройство армии',80,'band');put('army_diagram',box=[300,175,570,310])
command_rows([(510,595,'Солдат',T[8][0],None),(600,730,'Отряд',T[8][1],None),(735,870,'Легион',T[8][2],None),(875,1030,'Армия',T[8][3],None)])
page=9
H('Ход игры',80,'band');H('1. Начало партии',160);B(T[9][0],205,100)
H('2. Укрепление державы',330);S('qa-province-only/s0-cold.png',[120,400,345,270]);B(T[9][1],380,360,x=495,w=510)
B(T[9][2],755,120);H('3. Подготовка похода',900);B(T[10][0].split('Игра перейдёт')[0],945,85)
page=10
put('battle_pair');B('Походная карта: команды легионам. При столкновении начинается тактическое сражение: команды получают отдельные отряды.',430,110)
H('4. Объединение',565);B('\n\n'.join(T[10][1:3]),610,180)
H('Ход игры',815);Q('Начало → развитие державы → поход → сражение\n↓\nВозвращение к управлению → объединение',350,875,650,130)
page=11
H('Перед началом игры',80,'ribbon');H('Контроллер',190,'band')
command_rows([(290,390,'START',T[11][0],None),(400,675,'A',T[11][1],None),(690,840,'B',T[11][2],None),(855,935,'C',T[11][3],None),(950,1030,'Крестовина',T[11][4],None)])
page=12
command_rows([(80,290,'Ввод чисел',T[12][0],None),(310,455,'Распределение жителей',T[12][1],None)])
H('Ввод имени',475,'band');S('keyboard-ru-2828.png',[120,575,300,225])
B('\n\n'.join(T[12][2:]),550,475,x=445,w=550)
page=13
H('Картридж резервной памяти',80,'band');B(T[13][0],160,240)
H('Использование RAM-картриджа',425);B(T[13][1],475,300)
H('Файлы сохранений',800);B('\n\n'.join(T[13][2:]).replace('стр. 16 оригинала','стр. 16'),850,175)
page=14
H('Запуск игры',80,'band');B(T[14][0],160,75);B(T[14][1],250,480)
H('Новая игра',755,'band');put('main_menu',box=[120,850,280,175]);B(T[14][2],835,190,x=435,w=565)
page=15
B('\n\n'.join(T[15][:3]),75,330);H('Сохранение игры',430,'band')
H('Необходимая память',540);B(T[15][3],585,200)
H('Запись данных',810);B(T[15][4],855,170)
page=16
H('Завершение игры',80,'band');B('\n\n'.join(T[16][:2]),165,370)
H('Извлечение диска MEGA-CD',565,'band');B(T[16][2],650,365)
page=17
H('Загрузка сохранения',80,'band');B(T[17][0],165,170)
H('Игра без RAM-картриджа',370,'band');H('Запуск игры',465);B('\n\n'.join(T[17][1:]),515,300)
H('Новая партия',845);B('Выбор сценария и настройка новой партии выполняются так же, как при использовании RAM-картриджа (стр. 13).',890,70)
H('Завершение',970);B('Завершение игры описано на стр. 15.',1010,30)
page=18
H('Справочник персонажей',80,'band');B(T[18][0],155,75)
H('Полководцы',245);S('catalog-final-card-2839.png',[120,290,225,196.875]);B(T[18][1],290,215,x=410,w=585)
H('Дети',520);S('manual-child-biography.png',[120,565,225,196.875]);B(T[18][2],565,205,x=410,w=585)
H('Жёны',795);S('manual-wife-biography.png',[120,840,225,196.875]);B(T[18][3]+'\n\n'+T[18][4],840,195,x=410,w=585)
page=19
H('Прослушивание музыки',80,'band');S('qa-music-switch/title-0.png',[120,215,330,230]);B(T[19][0],165,260,x=490,w=515)
for j,p in enumerate(T[19][1:]):
    y=460+j*80;L(['СТОП','ПУСК / ПАУЗА','НАЗАД / ВПЕРЁД','PRG','ПОВТ','RND','EXIT'][j],125,y,195,40,20)
    B(p,y,555/7-8)
page=20
H('Служебное меню',80,'band');B(T[20][0],160,60)
S('manual-service-menu.png',[120,245,300,262.5])
for j,p in enumerate(T[20][1:]):
    y=240+j*128
    B(p,y,118,x=450,w=550)
page=21
H('Стратегические команды',80,'ribbon');H('Стратегический ход',190,'band');B(T[21][0],270,120,x=120,w=880)
put('annotated_screen',file='manual-strategy-screen.png',box=[120,410,370,323.75],marks=[(1,30,31),(2,77,45),(3,30,98),(4,210,26),(5,210,92),(6,144,183)]);B(T[21][1],410,310,x=540,w=460)
B('\n\n'.join(T[21][2:]),755,275,x=120,w=880)
page=22
H('Расход сил',80);B(T[22][0],125,255);G([113,185,235,399],[120,175,150,260])
H('Политика',410,'band');B(T[22][1],485,70)
H('Новая политика - 8 сил',575);I(480,620);B(T[22][2],620,160)
B(T[22][3],795,85);B(T[22][4],895,65)
for j,label in enumerate(['Земледелие','Скот','Промыслы','Города']):G([325+j*132,925,440+j*132,980],[345+j*145,965,125,53]);L(label,345+j*145,1018,140,30,16)
page=23
for k,(head,body,labels,iy) in enumerate([
('Общий курс','Определяет основное направление политики.',['Хозяйство','Армия','Богатство','На усмотрение'],151),
('Вложения','Для вложений необходим советник.',['Экономика','Сельское хозяйство','Укрепления','На усмотрение'],343),
('Военные приготовления','Выберите направление подготовки войск.',['Численность','Виды войск','Оснащение','На усмотрение'],535),
('Дипломатия','Курс на завоевания допускает походы против других держав.',['Завоевания','Давление','Равноправие','Покорность'],727)]):
    y=80+k*192;H(head,y,'red',x=345,w=650);B(body,y+35,42)
    for j,label in enumerate(labels):G([347+j*131,iy,465+j*131,iy+59]);L(label,347+j*131,iy+64,125,48,17)
H('Изменить политику - 5 сил',840);I(880);B('Выберите раздел политики, который хотите изменить.',880,35)
for j,label in enumerate(['Труд жителей','Общий курс','Вложения','Армия','Дипломатия']):G([347+j*131,918,465+j*131,976]);L(label,347+j*131,983,125,36,16)
page=24
command_rows([(80,190,'Советник - 10 сил',T[24][0],120),(195,300,'Передать управление - 5 сил',T[24][1],236)])
H('Приказы',315,'band');B(T[24][2],390,55)
command_rows([(455,570,'Поход - 7 сил',T[24][3],455),(575,690,'Перемещение - 6 сил',T[24][4],576),(695,850,'Перевозка - 6 сил',T[24][5],694),(855,1030,'Дипломатия - 8 сил',T[24][6],882)])
page=25
H('Кадры',80,'band');seq(T[25],180,1030,heads=['Наместник - 9 сил','Советник - 9 сил','Полководец - 7 сил','Принц - 6 сил','Брак - 6 сил'],icons=[230,346,614,842,958])
page=26
H('Ордо',80);I(120);B(T[26][0],125,245)
H('Военные команды',395,'band');B(T[26][1],470,65)
command_rows([(550,665,'Поход - 8 сил',T[26][2],478),(680,800,'Перемещение - 7 сил',T[26][3],595)])
B('\n\n'.join(T[26][4:]),810,220)
page=27
command_rows([(80,210,'Перевозка - 6 сил',T[27][0],120),(220,435,'Набор - 6 сил',T[27][1],235),(445,540,'Обучение - 7 сил',T[27][2],466),(550,680,'Роспуск - 8 сил',T[27][3],580)])
H('Хозяйство',695,'band');B(T[27][4],765,55)
command_rows([(825,930,'Распределение жителей - 10 сил',T[27][5],810),(935,1040,'Раздача - 11 сил',T[27][6],925)])
page=28
H('Чрезвычайный сбор - 14 сил',80);I(120);B(T[28][0],125,135)
H('Дипломатия',285,'band');B(T[28][1],360,95)
seq(T[28][2:],475,1030,['Подчинение - 10 сил','Дань - 9 сил','Союз - 8 сил'],[348,658,925])
page=29
H('Купцы',80,'band');B(T[29][0],160,65)
G([475,245,702,357]);L('Уйгурские / мусульманские',345,370,650,28,18);L('Китайские / венецианские',345,402,650,28,18)
B(T[29][1].split('В монгольской')[1].join(['В монгольской','']),440,115)
command_rows([(575,725,'Продать - 6 сил',T[29][2],499),(740,850,'Купить - 6 сил',T[29][3],766),(865,1030,'Наём - 6 сил',T[29][4],879)])
page=30
H('Информация',80,'band');B(T[30][0],160,55);H('Своя провинция - бесплатно',235)
for j,p in enumerate(T[30][2:]):I([310,388,541,617,694,770,847][j],305+j*100);B(p,305+j*100,85)
H('Другая провинция - 2 силы',1010)
page=31
seq(T[31],80,1030,['Другая провинция','Список владений - бесплатно','Полководцы - бесплатно','Купцы - бесплатно','Характеристики войск - бесплатно'],[80,501,696,814,930])
page=32
H('Кадры: посещение супруги',80,'band');I(155);B(T[32][0],155,250)
put('annotated_screen',file='harem-clean-deeds-597.png',box=[120,440,370,285],marks=[(1,38,45),(2,95,81),(3,55,153),(4,188,135),(5,216,182)]);B(T[32][1],440,190,x=530,w=470)
B(T[32][2],740,170);H('Лесть',930);B(T[32][3],975,60)
page=33
seq(T[33],80,1030,['Образ','Любовь','Дары','Совет','Уйти'])
page=34
H('Провинции, персонажи и войска',80,'ribbon');H('Провинция',190,'band')
S('qa-province-only/s0-cold.png',[120,295,400,280]);B(T[34][0],280,290,x=555,w=450)
seq(T[34][1:],600,1030,['Золото: 0-9999','Продовольствие: 0-9999','Население: 0-9999'],[554,709,861])
page=35
seq(T[35][:3],80,550,['Экономика: 0-200','Сельское хозяйство: 0-200','Лояльность: 0-100%'],[122,238,354])
H('Культура',565);B(T[35][3],610,90)
for j,name in enumerate(['Монголия','Внутренняя Азия','Индия','Япония','Западная Европа','Восточная Европа','Исламский мир','Китай']):
    col=j%4;row=j//4;G([350+col*161,650+row*152,500+col*161,746+row*152],[345+col*164,715+row*105,155,85]);L(name,345+col*164,802+row*105,155,35,15)
H('Климат',950);B(T[35][4],990,50)
page=36
B(T[36][0],75,135);B(T[36][1],230,140)
seq(T[36][2:5],395,795,['Земледелие: 0-100%','Животноводство: 0-100%','Местные промыслы: 0-100%'],[470,580,690])
for j,label in enumerate(['Меха','Шёлк','Камни','Драгметаллы','Лекарства','Дерево','Фарфор','Стекло','Ткани','Пряности']):
    col=j%5;row=j//5;G([325+col*132,805+row*116,441+col*132,863+row*116],[345+col*130,815+row*112,115,57]);L(label,345+col*130,875+row*112,125,35,16)
page=37
seq(T[37][:5],80,710,['Города: 0-100%','Укрепления: 0-100%','Отряды: 0-20','Оснащение: 0-100%','Обучение: 0-100%'],[122,238,354,470,582])
H('Персонажи',735,'band');B(T[37][5],815,160)
page=38
H('Правящая семья и родственники',80);B(T[38][0],130,100)
Q('Правитель и супруга\n↓\nСын-полководец: правящая семья\nДочь + полководец: родственник',210,260,370,260)
Q('После наследования\nНовый правитель\nЕго сыновья: правящая семья\nПрежняя семья: родственники',620,260,370,260)
B(T[38][1],545,140);seq(T[38][2:],710,1035,['Политика: A-E','Война: A-E','Лидер: A-E'])
page=39
seq(T[39][:3],80,570,['Хариз: A-E','Здрав: 0-15','Возраст'])
H('Положение',585);B(T[39][3],630,75)
for j,label in enumerate(['Правитель','Наместник','Советник','Полководец','Свободный']):G([349+j*94,538,423+j*94,612],[345+j*130,720,74,74]);L(label,325+j*130,797,125,35,16)
H('Войска',845,'band');B(T[39][4],925,110)
page=40
seq(T[40][:6],70,555,['Боевой дух: число','Подвижность: число','Ближняя атака: A-E','Натиск: A-E','Дальняя атака: A-E','Защита: A-E'])
H('Виды отрядов',570,'band');B(T[40][6],645,50)
for j,p in enumerate(T[40][7:]):G([112,690+j*76,308,754+j*76],[115,710+j*77,196,64]);B(p,710+j*77,70)
page=41
for j,p in enumerate(T[41]):
    y=80+j*77;name,body=p.split(' — ',1)
    G([112,80+j*76.7,308,142+j*76.7],[115,y,193,62]);H(name,y,'red',x=345,w=655);B(body,y+33,44)
page=42
H('Походы и сражения',80,'ribbon');B(T[42][0],185,130)
H('Условия победы',340,'band');B('\n\n'.join(T[42][1:]),420,255)
H('Подготовка войны',705,'band');B(T[43][0],790,240)
page=43
S('qa-battle-wave-deployment.png',[120,95,300,225]);B('\n\n'.join(T[43][1:4]),80,460,x=460,w=540)
B('\n\n'.join(T[43][4:]),580,420)
page=44
H('Ход войны',80,'band');seq(T[44],175,1030,['1. Размещение легионов','2. Начальные позиции','3. Походные команды и сражения','4. Победа и послевоенные решения'])
page=45
H('Походная карта',80,'band');B(T[45][0],165,265)
put('annotated_screen',file='manual-march-next.png',box=[120,455,350,306.25],marks=[(1,75,15),(2,168,15),(3,216,15),(4,153,119),(5,168,65),(6,119,209)])
B(T[45][1],450,290,x=555,w=445);H('Погода',775);B(T[45][2],820,115)
for j,label in enumerate(['Ясно','Облачно','Дождь','Снег','Метель','Жара','Шторм','Буря']):G([350+j*75,916,408+j*75,973],[345+j*80,952,56,52]);L(label,337+j*80,1008,75,30,14)
page=46
H('Походные команды',80,'band');B(T[46][0],160,80);seq(T[46][1:],265,1030,['Приказы легионам','Марш','Преследование','Атака','Засада'])
page=47
seq(T[47],80,850,['Снабжение','Отступление','Самостоятельные действия','Переформирование'])
H('Переговоры',875);B(T[48][0]+' '+T[48][1],920,110)
page=48
seq([T[48][2],T[48][3],'\n'.join(T[48][4:])],80,1030,['Потребовать капитуляции','Потребовать перемирия','Информация'])
page=49
H('Тактическое сражение',80,'band');B('\n\n'.join(T[49][:2]),165,290)
put('annotated_screen',file='manual-tactical-screen.png',box=[120,480,370,323.75],marks=[(1,174,15),(2,103,32),(3,146,32),(4,188,32),(5,32,156),(6,224,91),(7,110,208)]);B(T[49][2],480,300,x=550,w=450)
H('Условия победы',830);B(T[49][3],880,140)
page=50
H('Замешательство',80);G([115,115,255,260]);B(T[50][0],125,190)
H('Тактические команды',345,'band');B(T[50][1],425,150)
seq(T[50][2:6],600,1030,['Движение - 2 или 3 очка','Атака','Ближний бой - 3 очка','Обстрел - 3 очка'])
page=51
H('Натиск - 5 очков',80,'red',x=345,w=650);B(T[50][6],125,100)
H('Командование',250);B(T[51][0],295,65)
seq(T[51][1:],380,1030,['Возглавить отряд - 4 очка','Восстановить порядок - 4 очка','Передать управление - бесплатно','Сведения об отряде','Сведения о командире'])
page=52
H('После войны',80,'band');seq(T[52],180,1030,['Пленники','Судьба пленников','Супруги и одарённые люди','Новый правитель и наместник'])
page=53
H('События',80,'ribbon');H('Сезонные события',190,'band');B(T[53][0],270,55)
seq(T[53][1:],350,825,['Налоги','Урожай и товары','Жалованье','Содержание жителей','Смерть'])
H('Случайные события',850,'band');B(T[54][0],930,100)
page=54
B(T[54][1],75,100)
for j,p in enumerate(T[54][2:]):G([95,[158,271,425,540,654,811][j],240,[258,372,526,641,756,914][j]],[120,190+j*138,145,100]);H(p.split(' — ')[0],190+j*138,'red',x=345,w=650);B(p,228+j*138,92)
for i in range(55,60):
    page=i;name=titles[i].split('. ',1)[1].split(' — ')[0];H(name,80,'ribbon')
    L(f'Сценарий {i-54} • '+['1184','1180','1206','1271','1185'][i-55],700,177,300,28,18)
    S('manual-strategy-screen.png' if i==55 else f'manual-scenario-{i-55}.png',[120,210,380,332.5])
    paras=[p for p in T[i] if not p.startswith(('Редакторское примечание:','Примечание:'))]
    B('\n\n'.join(paras[:2]),205,355,x=565,w=440);B('\n\n'.join(paras[2:]),580,450)
page=60
H('Державы и правители',80,'ribbon');B(T[60][0],180,55,x=120,w=880)
for k,(x,y,w,h) in enumerate([(115,260,420,210),(115,495,420,220),(115,740,420,290),(570,260,430,330),(570,615,430,340)]):
    put('table',s=T[60][k+1],box=[x,y,w,h])
L('Какого правителя выберете?',590,980,390,45,22)
page=61
H('Музыка игры',80,'ribbon');H('Музыкальный мир игры',190,'band');B('\n\n'.join(T[61][:2]),270,440)
H('О композиторе',740,'band');B(T[61][2],820,210)
page=62
L('Обслуживание и выходные данные',130,80,850,65,30)
B('\n\n'.join(T[62][:3]),200,600,x=135,w=830);B('\n\n'.join(T[62][3:]),850,180,x=135,w=830)
page=63
put('backcover')

# Restore compact illustrated spreads. Captions are a separate type, not body text.
def R(s,x,y,w,h,size=17):put('text',s=s,box=[x,y,w,h],role='caption',size=size,align=0)
page=22;plans[page]=[]
H('Расход сил',80);B(T[22][0],125,240);G([95,175,288,370],[120,175,150,180])
H('Политика',390,'band');B(T[22][1],465,65);H('Новая политика - 8 сил',540);I(534,585);B(T[22][2],585,130)
put('annotated_screen',file='manual-policy-native.png',crop=[8,143,247,216],box=[120,730,540,165],marks=[(1,36,20),(2,36,38),(3,36,55),(4,122,20),(5,122,38),(6,122,55),(7,182,20),(8,182,38)]);R(T[22][3],700,730,300,175,16)
B(T[22][4],920,55)
for j,label in enumerate(['Земледелие','Скот','Промыслы','Города']):G([325+j*132,916,440+j*132,971],[345+j*145,975,115,45]);L(label,345+j*145,1020,140,20,14)
page=32
# Make space for the original five compliment buttons and their Russian captions.
plans[page]=[o for o in plans[page] if not(o['kind']=='heading' and o['y']==930) and not(o['kind']=='text' and o['box'][1]>=930)]
H('Лесть',890);B('Похвалите достоинства супруги.',930,30)
for j,label in enumerate(['Красота','Ум','Сила духа','Рассудительность','Все достоинства']):G([325+j*132,916,440+j*132,973],[345+j*130,965,113,48]);L(label,338+j*130,1015,130,24,13)
page=33;plans[page]=[]
H('Образ',80);B(T[33][0],125,100)
for j,label in enumerate(['О подвигах','О лидерстве','О политике','Обаяние','Моя сила']):G([350+j*131,158,465+j*131,215],[345+j*130,240,115,57]);L(label,340+j*130,302,130,40,16)
G([350,270,465,326],[345,350,115,56]);L('Слабость',345,409,125,28,16)
H('Любовь',455);B(T[33][1],500,85)
for j,label in enumerate(['Взгляд в глаза','Нежность','Непринуждённость','Настойчивость']):G([350+j*131,466,465+j*131,522],[345+j*160,600,115,56]);L(label,330+j*160,663,155,40,16)
command_rows([(720,850,'Дары',T[33][2],None),(865,950,'Совет',T[33][3],None),(965,1040,'Уйти',T[33][4],None)])
page=34;plans[page]=[]
H('Провинции, персонажи и войска',80,'ribbon');H('Провинция',190,'band')
put('annotated_screen',file='manual-strategy-screen.png',crop=[8,143,247,216],box=[120,295,565,173],marks=[(1,28,23),(2,28,40),(3,28,57),(4,134,23),(5,134,40),(6,134,57),(7,202,35),(8,202,60)]);R(T[34][0],730,295,265,185,16)
seq(T[34][1:],510,1030,['Золото: 0-9999','Продовольствие: 0-9999','Население: 0-9999'],[554,709,861])
page=36
plans[page]=[o for o in plans[page] if not(o['kind']=='text' and o['box'][1]==230)]
put('annotated_screen',file='manual-policy-panel.png',crop=[8,143,247,216],box=[120,220,565,173],marks=[(1,36,20),(2,36,38),(3,36,55),(4,122,20),(5,122,38),(6,182,20),(7,182,38),(8,182,55)]);R(T[36][1],730,220,265,175,16)
page=37;plans[page]=[]
seq(T[37][:5],80,625,['Города: 0-100%','Укрепления: 0-100%','Отряды: 0-20','Оснащение: 0-100%','Обучение: 0-100%'],[122,238,354,470,582])
H('Персонажи',650,'band');B(T[37][5],730,115)
put('annotated_screen',file='manual-person-card.png',crop=[8,6,248,83],box=[120,860,540,173],marks=[(1,8,58),(2,180,38)]);R('1 - родство\n2 - способности персонажа',720,860,275,160)
page=39;plans[page]=[]
seq(T[39][:3],80,450,['Хариз: A-E','Здрав: 0-15','Возраст']);H('Положение',465);B(T[39][3],510,65)
for j,label in enumerate(['Правитель','Наместник','Советник','Полководец','Свободный']):G([349+j*94,538,423+j*94,612],[345+j*130,590,74,74]);L(label,325+j*130,670,125,35,16)
H('Войска',715,'band');B('Характеристики отрядов доступны в информационном меню.',790,45)
put('annotated_screen',file='manual-unit-card.png',crop=[111,47,240,123],box=[120,840,300,177],marks=[(1,66,17),(2,76,48),(3,76,65),(4,111,17),(5,111,33),(6,111,49),(7,111,65)]);R(T[39][4],470,840,525,190,16)
page=44
S('manual-war-deploy.png',[120,220,143,125])

page=24
for j,label in enumerate(['Золото','Продовольствие']):G([327+j*132,727,442+j*132,784],[350+j*160,785,105,50]);L(label,335+j*160,838,145,22,14)
for j,label in enumerate(['Подчинение','Дань']):G([327+j*132,919,442+j*132,976],[350+j*160,970,105,50]);L(label,335+j*160,1022,145,22,14)
page=25
for head,sy,labels in [('Советник - 9 сил',468,['Назначить','Снять']),('Полководец - 7 сил',697,['Нанять','Уволить'])]:
    y=next(o['y'] for o in plans[page] if o['kind']=='heading' and o['s']==head)
    for j,label in enumerate(labels):G([350+j*132,sy,465+j*132,sy+57],[115+j*105,y+96,90,32]);L(label,110+j*105,y+130,100,18,12)
page=26
G([142,694,255,750],[120,820,120,60]);G([142,883,255,939],[120,950,120,60])
page=29
plans[page]=[o for o in plans[page] if not(o['kind']=='crop' and o['target'] and o['target'][1]==615)]
put('annotated_screen',file='manual-goods-native.png',crop=[8,143,247,216],box=[115,620,215,65.67],marks=[(1,29,10),(2,62,10)])

page=38
plans[page]=[o for o in plans[page] if o['kind']!='diagram'];put('family_tree',box=[150,255,845,275])
page=43;plans[page]=[]
B('\n\n'.join(T[43][1:4]),80,490,x=460,w=540)
B('\n\n'.join(T[43][4:]),700,320,x=460,w=540)
for j,file in enumerate(['manual-legion-setup.png','manual-legion-summary.png','manual-war-count.png']):S(file,[120,[90,440,720][j],310,271.25])

# ROM-verified unit reference tables and illustrated war sequence.
page=40;plans[page]=[]
for j,head in enumerate(['Боевой дух: число','Подвижность: число','Ближняя атака: A-E','Натиск: A-E','Дальняя атака: A-E','Защита: A-E']):
    xx=115+(j//3)*450;yy=70+(j%3)*130
    H(head,yy,x=xx,w=430);B(T[40][j],yy+38,88,x=xx,w=430)
H('Виды отрядов',480,'band')
R('Базовые характеристики из игры. A - лучшая оценка, E - худшая; * - нет стрельбы. Дух и подвижность в бою могут меняться.',120,555,880,55,18)
put('unit_table',ids=list(range(4)),box=[115,625,880,405])
page=41;plans[page]=[]
H('Виды отрядов: продолжение',80,'band')
R('Дух - боевой дух; Действ - подвижность; Ближ - ближняя атака; Натиск - атака с разгона; Дальн - обстрел; Защ - защита.',120,155,880,65,18)
put('unit_table',ids=list(range(4,16)),box=[115,230,880,800])
page=44;plans[page]=[]
H('Ход войны',80,'band')
for j,(head,file) in enumerate(zip(['1. Размещение легионов','2. Начальные позиции','3. Походные команды и сражения','4. Возвращение к управлению'],['manual-war-deploy.png','qa-battle-wave-deployment.png','manual-tactical-screen.png','manual-strategy-screen.png'])):
    yy=165+j*215
    H(head,yy);S(file,[120,yy+40,200,175]);B(T[44][j],yy+40,170,x=350,w=645)
page=53;plans[page]=[]
H('События',80,'ribbon');H('Сезонные события',190,'band');B(T[53][0],265,45,x=120,w=880)
for j,head in enumerate(['Налоги','Урожай и товары','Жалованье','Содержание жителей','Смерть']):
    yy=330+j*100
    H(head,yy);B(T[53][j+1],yy+36,62,x=120,w=880)
H('Случайные события',850,'band');B(T[54][0],925,105,x=120,w=880)
page=60
for op in plans[page]:
    if op['kind']=='table' and op['box'][0]==570 and op['box'][1]==615:op['box'][3]=260
plans[page]=[op for op in plans[page] if op.get('s')!='Какого правителя выберете?']
G([551,866,673,1010],[575,885,106,125],source=60)
Q('Какого правителя\nвыберете?',700,905,285,90)

# Legends use a smaller fixed caption font while all surrounding prose stays uniform.
for pn in [21,32]:
    legend=T[pn][1 if pn!=49 else 2]
    for o in plans[pn]:
        if o['kind']=='text' and o['s']==legend:o.update(role='caption',size=20 if pn==21 else 16,align=0)

for pn,ops in plans.items():
    for op in ops:
        assert op['kind'] not in {'panel','setup_screen','localized_battle'}
        if op['kind']=='annotated_screen':
            numbers=[m[0] for m in op['marks']]
            assert sorted(numbers)==list(range(1,len(numbers)+1)),(pn,numbers)

# Painting / validation.
def para(s,size,role='body',align=0,color='#111111'):
    s=re.sub('[\u2010-\u2015]','-',s)
    return Paragraph(escape(s).replace('\n','<br/>'),ParagraphStyle('p',fontName='Body' if role in ['body','caption'] else 'Bold',fontSize=size,leading=size*1.26,textColor=color,alignment=align))
selected=[int(x) for x in sys.argv[1].split(',')] if len(sys.argv)>1 else list(range(64))
OUTPUT=OUT/('Genchou-Hishi-Mega-CD-Manual-RU.pdf' if len(selected)==64 else 'manual-layout-check.pdf')
C=canvas.Canvas(str(OUTPUT),pagesize=(600,600));C.setTitle('Серый волк и белая лань - Тайная история Юань. Руководство Mega-CD');C.setAuthor('KOEI / русский перевод')
report=[]
def img(im,box):x,y,w,h=box;C.drawImage(ImageReader(im),x,1100-y-h,w,h)
def rect(box,color,stroke=None):
    x,y,w,h=box;C.setFillColor(color);C.setStrokeColor(stroke or color);C.rect(x,1100-y-h,w,h,fill=1,stroke=bool(stroke))
def drawtext(s,box,size,role='body',align=0,color='#111111'):
    x,y,w,h=box;p=para(s,size,role,align,color);_,hh=p.wrap(w,h)
    if hh>h+.1:raise ValueError((page,role,s[:80],size,box,hh))
    p.drawOn(C,x,1100-y-hh)
def crop(im,b):return im.crop(tuple(round(v*2) for v in b))
for page in selected:
    ops=plans[page];main=[o for o in ops if o['kind']=='text' and o['role']=='body']
    fs=23
    while fs>=14:
        if all(para(o['s'],fs).wrap(o['box'][2],o['box'][3])[1]<=o['box'][3] for o in main):break
        fs-=.25
    if fs<14:raise ValueError(('Page body does not fit',page))
    C.saveState();C.scale(600/1100,600/1100)
    if 3<=page<=61:
        background=src(page).copy();ImageDraw.Draw(background).rectangle((156,120,2086,2092),fill='white');img(background,[0,0,1100,1100])
        title,color,pale=chapter(page);sx=55 if page%2 else 997
        rect([sx,550,45,490],pale,stroke='#797466')
        rect([sx,490,45,60],'white')
        drawtext(str(page-1),[sx,505,45,42],28,'label',1)
        C.saveState();C.translate(sx+22,530);C.rotate(-90);C.setFont('Bold',19);C.setFillColor('#111111');C.drawString(0,-7,title);C.restoreState()
        C.setStrokeColor('#68665d');C.setLineWidth(.75);C.line(105 if page%2 else 78,1040,1022 if page%2 else 997,1040);C.line(105 if page%2 else 78,60,1022 if page%2 else 997,60)
    C.bookmarkPage(f'page{page}');C.addOutlineEntry(titles[page],f'page{page}')
    for op in ops:
        k=op['kind']
        if k=='text':drawtext(op['s'],op['box'],fs if op['role']=='body' else op['size'],op['role'],op.get('align',0))
        elif k=='crop':
            b=op['box'];img(crop(src(op['source']),b),op['target'] or [b[0],b[1],b[2]-b[0],b[3]-b[1]])
        elif k=='screen':
            im=Image.open(ROOT/'analysis'/op['file']).convert('RGB');img(im,op['box'])
        elif k=='annotated_screen':
            im=Image.open(ROOT/'analysis'/op['file']).convert('RGB')
            if 'crop' in op:im=im.crop(op['crop'])
            x,y,w,h=op['box'];img(im,op['box'])
            # Compact numbered badges beside the referenced interface elements.
            for number,px,py in op['marks']:
                cx=x+px/im.width*w;cy=y+py/im.height*h
                C.setStrokeColor('#222222');C.setLineWidth(1)
                C.setFillColor('white');C.circle(cx,1100-cy,10,fill=1,stroke=1)
                drawtext(str(number),[cx-9,cy-9,18,22],14,'label',1)
        elif k=='heading':
            x,y,w=op['x'],op['y'],op['w'];sty=op['style'];color=chapter(page)[1]
            if sty=='gray':
                im=crop(src(6),[480,80,680,105]);img(im,[x,y,w,32]);drawtext(op['s'],[x+8,y+3,w-16,28],20,'label')
            elif sty=='red':
                C.setFillColor('#a73436');path=C.beginPath();path.moveTo(x,1100-y-14);path.lineTo(x+9,1100-y-5);path.lineTo(x+18,1100-y-14);path.lineTo(x+9,1100-y-23);path.close();C.drawPath(path,fill=1,stroke=0)
                drawtext(op['s'],[x+27,y,w-27,32],23,'label',color='#a73436')
            elif sty=='band':
                rect([x,y,w,60],'#eceee9',stroke=color)
                for dx in [0,12,28,w-40,w-24,w-10]:rect([x+dx,y,8,60],color)
                drawtext(op['s'],[x+55,y+10,w-110,40],27,'label',1,color)
            else:
                # Original irregular ribbon outline; remove its old lettering with a clean texture.
                ribbon=crop(src(55),[112,80,1006,175]).resize((894,95))
                a=ImageDraw.Draw(ribbon);a.rectangle((28,18,865,78),fill='#812728')
                ar=np.asarray(ribbon).copy();mask=(ar[:,:,0]>ar[:,:,1]*1.25)&(ar[:,:,0]>ar[:,:,2]*1.15)
                rgb=np.array([int(color[q:q+2],16) for q in (1,3,5)]);shade=ar[:,:,0].astype(float)/129
                ar[mask]=np.clip(shade[mask,None]*rgb,0,255).astype('uint8');ribbon=Image.fromarray(ar)
                img(ribbon,[x,y,w,95]);drawtext(op['s'],[x+35,y+22,w-70,53],30,'label',1,'#fff8df')
        elif k=='state_relationships':
            # Match the original manual: state, capital/dependency, family and service links.
            rect([155,430,855,285],'#fafbf3',stroke='#555c52')
            rect([170,480,520,220],'#c9dfe0',stroke='#555c52')
            rect([710,480,285,220],'#e9e8e2',stroke='#555c52')
            rect([515,416,135,29],'white')
            drawtext('Держава',[520,418,125,30],22,'label',1)
            drawtext('Столичная провинция',[180,450,500,30],21,'label',1)
            drawtext('Подчинённая провинция',[715,450,275,30],19,'label',1)
            def link(points,dotted=False):
                C.setStrokeColor('#424b48');C.setLineWidth(1.3)
                C.setDash(3,3) if dotted else C.setDash()
                for (ax,ay),(bx,by) in zip(points,points[1:]):C.line(ax,1100-ay,bx,1100-by)
                C.setDash()
            def node(label,x,y,w):
                rect([x,y,w,34],'#ffffff',stroke='#424b48')
                drawtext(label,[x+4,y+5,w-8,25],18,'label',1)
            def heart(x,y):
                C.setFillColor('#d83936');C.setStrokeColor('#d83936')
                p=C.beginPath();p.moveTo(x,1100-y-13)
                p.curveTo(x-31,1100-y+8,x-14,1100-y+24,x,1100-y+10)
                p.curveTo(x+14,1100-y+24,x+31,1100-y+8,x,1100-y-13)
                C.drawPath(p,fill=1,stroke=0)
            link([(340,517),(535,517)])
            link([(265,534),(265,635)],True)
            link([(600,534),(600,550),(520,550),(520,565)])
            link([(600,550),(600,635)])
            link([(455,594),(340,640)])
            C.setFillColor('#424b48');p=C.beginPath();p.moveTo(340,460);p.lineTo(354,461);p.lineTo(349,471);p.close();C.drawPath(p,fill=1,stroke=0)
            link([(340,652),(535,652)])
            link([(850,534),(850,635)],True)
            node('Правитель',190,500,150);node('Супруга',535,500,135)
            node('Советник',190,565,180);node('Принц',455,565,130)
            node('Полководец',190,635,150);node('Принцесса',535,635,140)
            node('Наместник',775,500,150);node('Советник',760,635,180)
            heart(430,517);heart(430,652)
        elif k=='diagram':
            rect(op['box'],'#eef1e7',stroke=chapter(page)[1]);x,y,w,h=op['box'];drawtext(op['s'],[x+12,y+20,w-24,h-30],21,'label',1)
        elif k=='frame':rect(op['box'],op.get('fill','white'),op['color'])
        elif k=='table':
            x,y,w,h=op['box'];lines=op['s'].splitlines();drawtext(lines[0],[x,y,w,30],21,'label',color='#a73436');rh=(h-40)/(len(lines)-1)
            for j,line in enumerate(lines[1:]):rect([x,y+40+j*rh,w,rh],'#b3ccc0' if j%2==0 else '#dde5de');drawtext(line,[x+7,y+44+j*rh,w-14,rh-6],16,'body')
        elif k=='unit_table':
            data=json.loads((ROOT/'docs/manuals/unit-stats-rom.json').read_text('utf8'))['rows']
            x,y,w,h=op['box'];widths=[105,180,45,65,65,65,65,65,225];head=48;rh=(h-head)/len(op['ids'])
            labels=['Вид','Название','Дух','Действ','Ближ','Натиск','Дальн','Защ','Где набирают']
            xx=x
            for cw,label in zip(widths,labels):
                rect([xx,y,cw,head],'#d3d4e7',stroke='#8b8c9e');drawtext(label,[xx+2,y+6,cw-4,38],13,'label',1);xx+=cw
            for j,i in enumerate(op['ids']):
                row=data[i];yy=y+head+j*rh;xx=x
                for cw in widths:rect([xx,yy,cw,rh],'#f3f3f8' if j%2==0 else '#e4e5ef',stroke='#aaaabb');xx+=cw
                if i<4:box=[112,690+i*76,308,754+i*76];sp=40
                else:box=[112,80+(i-4)*76.7,308,142+(i-4)*76.7];sp=41
                img(crop(src(sp),box),[x+5,yy+(rh-32)/2,95,32])
                cells=[row['name'],str(row['morale']),str(row['mobility']),row['melee'],row['charge'],row['ranged'],row['defence'],row['culture']]
                xx=x+widths[0]
                for col,(cw,value) in enumerate(zip(widths[1:],cells)):
                    sz=16 if col in [0,7] else 19
                    drawtext(value,[xx+5,yy+7,cw-10,rh-10],sz,'body' if col in [0,7] else 'label',0 if col in [0,7] else 1);xx+=cw
        elif k=='army_diagram':
            x,y,w,h=op['box']
            for j in range(4):
                C.setFillColor(['#a9a9c8','#babbd3','#d3d4e7','#e4f6f5'][j]);C.setStrokeColor('#555568');C.ellipse(x+j*82,1100-y-h+j*28,x+w-j*16,1100-y-j*28,fill=1,stroke=1)
            # At the horizontal centre the first three rings are 82 units wide.
            # Centre each label within its own ring; soldier belongs to the core.
            for j,label in enumerate(['Армия','Легион','Отряд','Солдат']):
                left=x+j*82
                width=82 if j<3 else w-3*82-3*16
                assert pdfmetrics.stringWidth(label,'Bold',18) < width-8
                drawtext(label,[left+4,y+h/2-11,width-8,28],18,'label',1)
        elif k=='family_tree':
            x,y,w,h=op['box'];rect(op['box'],'#fafafa',stroke='#7774a3')
            drawtext('Правящая семья и родство',[x+15,y+10,w-30,35],23,'label')
            for xx in [x+20,x+445]:
                C.setStrokeColor('#666666');C.setLineWidth(1.2)
                C.line(xx+170,1100-y-92,xx+170,1100-y-145);C.line(xx+60,1100-y-145,xx+310,1100-y-145)
                for dx in [60,310]:C.line(xx+dx,1100-y-145,xx+dx,1100-y-162)
            for title,box,color in [
                ('Правитель и супруга',[x+75,y+57,280,42],'#e1e4e5'),('Сын: семья',[x+20,y+165,170,45],'#c1b6d8'),('Муж дочери: родня',[x+235,y+165,170,45],'#bbd2af'),
                ('Новый правитель',[x+500,y+57,280,42],'#e1e4e5'),('Его сын: семья',[x+445,y+165,170,45],'#c1b6d8'),('Прежняя семья: родня',[x+660,y+165,170,45],'#bbd2af')]:rect(box,color);drawtext(title,[box[0]+4,box[1]+7,box[2]-8,box[3]-9],14,'label',1)
            drawtext('Наследование престола меняет родственные статусы.',[x+20,y+230,w-40,30],18,'caption')
        elif k=='battle_pair':
            for xx,file,label in [(120,'manual-march-next.png','Поход: команды легионам'),(590,'manual-tactical-screen.png','Сражение: команды отрядам')]:
                im=Image.open(ROOT/'analysis'/file).convert('RGB');img(im,[xx,90,350,306.25])
                drawtext(label,[xx-5,401,360,30],19,'label',1)
        elif k=='main_menu':
            x,y,w,h=op['box'];im=Image.open(ROOT/'analysis/manual-main-menu.png').convert('RGB').crop((88,127,247,219));img(im,[x,y,w,w*92/159])
        elif k=='cover':
            img(src(0),[0,0,1100,1100]);rect([880,125,220,590],'#070909')
            C.saveState();C.translate(980,935);C.rotate(-90);C.setFont('Bold',36);C.setFillColor('#d9c38b');C.drawString(0,0,'ТАЙНАЯ ИСТОРИЯ ЮАНЬ');C.restoreState()
            rect([585,890,515,210],'#ceb67b');drawtext('СЕРЫЙ ВОЛК\nИ БЕЛАЯ ЛАНЬ',[610,905,465,120],40,'label',1);drawtext('Руководство пользователя',[615,1040,455,40],24,'label',1)
            rect([278,1015,305,55],'black')
        elif k=='backcover':
            img(src(63),[0,0,1100,1100]);rect([180,800,920,300],'#050707');drawtext('Серый волк и белая лань\nТайная история Юань',[200,820,840,75],26,'label',color='white');drawtext('\n'.join(T[63][1:]),[200,920,850,155],15,'body',color='white')
    report.append({'source_page':page,'printed_page':page-1,'body_font':fs,'body_blocks':len(main),'elements':len(ops)})
    C.restoreState();C.showPage()
C.save()
r=PdfReader(OUTPUT);assert len(r.pages)==len(selected)
assert not re.search(r'[\u3040-\u30ff\u3400-\u9fff]',''.join(p.extract_text() for p in r.pages))
(OUT/('manual-full-layout-validation.json' if len(selected)==64 else 'manual-layout-check.json')).write_text(json.dumps({'status':'render_review_pending','pages':report,'sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),'utf8')
print(OUTPUT)
