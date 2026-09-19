import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from audit_extraction_claims import literal_claims

class LiteralAuditTests(unittest.TestCase):
    def test_single_claim_and_residual(self):
        claims,extra=literal_claims('Attended yoga session on Day 03 and did not enjoy it. A clock stood nearby.')
        self.assertEqual(claims,[{'activity':'yoga','day':3,'positive':False}])
        self.assertEqual(extra,'. A clock stood nearby.')
    def test_group_claims(self):
        claims,extra=literal_claims('Enjoyed chess session on days: 01, 04, 12')
        self.assertEqual([c['day'] for c in claims],[1,4,12])
        self.assertTrue(all(c['positive'] for c in claims));self.assertEqual(extra,'')
    def test_unsupported_text_remains_unjudged(self):
        text='User generally likes swimming more than cycling.'
        self.assertEqual(literal_claims(text),([],text))
    def test_negation_not_misread_as_positive(self):
        claims,_=literal_claims('Did not enjoy chess session on days: 01, 02')
        self.assertTrue(all(c['positive'] is False for c in claims))
    def test_explicit_date_first_formats(self):
        for text in ['V01 | Day 01: Attended a yoga session and did not enjoy it',
                     'Day 01: Attended a yoga session, did not enjoy the session',
                     'Attended yoga session on Day 01, did not enjoy']:
            claims,extra=literal_claims(text)
            self.assertEqual(claims,[{'activity':'yoga','day':1,'positive':False}])
            self.assertEqual(extra,'')
if __name__=='__main__':unittest.main()
