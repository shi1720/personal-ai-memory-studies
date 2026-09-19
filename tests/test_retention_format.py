import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from retention_format_sensitivity import parse_fenced_selection

class FenceSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.ids = {f'E{i:02d}' for i in range(1, 25)}
        self.valid = '["E01", "E02", "E03", "E04", "E05", "E06"]'
    def test_bare_and_fence_only(self):
        self.assertEqual(parse_fenced_selection(self.valid, self.ids)[1], 'strict')
        for tag in ['json', '']:
            self.assertEqual(parse_fenced_selection('```' + tag + '\n' + self.valid + '\n```', self.ids)[1], 'fence_only')
    def test_no_prose_recovery(self):
        for text in ['Here is the answer:\n```json\n' + self.valid + '\n```', '```json\n' + self.valid + '\n```\nExplanation']:
            self.assertEqual(parse_fenced_selection(text, self.ids), (None, 'invalid'))
    def test_does_not_repair_semantic_or_json_errors(self):
        for text in [self.valid.replace('E06','E25'), self.valid.replace('E06','E01'), self.valid.replace('"','')]:
            self.assertEqual(parse_fenced_selection('```json\n'+text+'\n```', self.ids), (None, 'invalid'))
if __name__ == '__main__':
    unittest.main()
