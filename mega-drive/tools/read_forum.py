from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,re
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.data=[];self.skip=0;self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag in ('p','div','br','tr','hr'):self.data.append('\n')
        if tag=='a':self.links.append(dict(attrs).get('href',''))
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip-=1
        if tag in ('p','div','tr'):self.data.append('\n')
    def handle_data(self,value):
        if not self.skip:self.data.append(value)
def fetch(page):
    url=f'http://chief-net.ru/forum/topic.php?forum=4&topic=35&p={page}'
    raw=urllib.request.urlopen(url,timeout=30).read()
    (ROOT/'analysis'/f'forum-page{page}.html').write_bytes(raw)
    p=Parser();p.feed(raw.decode('cp1251'))
    text='\n'.join(s.strip() for s in ''.join(p.data).splitlines() if s.strip())
    (ROOT/'analysis'/f'forum-page{page}.txt').write_text(text,encoding='utf-8')
    return page,[link for link in p.links if any(k in link.lower() for k in ('.zip','.7z','.rar','.tbl','attachment','file.php','download'))]
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch,range(1,7)):print(result)
