"""Compare original/patched UI outside the translated text rectangle."""
from pathlib import Path
import json, subprocess, sys, shutil, os
os.environ["CORE_OPTIONS"]=json.dumps({"genesis_plus_gx_cart_size":"none"})
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
sys.path.insert(0,str(PROJECT/'mega-drive/tools'))
from find_title import read_png
inputs=[[300,310,3],[900,910,8],[1500,1510,3],[2100,2110,8]]
sources=[('original',ROOT/'build/playable-original/game.cue'),
         ('russian',ROOT/'build/playable-japanese-audio/game.cue')]
frames=[]
for label,cue in sources:
    # Advance the initial notification in both versions before comparing the dialog.
    sequence=inputs
    subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(cue),'3500',json.dumps(sequence)],check=True,capture_output=True)
    target=ROOT/'analysis'/f'confirmation-{label}.png'
    shutil.copyfile(ROOT/'analysis/screen-latest.png',target)
    frames.append(read_png(target))
w,h,original=frames[0];w2,h2,russian=frames[1]
assert (w,h)==(w2,h2)==(256,224)
inside=outside=buttons=0
for y in range(h):
    for x in range(w):
        offset=(y*w+x)*3
        changed=original[offset:offset+3]!=russian[offset:offset+3]
        if 80<=x<184 and 80<=y<128: inside+=changed
        elif 200<=x<232 and 64<=y<96: buttons+=changed
        else: outside+=changed
assert inside>0, 'Translated screen did not change'
assert buttons>0, 'Russian Yes/No buttons did not change'
assert outside==0, f'{outside} changed pixels outside translated message'
states=[]
for label,extra,frame_count in [('no',[[3600,3610,5]],4000),('return',[[3600,3610,5],[4200,4210,4]],4600)]:
    subprocess.run([sys.executable,str(ROOT/'tools/emulate.py'),str(sources[1][1]),str(frame_count),json.dumps(inputs+extra)],check=True,capture_output=True)
    target=ROOT/'analysis'/f'confirmation-russian-{label}.png'
    shutil.copyfile(ROOT/'analysis/screen-latest.png',target)
    sw,sh,pixels=read_png(target);assert(sw,sh)==(w,h)
    states.append(pixels)
assert states[0]!=russian,'Yes/No selection did not move'
assert states[1]==russian,'Returning to Yes did not restore original pixels'
assert all(russian[(y*w+x)*3:(y*w+x)*3+3]==states[0][(y*w+x)*3:(y*w+x)*3+3]
           for y in range(h) for x in range(w) if not(200<=x<232 and 64<=y<96)), 'Selection affected pixels outside the buttons'
report=dict(frames=3500,inputs=inputs,original_extra_input=[],changed_message_pixels=inside,changed_button_pixels=buttons,changed_outside_pixels=outside,
            bios_sha256=__import__('hashlib').sha256((PROJECT/'.runtime/bios_CD_J.bin').read_bytes()).hexdigest(),
            selection_down_and_up='passed',limitations='One initial memory-confirmation screen; not gameplay coverage.')
(ROOT/'analysis/interface-test.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(f'PASS: {inside} changed dialog pixels, {buttons} changed Yes/No pixels; portrait and outside background unchanged')
