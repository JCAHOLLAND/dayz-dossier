import unittest
from associations import analyse

def event(day,second,killer,victim):
    return {'timestamp':f'2024-06-{day:02d}T12:{second//60:02d}:{second%60:02d}.000Z','killer':{'id':killer},'victim':{'id':victim}}

class AssociationTests(unittest.TestCase):
    def test_global_maximum_three_and_consistent_membership(self):
        events=[event(day,i*20,actor,'opponent') for day in (1,2,3) for i,actor in enumerate('abcd')]
        result=analyse(events)['profiles']
        for pid,p in result.items():
            group={pid,*[r['id'] for r in p['team']]}
            self.assertLessEqual(len(group),3)
            for other in group-{pid}:self.assertEqual(group,{other,*[r['id'] for r in result[other]['team']]})
        self.assertTrue(any(p['team'] for p in result.values()))
    def test_both_victim_and_killer_roles_and_direct_combat(self):
        events=[]
        for day in (1,2,3):events.extend([event(day,0,'opponent','a'),event(day,30,'b','opponent')])
        before=analyse(events)['profiles']['a'];record=next(r for r in before['team']+before['candidates'] if r['id']=='b')
        self.assertEqual(record['sharedWindows'],3);self.assertEqual(record['days'],3)
        events.append(event(4,0,'a','b'))
        after=analyse(events)['profiles']['a'];record2=next(r for r in after['candidates'] if r['id']=='b')
        self.assertEqual(record2['directCombats'],1);self.assertFalse(record2['eligible'])
        self.assertLess(record2['strength'],record['strength'])
    def test_one_continuous_fight_cannot_create_two_windows(self):
        events=[event(1,s,k,'opponent') for s,k in [(29*60,'a'),(29*60+10,'b'),(31*60,'a'),(31*60+10,'b')]]
        r=analyse(events)['profiles']['a']['candidates'][0]
        self.assertEqual(r['sharedWindows'],1);self.assertFalse(r['eligible'])
    def test_empty_input(self):self.assertEqual(analyse([])['profiles'],{})
    def test_weapon_names_have_no_effect(self):
        events=[event(day,i*20,k,'opponent') for day in (1,2,3) for i,k in enumerate('abc')]
        a=analyse([{**e,'weapon':'M4-A1'} for e in events])
        b=analyse([{**e,'weapon':'unrelated-'+str(i)} for i,e in enumerate(events)])
        self.assertEqual(a,b)

if __name__=='__main__':unittest.main()
