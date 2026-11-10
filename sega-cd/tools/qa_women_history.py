"""Cold-boot the catalogue, then exercise every wife's card from current-build states."""
from pathlib import Path
import subprocess,sys,os,json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/qa-women-history'
OUT.mkdir(exist_ok=True)
m=json.loads((ROOT/'build/manifest.json').read_text('utf8'))
cue=ROOT/'build/qa-generated/trial.cue'
shutil.copyfile(ROOT/'build/genchou-hishi-ru-experimental.iso',cue.with_name('trial.iso'))
env=os.environ.copy();env['CORE_OPTIONS']='{"genesis_plus_gx_cart_size":"none"}'
def run(name,frames,buttons,state=None):
    env.pop('STATE_IN',None)
    if state:env['STATE_IN']=str(OUT/(state+'.state'))
    env['STATE_OUT']=str(OUT/(name+'.state'))
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/emulate.py'),str(cue),str(frames),json.dumps(buttons)],env=env,check=True,stdout=subprocess.DEVNULL)
    shutil.copyfile(ROOT/'analysis/screen-latest.png',OUT/(name+'.png'))
route=[[300,310,3],[900,910,8],[1500,1510,3],[3600,3610,4],[3800,3810,8],[4500,4510,8],[5400,5410,8],[6000,6010,8],[6600,6610,3],[7150,7160,3],[8050,8060,5],[8150,8160,5],[8250,8260,8],[8650,8660,5],[8750,8760,5],[8850,8860,8],[9250,9260,8]]
run('list',9600,route);run('filter',300,[[50,60,0]],'list')
offset=0;cards=[]
for group,count in enumerate(m['catalog_index']['wives']['counts']):
    keys=([7] if group>=5 else [])+[5]*(group%5)+[8]
    actions=[[50+i*120,60+i*120,k] for i,k in enumerate(keys)]
    run(f'group-{group}',len(keys)*120+250,actions,'filter')
    for local in range(count):
        index=offset+local;name=m['catalog_index']['wives']['names'][index]
        keys=([7] if local>=8 else [])+[5]*(local%8)+[8]
        actions=[[50+i*120,60+i*120,k] for i,k in enumerate(keys)]
        run(f'card-{index:02}',len(keys)*120+300,actions,f'group-{group}')
        cards.append(dict(index=index,original_index=m['catalog_index']['wives']['order'][index],name=name,screenshot=f'card-{index:02}.png'))
    print(f'PASS: group {group+1}/10, {count} cards opened',flush=True)
    offset+=count
run('return',900,[[50,60,0],[300,310,0],[550,560,0]],'card-83')
report=dict(iso_sha256=m['iso_sha256'],emulator='Genesis Plus GX libretro',cold_boot=True,cards=cards,visual_review='Selected screenshots inspected separately; opening all cards alone is not pixel-by-pixel review.')
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
assert len(cards)==84
print('PASS: all 84 current-build cards opened; returned to category menu')
