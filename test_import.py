import unittest
from import_data import build
from server import MemoryFile

def message(mid='1',victim='Example victim',killer='Example killer',weapon='<span>VS</span><span>-89</span>',distance='<span>4</span><span>1</span><span>.74</span>'):
    return f'''<li id="chat-messages-99-{mid}"><div><time datetime="2024-06-08T20:39:49.252Z">noise</time><div id="message-content-{mid}"><a href="https://app.cftools.cloud/profile/victim"><span>{victim}</span></a><span> got killed by </span><a href="https://app.cftools.cloud/profile/killer">{killer}</a><span> (</span>{weapon}<span>, </span>{distance}<span>m)</span></div><div>ignored accessories</div></div></li>'''

class ImportTests(unittest.TestCase):
    def test_split_spans_entities_and_noise(self):
        d=build([MemoryFile('a',message(victim='Example &amp; Co'))]); e=d['events'][0]
        self.assertEqual(e['weapon'],'VS-89');self.assertEqual(e['distance'],41.74)
        self.assertEqual(e['victim'],{'id':'victim','name':'Example & Co'})
        self.assertEqual(e['timestamp'],'2024-06-08T20:39:49.252Z')
    def test_dedup_and_profile_aliases(self):
        d=build([MemoryFile('a',message()),MemoryFile('b',message()+message('2',killer='Another example name'))])
        self.assertEqual(len(d['events']),2);self.assertEqual(d['files'][1]['duplicates'],1)
        self.assertEqual({e['killer']['id'] for e in d['events']},{'killer'})
        self.assertEqual({e['killer']['name'] for e in d['events']},{'Example killer','Another example name'})
    def test_unparsed_preserved(self):
        d=build([MemoryFile('a','<li id="chat-messages-99-3"><div id="message-content-3">Server notice</div></li>')])
        self.assertEqual(len(d['unparsed']),1);self.assertEqual(d['unparsed'][0]['text'],'Server notice')
    def test_richer_copy_recovery_and_conflict_audit(self):
        incomplete='<li id="chat-messages-99-1"><div id="message-content-1">Example victim got killed by</div></li>'
        d=build([MemoryFile('incomplete',incomplete),MemoryFile('valid',message())])
        self.assertEqual(len(d['events']),1);self.assertEqual(len(d['unparsed']),0)
        self.assertEqual(d['audit']['recoveredIds'],1);self.assertEqual(d['audit']['conflictingIds'],1)
        self.assertEqual(d['files'][1]['duplicates'],1)
    def test_identical_text_different_ids_remains_distinct(self):
        d=build([MemoryFile('a',message('1')+message('2'))])
        self.assertEqual(len(d['events']),2);self.assertEqual(d['audit']['duplicateOccurrences'],0)
    def test_parentheses_in_profile_name_are_not_weapon_text(self):
        d=build([MemoryFile('a',message(killer='Example ( ) player',victim='Name (89)'))])
        self.assertEqual(d['events'][0]['weapon'],'VS-89')

if __name__=='__main__': unittest.main()
