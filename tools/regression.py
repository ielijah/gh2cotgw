"""Emulator regression captures and menu redraw stability check."""
from pathlib import Path
import sys,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from find_title import read_png
from graphics_codec import decode

basic=[[1900,1910,3],[3000,3010,3]]
scenario=basic+[[4100,4110,8]]
choices=scenario+[[5100,5110,8],[5500,5510,8],[6400,6410,8],[7200,7210,8]]
cases=[('intro-ru',1800,[]),('intro-later-ru',4500,[]),('new-game-ru',4000,basic),('scenario-ru',4500,scenario),('scenario-redraw-ru',5000,scenario+[[4600,4605,5],[4800,4805,4]]),('buttons-ru',7800,choices),('title-ru',9000,[])]
cases.append(('buttons-no-ru',8000,choices+[[7900,7905,7]]))
game=choices+[[t,t+10,8] for t in range(8100,15001,600)]
cases += [('self-orders-ru',11500,game),('orders-prompt-ru',12100,game),('commands-ru',13200,[i for i in game if i[0]<=11700]),('action-cost-ru',15200,game)]
for name,frames,inputs in cases:
    subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(ROOT/'build/genghis2-ru-experimental.gen'),str(frames),json.dumps(inputs)],cwd=ROOT,check=True,capture_output=True)
    shutil.copyfile(ROOT/'analysis/screen-genghis2-ru-experimental.png',ROOT/'analysis'/f'{name}.png')
    print(f'Captured {name}: {frames} frames')
w,h,first=read_png(ROOT/'analysis/scenario-ru.png')
w2,h2,again=read_png(ROOT/'analysis/scenario-redraw-ru.png')
assert (w,h)==(w2,h2)==(256,224)
changed=sum(first[(y*w+x)*3:(y*w+x)*3+3]!=again[(y*w+x)*3:(y*w+x)*3+3] for y in range(120,200) for x in range(80,240))
assert changed==0,f'Menu changed after down/up selection: {changed} pixels'
_,_,hud=read_png(ROOT/'analysis/new-game-ru.png')
for name in ('scenario-ru','scenario-redraw-ru','buttons-ru'):
    _,_,frame=read_png(ROOT/'analysis'/f'{name}.png')
    diff=sum(hud[(y*w+x)*3:(y*w+x)*3+3]!=frame[(y*w+x)*3:(y*w+x)*3+3] for y in range(32,48) for x in range(174,238))
    assert diff==0,(name,'Price indicator changed',diff)
# Check actual rendered foreground, not just the palette indices in the ROM.
# Original Yes/No foreground is RGB (238,238,238) in this setup screen.
rom=(ROOT/'build/genghis2-ru-experimental.gen').read_bytes()
for name in ('buttons-ru','buttons-no-ru'):
    w,h,frame=read_png(ROOT/'analysis'/f'{name}.png')
    for resource,left in ((0xb9,176),(0xba,208)):
        table=0xa663c+resource*4
        raw,_=decode(rom[int.from_bytes(rom[table:table+4],'big'):])
        ink=0
        for y in range(16):
            for x in range(32):
                value=(raw[(y//8*4+x//8)*32+y%8*4+x%8//2]>>(4 if x%2==0 else 0))&15
                if value==14:
                    offset=((56+y)*w+left+x)*3
                    assert frame[offset:offset+3]==bytes((238,238,238)),(name,resource,x,y,'Button ink differs from original white')
                    ink+=1
        assert ink>0
subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(ROOT/'rom/original.gen'),'15200',json.dumps(game)],cwd=ROOT,check=True,capture_output=True)
_,_,original=read_png(ROOT/'analysis/screen-original.png')
_,_,translated=read_png(ROOT/'analysis/action-cost-ru.png')
action_diff=sum(original[(y*w+x)*3:(y*w+x)*3+3]!=translated[(y*w+x)*3:(y*w+x)*3+3] for y in range(40,56) for x in range(72,112))
assert action_diff==0,('Action indicator differs from original',action_diff)
report=dict(action_indicator_changed_pixels=action_diff,cases=[dict(name=n,frames=f,inputs=i) for n,f,i in cases],button_ink_rgb=[238,238,238],scenario_redraw_changed_pixels=changed,price_indicator_changed_pixels=0,status='PASS',scope='Launch, intro, menu selection, setup prompts and title; not a full playthrough')
(ROOT/'analysis/regression.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PASS: expanded scenario menu identical after down/up; Price HUD unchanged across menus')
