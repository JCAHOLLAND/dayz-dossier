"""Build the offline dashboard data from Discord HTML exports (stdlib only)."""
from html.parser import HTMLParser
from pathlib import Path
import json, re

class Messages(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[]; self.row=None; self.depth=0; self.content_depth=None; self.anchor=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='li' and a.get('id','').startswith('chat-messages-'):
            self.row={'id':a['id'].split('-')[-1], 'timestamp':None,'text':'','profiles':[]}
        if self.row is None: return
        if tag=='time': self.row['timestamp']=a.get('datetime')
        if tag=='div':
            self.depth+=1
            if a.get('id','').startswith('message-content-'): self.content_depth=self.depth
        if self.content_depth is not None and tag=='a':
            m=re.fullmatch(r'https://app\.cftools\.cloud/profile/([A-Za-z0-9]+)(?:/)?',a.get('href',''))
            if m:
                self.anchor={'id':m[1],'name':''}; self.row['profiles'].append(self.anchor)
    def handle_data(self,data):
        if self.row is not None and self.content_depth is not None:
            self.row['text']+=data
            if self.anchor is not None: self.anchor['name']+=data
    def handle_endtag(self,tag):
        if tag=='a': self.anchor=None
        if tag=='div':
            if self.content_depth==self.depth: self.content_depth=None
            self.depth=max(0,self.depth-1)
        if tag=='li' and self.row is not None:
            self.rows.append(self.row); self.row=None; self.content_depth=None; self.depth=0

def parse_event(row):
    ps=row['profiles']
    if len(ps)!=2:return None
    prefix=f"{ps[0]['name']} got killed by {ps[1]['name']}"
    if not row['text'].startswith(prefix):return None
    match=re.fullmatch(r'\((.+),\s*([\d.]+)m\)',row['text'][len(prefix):].strip())
    if match and row['timestamp']:
        try:
            distance=float(match[2])
        except ValueError:return None
        return {'id':row['id'],'timestamp':row['timestamp'],'victim':ps[0],'killer':ps[1],'weapon':match[1].strip(),'distance':distance}
    return None

def build(paths):
    groups={};events=[];unparsed=[];files=[];conflicts=[];recovered=[];examples=[]
    for index,path in enumerate(paths):
        parser=Messages();parser.feed(path.read_text(encoding='utf-8-sig'))
        earlier=set(groups);local=set();overlap=set()
        counts={'name':path.name,'messages':len(parser.rows),'duplicates':0,'parsed':0,'unparsed':0,'withinFileDuplicates':0,'overlapIdsWithEarlierFiles':0}
        for row in parser.rows:
            row['text']=re.sub(r'\s+',' ',row['text']).strip()
            for p in row['profiles']:p['name']=re.sub(r'\s+',' ',p['name']).strip()
            row['source']=path.name;row['sourceIndex']=index
            if row['id'] in local:counts['withinFileDuplicates']+=1
            if row['id'] in earlier:overlap.add(row['id'])
            local.add(row['id'])
            if row['id'] in groups:counts['duplicates']+=1
            groups.setdefault(row['id'],[]).append(row)
        counts['overlapIdsWithEarlierFiles']=len(overlap)
        files.append(counts)
    for mid,rows in groups.items():
        evaluated=[(row,parse_event(row)) for row in rows]
        chosen,event=max(evaluated,key=lambda x:(x[1] is not None,len(x[0]['text']),len(x[0]['profiles'])))
        owner=files[rows[0]['sourceIndex']]
        if event:events.append(event);owner['parsed']+=1
        else:unparsed.append({k:v for k,v in {**chosen,'reason':'Unrecognized event format or missing profile/timestamp'}.items() if k!='sourceIndex'});owner['unparsed']+=1
        variants={}
        for row,parsed in evaluated:
            signature=json.dumps([row['timestamp'],row['text'],row['profiles']],sort_keys=True)
            if signature not in variants:variants[signature]={'source':row['source'],'text':row['text'],'timestamp':row['timestamp'],'profiles':row['profiles'],'parsed':parsed is not None}
        if len(variants)>1:conflicts.append({'id':mid,'chosenSource':chosen['source'],'reason':'Same message ID has different normalized content; richest valid copy retained.','variants':list(variants.values())})
        if event and evaluated[0][1] is None:recovered.append({'id':mid,'firstSource':rows[0]['source'],'chosenSource':chosen['source']})
        if len(rows)>1 and len(examples)<5:examples.append({'id':mid,'occurrences':len(rows),'sources':{name:sum(r['source']==name for r in rows) for name in dict.fromkeys(r['source'] for r in rows)},'text':chosen['text']})
    events.sort(key=lambda e:e['timestamp'],reverse=True)
    raw=sum(f['messages'] for f in files);duplicate=sum(f['duplicates'] for f in files)
    assert raw==len(groups)+duplicate
    assert len(groups)==len(events)+len(unparsed)
    return {'events':events,'unparsed':unparsed,'files':files,'audit':{'rawOccurrences':raw,'uniqueMessageIds':len(groups),'duplicateOccurrences':duplicate,'conflictingIds':len(conflicts),'recoveredIds':len(recovered),'examples':examples},'conflicts':conflicts,'recovered':recovered}

if __name__=='__main__':
    result=build(sorted(Path('.').glob('killfeedpart*.txt')))
    Path('data.js').write_text('window.DOSSIER_DATA = '+json.dumps(result,ensure_ascii=True)+';\n',encoding='utf-8')
    print(json.dumps({'files':result['files'],'events':len(result['events']),'unparsed':len(result['unparsed'])},indent=2))
