"""Sanity checks only: there are no team labels sufficient for accuracy estimates."""
import json,random,statistics
from pathlib import Path
from collections import defaultdict
from associations import analyse
from test_associations import event

text=Path('data.js').read_text();events=json.loads(text[text.index('=')+1:].strip()[:-1])['events']
def stats(a):
    records=[r for p in a['profiles'].values() for r in p['team']+p['candidates']]
    return {'qualifyingEdges':a['qualifyingEdges'],'groups':a['inferredGroups'],'meanDisplayedScore':round(statistics.mean(r['strength'] for r in records),2) if records else 0}
observed=analyse(events)
days=defaultdict(list)
for e in events:days[e['timestamp'][:10]].append(e)
permutations=[]
for seed in (31,73,109):
    rng=random.Random(seed);shuffled=[]
    for rows in days.values():
        stamps=[e['timestamp'] for e in rows];rng.shuffle(stamps)
        shuffled.extend({**e,'timestamp':stamp} for e,stamp in zip(rows,stamps))
    permutations.append(stats(analyse(shuffled)))
ordered=sorted(events,key=lambda e:e['timestamp']);cut=int(.75*len(ordered));train=analyse(ordered[:cut]);holdout=analyse(ordered[cut:])
def pairs(a):return {tuple(sorted((pid,r['id']))) for pid,p in a['profiles'].items() for r in p['team']+p['candidates'] if r['sharedWindows']>=2}
tp,hp=pairs(train),pairs(holdout)
busy=[event(1,second,'busy',f'player{i}') for i,second in enumerate(range(0,600,10))]
busy_result=analyse(busy)
assert busy_result['inferredGroups']==0
unrelated=[event(day,0,f'a{day}',f'b{day}') for day in range(1,20)]
assert analyse(unrelated)['inferredGroups']==0
result={'datasetEvents':len(events),'observed':stats(observed),'withinDayTimestampPermutations':permutations,'temporalHoldout':{'trainEvents':cut,'holdoutEvents':len(ordered)-cut,'trainRepeatedPairs':len(tp),'holdoutRepeatedPairs':len(hp),'repeatedPairsInBoth':len(tp&hp)},'busySingleFightFalseGroupCount':busy_result['inferredGroups'],'note':'No accuracy, precision, recall or calibration claim is possible from these unlabeled sanity checks. Permutations preserve per-day actor/opponent volumes, but destroy chronology and event-hour patterns.'}
Path('association-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
