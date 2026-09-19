import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from retention_pilot_data import make_journals,parse_selection,render_journal

class RetentionDataTests(unittest.TestCase):
    def test_balanced_journals_have_fixed_empirical_targets(self):
        journals=make_journals()
        self.assertEqual(journals,make_journals())
        self.assertEqual(len(journals),12)
        for j in journals:
            self.assertEqual(len({e['id'] for e in j['events']}),24)
            for a,count in zip(j['activities'],[9,6]):
                events=[e for e in j['events'] if e['activity']==a]
                self.assertEqual(len(events),12)
                self.assertEqual(sum(e['positive'] for e in events),count)
            self.assertEqual(sum(bool(e['detail']) for e in j['events']),6)
            for detailed in [False,True]:
                text=render_journal(j,detailed)
                self.assertEqual(text.count('I enjoyed the session.'),15)
                self.assertEqual(text.count('I did not enjoy the session.'),9)
    def test_malformed_selections_are_not_repaired(self):
        allowed={f'E{i:02d}' for i in range(1,25)}
        good='["E01","E02","E03","E04","E05","E06"]'
        self.assertIsNotNone(parse_selection(good,allowed))
        for bad in ['```json\n'+good+'\n```',good.replace('E06','E01'),good.replace('E06','E99'),'[1,2,3,4,5,6]']:
            self.assertIsNone(parse_selection(bad,allowed))

from analyze_retention_pilot import measure

class RetentionMetricTests(unittest.TestCase):
    def test_full_population_has_zero_error_and_correct_order(self):
        j=make_journals()[0]
        m=measure(j,[e['id'] for e in j['events']])
        self.assertEqual(m['mae_available'],0)
        self.assertEqual(m['rank'],'correct')
    def test_missing_activity_is_reported_not_imputed(self):
        j=make_journals()[0]
        selected=[e['id'] for e in j['events'] if e['activity']==j['activities'][0]][:6]
        m=measure(j,selected)
        self.assertEqual(m['missing_activities'],1)
        self.assertEqual(m['rank'],'missing')
    def test_selected_positive_visits_do_not_have_zero_population_error(self):
        j=make_journals()[0]
        selected=[]
        for activity in j['activities']:
            selected.extend([e['id'] for e in j['events'] if e['activity']==activity and e['positive']][:3])
        m=measure(j,selected)
        self.assertEqual(m['mae_available'],.375)
        self.assertEqual(m['rank'],'tie')

if __name__=='__main__':unittest.main()
