import unittest, tempfile, json
from pathlib import Path
from unittest.mock import patch
import server

class PortraitTests(unittest.TestCase):
    def test_saved_assignment_survives_name_and_manifest_changes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory,patch.object(server,'ROOT',Path(directory)):
            data={'events':[{'killer':{'id':'a','name':'Before'},'victim':{'id':'b','name':'Other'}}]}
            before=server.attach_portraits(data)['portraits'].copy()
            data['events'][0]['killer']['name']='After'
            with patch.object(server,'PORTRAIT_MANIFEST',['future.png']):
                self.assertEqual(server.attach_portraits(data)['portraits'],before)
            self.assertEqual(json.loads((Path(directory)/'portrait-assignments.json').read_text())['version'],1)
    def test_all_expected_assets_exist(self):
        self.assertEqual(len(server.PORTRAIT_MANIFEST),21)
        for name in server.PORTRAIT_MANIFEST:self.assertTrue((server.ROOT/'assets'/name).is_file(),name)

if __name__=='__main__':unittest.main()
