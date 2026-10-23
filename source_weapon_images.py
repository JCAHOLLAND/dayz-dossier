"""One-off source acquisition; the dashboard itself never accesses the internet."""
import json, urllib.request, urllib.parse
from pathlib import Path

# Exact Standalone page/file matches verified through the DayZ Wiki page image lists.
items={'DMR':('DMR','M14.png'),'VSD':('VSD','SVD.png'),'M4-A1':('M4-A1','M4A1.png'),'M70 Tundra':('M70 Tundra','Winchester70.png'),'CR-550 Savanna':('CR-550 Savanna','CZ550.png'),'VS-89':('VS-89','SV98.png'),'Blaze':('Blaze','B95.png')}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://dayz.fandom.com/'}),timeout=30).read()
def api(**args):
    return json.loads(get('https://dayz.fandom.com/api.php?'+urllib.parse.urlencode({'action':'query','format':'json',**args})))
if __name__=='__main__':
    folder=Path('assets/weapons');folder.mkdir(exist_ok=True)
    additional=['Vikhr','LAR','SVAL','VSS','KA-M','KA-74','KA-101','Mosin 91/30','SK 59/66','SSG 82','LE-MAS','AUR AX','M16-A2','BK-133','USG-45','SG5-K','CR-61 Skorpion','Pioneer','KAS-74U','CR-527','Mlock-91','Bizon','IJ-70','BK-43','Deagle']
    pages=api(titles='|'.join(additional),prop='pageimages',piprop='name')['query']['pages']
    for page in pages.values():
        if page.get('pageimage'):items[page['title']]=(page['title'],page['pageimage'])
    result={}
    for name,(page,file) in items.items():
        info=api(titles='File:'+file,prop='imageinfo|revisions',iiprop='url|extmetadata',rvprop='content')
        record=next(iter(info['query']['pages'].values()));image=record['imageinfo'][0]
        raw=get(image['url']);extension='.png' if raw.startswith(b'\x89PNG') else '.webp' if raw.startswith(b'RIFF') else None
        if extension is None:raise ValueError('Expected image: '+name)
        filename=Path(file).stem.lower()+extension
        (folder/filename).write_bytes(raw)
        result[name]={'src':'/assets/weapons/'+filename,'page':'https://dayz.fandom.com/wiki/'+urllib.parse.quote(page),'filePage':image['descriptionurl'],'original':image['url'],'copyright':'Bohemia Interactive; game screenshot/cutout via DayZ Wiki','reuse':'Game screenshot use under Bohemia Game Content Usage Rules. Wiki file descriptions preserved below; not claimed to be freely licensed game assets.','fileDescription':record['revisions'][0]['*']}
        print(name,len(raw),flush=True)
    Path('assets/weapon-sources.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
