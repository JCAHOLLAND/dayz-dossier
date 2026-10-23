"""Explainable combat-pattern associations; scores are evidence indices, not probabilities."""
from collections import defaultdict, Counter
from datetime import datetime, timezone
from itertools import combinations
import math

def analyse(events,confirmed_groups=None):
    edges={}; interactions=defaultdict(list); hours=defaultdict(Counter); direct=Counter(); timeline=[];activity=defaultdict(Counter);distances=defaultdict(Counter)
    def edge(a,b):
        key=tuple(sorted((a,b)))
        if key not in edges:edges[key]={'shared':set(),'context':set(),'opponents':set(),'samples':[],'patterns':defaultdict(set)}
        return edges[key]
    for e in events:
        a,b=e['killer']['id'],e['victim']['id']
        dt=datetime.fromisoformat(e['timestamp'].replace('Z','+00:00'));t=dt.timestamp();day=dt.strftime('%Y-%m-%d')
        if a==b:continue
        direct[tuple(sorted((a,b)))]+=1
        distances[a][int(min(9,e.get('distance',0)//100))]+=1
        for actor,opponent,role in [(a,b,'killer'),(b,a,'victim')]:
            interactions[opponent].append((t,actor,role,e['timestamp'],day));hours[actor][dt.hour]+=1;activity[actor][int(t//1800)]+=1
        timeline.append((t,(a,b),day))
    # All roles count: two players kill the same opponent, die to the same opponent,
    # or appear on opposite sides of separate encounters involving that opponent.
    for opponent,records in interactions.items():
        records.sort()
        for i,(t,a,role,stamp,day) in enumerate(records):
            for j in range(i+1,len(records)):
                u,b,other,stamp2,day2=records[j]
                if u-t>180:break
                if a==b:continue
                item=edge(a,b)
                if t not in item['shared'] and len(item['samples'])<3:
                    item['samples'].append({'timestamp':stamp,'otherTimestamp':stamp2,'opponent':opponent,'roles':[role,other]})
                item['shared'].add(t);item['opponents'].add(opponent)
                item['patterns']['sharedThreat' if role==other=='victim' else 'sharedTarget' if role==other=='killer' else 'tradeSequence'].add(t)
    # Weak temporal context considers both endpoints of every event. A fight with
    # many messages contributes just one continuous context observation window.
    timeline.sort()
    for i,(t,actors,day) in enumerate(timeline):
        for j in range(i+1,len(timeline)):
            u,others,day2=timeline[j]
            if u-t>60:break
            for a in actors:
                for b in others:
                    if a!=b:edge(a,b)['context'].add(t)
    def episodes(times):
        output=[];last=None
        for t in sorted(times):
            if last is None or t-last>1800:output.append(t)
            last=t
        return output
    graph=defaultdict(set)
    for (a,b),item in edges.items():
        if len(episodes(item['shared']))>=2:graph[a].add(b);graph[b].add(a)
    opponentPopularity={pid:len({r[1] for r in records}) for pid,records in interactions.items()}
    def similarity(a,b):
        na=sum(a.values());nb=sum(b.values())
        return sum(min(a[k]/na,b[k]/nb) for k in a.keys()|b.keys()) if min(na,nb)>=5 else 0
    candidates=defaultdict(list);eligible={}
    for (a,b),item in edges.items():
        independent=episodes(item['shared']);windows=len(independent);context=len(episodes(item['context']));combats=direct[(a,b)]
        # Only evidence-bearing pairs with repeated windows, or a shared opponent,
        # are useful to inspect. Mere isolated co-occurrence stays out of the UI.
        days=len({datetime.fromtimestamp(t,tz=timezone.utc).date() for t in independent})
        totalA=sum(hours[a].values());totalB=sum(hours[b].values())
        overlap=sum(min(hours[a][h]/totalA,hours[b][h]/totalB) for h in range(24)) if min(totalA,totalB)>=5 else 0
        expected=sum(min(1,activity[a][w]*activity[b][w]/15) for w in activity[a].keys()&activity[b].keys())
        timingExcess=max(0,context-expected)
        rarity=sum(1/math.sqrt(max(1,opponentPopularity[o])) for o in item['opponents'])/len(item['opponents']) if item['opponents'] else 0
        roleCounts={kind:len(episodes(times)) for kind,times in item['patterns'].items()}
        roleDiversity=min(4,max(0,len(roleCounts)-1)*2)
        mutual=graph[a]&graph[b]
        graphSupport=min(5,sum(2/math.sqrt(max(1,len(graph[n]))) for n in mutual))
        distanceOverlap=similarity(distances[a],distances[b])
        observations=len(episodes(item['shared']|item['context']))
        reliability=.65+.35*observations/(observations+3)
        components={'sharedOpponents':8*min(windows,10)*(.7+.3*rarity),'repeatDays':3*min(days,6),'timingExcess':min(10,2*timingExcess),'timingContext':min(6,2*math.log1p(context)),'patternDiversity':roleDiversity,'graphContext':graphSupport,'hourContext':4*overlap,'distanceContext':1.5*distanceOverlap,'directCombatPenalty':-min(40,8*combats)}
        rawScore=sum(components.values());unbounded=rawScore*reliability
        score=round(max(0,min(100,unbounded)))
        qualifies=windows>=2 and score>=30 and combats==0
        evidence={'strength':score,'rawStrength':round(rawScore,4),'unboundedStrength':round(unbounded,4),'saturated':unbounded>=100,'sharedWindows':windows,'days':days,'opponents':len(item['opponents']),'contextWindows':context,'directCombats':combats,'hourOverlap':round(overlap,2),'expectedTimingWindows':round(expected,2),'distanceOverlap':round(distanceOverlap,2),'mutualPatternNeighbours':len(mutual),'rolePatterns':roleCounts,'independentObservations':observations,'reliabilityMultiplier':round(reliability,6),'components':{k:round(v,2) for k,v in components.items()},'samples':item['samples'],'eligible':qualifies}
        if qualifies:eligible[(a,b)]=score
        candidates[a].append({'id':b,**evidence});candidates[b].append({'id':a,**evidence})
    # Form one global non-overlapping partition. A trio requires qualifying
    # evidence on ALL three edges; taking independent top-two lists is forbidden.
    neighbours=defaultdict(set)
    for a,b in eligible:neighbours[a].add(b);neighbours[b].add(a)
    proposals=[]
    for (a,b),score in eligible.items():
        proposals.append((score,(a,b)))
        for c in neighbours[a]&neighbours[b]:
            if c>b:
                members=tuple(sorted((a,b,c)))
                proposals.append((sum(eligible[tuple(sorted(pair))] for pair in combinations(members,2)),members))
    assigned={};used=set();confirmed_pairs=set()
    for members in confirmed_groups or []:
        members=tuple(sorted(set(members)))
        if not 2<=len(members)<=3:raise ValueError('Confirmed groups must contain two or three total profiles.')
        if used.intersection(members):raise ValueError('Confirmed groups must not overlap.')
        used.update(members)
        for a,b in combinations(members,2):
            confirmed_pairs.add(tuple(sorted((a,b))))
            for pid,other in [(a,b),(b,a)]:
                if not any(r['id']==other for r in candidates[pid]):
                    candidates[pid].append({'id':other,'strength':0,'sharedWindows':0,'days':0,'opponents':0,'contextWindows':0,'directCombats':direct[tuple(sorted((a,b)))],'hourOverlap':0,'expectedTimingWindows':0,'distanceOverlap':0,'mutualPatternNeighbours':0,'rolePatterns':{},'independentObservations':0,'reliabilityMultiplier':.65,'components':{},'samples':[],'eligible':False})
        for pid in members:assigned[pid]=[other for other in members if other!=pid]
    for score,members in sorted(proposals,key=lambda p:(-p[0],-len(p[1]),p[1])):
        if used.intersection(members):continue
        used.update(members)
        for pid in members:assigned[pid]=[other for other in members if other!=pid]
    result={}
    for pid,records in candidates.items():
        for r in records:r['confirmed']=tuple(sorted((pid,r['id']))) in confirmed_pairs
        records.sort(key=lambda r:(-r['strength'],-r['sharedWindows'],r['id']))
        team=assigned.get(pid,[])
        result[pid]={'team':[r for r in records if r['id'] in team],'candidates':[r for r in records if r['id'] not in team][:8]}
    return {'profiles':result,'method':'combat-pattern-v2-exploratory','timezone':'UTC','windows':{'sharedOpponentSeconds':180,'contextSeconds':60,'independentGapMinutes':30},'qualifyingEdges':len(eligible),'inferredGroups':len({tuple(sorted([pid]+ids)) for pid,ids in assigned.items()})}
