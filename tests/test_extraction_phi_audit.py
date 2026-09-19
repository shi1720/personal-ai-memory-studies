import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from audit_extraction_phi import grouped_claims, count_claims


class PhiClaimAuditTests(unittest.TestCase):
    def test_repeated_day_prefix_and_period(self):
        claims, residual = grouped_claims('Did not enjoy yoga sessions on Day 01, Day 04, Day 09.')
        self.assertEqual([c['day'] for c in claims], [1, 4, 9])
        self.assertTrue(all(c['positive'] is False for c in claims))
        self.assertEqual(residual, '')

    def test_attendance_continuation_preserves_distinct_claim_types(self):
        claims, residual = grouped_claims('Attended pottery sessions on Days 01, 02, 03 and did not enjoy them on Days 01, 02')
        self.assertEqual([c['positive'] for c in claims], [None, None, None, False, False])
        self.assertEqual([c['day'] for c in claims], [1, 2, 3, 1, 2])
        self.assertEqual(residual, '')

    def test_date_list_does_not_consume_numerical_summary(self):
        events, residual = grouped_claims('Attended swimming sessions on Days 01, 02. Total swimming sessions: 12. Enjoyed 9 swimming sessions. Did not enjoy 3 swimming sessions.')
        counts, residual = count_claims(residual)
        self.assertEqual(len(events), 2)
        self.assertEqual({c['quantity']: c['value'] for c in counts}, {'total': 12, 'positive': 9, 'negative': 3})
        self.assertEqual(residual, '')

    def test_inconsistent_counts_are_preserved_without_repair(self):
        for text in ['Attended 10 pottery sessions, 4 not-enjoyed, 2 enjoyed',
                     'Total pottery sessions: 10, Enjoyed: 2, Did not enjoy: 4.']:
            counts, residual = count_claims(text)
            self.assertEqual({c['quantity']: c['value'] for c in counts}, {'total': 10, 'positive': 2, 'negative': 4})
            self.assertEqual(residual, '')

    def test_unknown_language_stays_unjudged(self):
        text = 'Usually preferred pottery, but sometimes enjoyed neither activity.'
        self.assertEqual(grouped_claims(text), ([], text))
        self.assertEqual(count_claims(text), ([], text))

    def test_semicolon_outcomes_and_compact_counts(self):
        claims, residual = grouped_claims('Attended chess sessions on Days 01, 02 and did not enjoy on Days 01; enjoyed on Days 02.')
        self.assertEqual([c['positive'] for c in claims], [None, None, False, True])
        self.assertEqual(residual, '')
        for text in ['Attended 12 chess sessions: 4 enjoyed, 8 not-enjoyed',
                     'Total chess sessions: 12. Enjoyed chess sessions: 4. Did not enjoy chess sessions: 8.']:
            counts, residual = count_claims(text)
            self.assertEqual({c['quantity']: c['value'] for c in counts}, {'total': 12, 'positive': 4, 'negative': 8})
            self.assertEqual(residual, '')

    def test_embedded_negative_phrase_is_not_a_count_claim(self):
        text = 'It is false that Enjoyed 9 chess sessions.'
        self.assertEqual(count_claims(text), ([], text))

    def test_additional_observed_literals(self):
        claims, residual = grouped_claims('Attended chess sessions on Days 01, 02 and did not enjoy on Days 01, 01, and enjoyed on Days 02.')
        self.assertEqual([c['day'] for c in claims], [1, 2, 1, 1, 2])
        self.assertEqual(residual, '')
        claims, residual = grouped_claims('Day 04: Swimming session enjoyed, noted a blue mural')
        self.assertEqual(claims, [{'activity': 'swimming', 'day': 4, 'positive': True}])
        self.assertEqual(residual, ', noted a blue mural')
        counts, residual = count_claims('Total visits to chess sessions: 10, Enjoyed: 5, Did not enjoy: 5.')
        self.assertEqual({c['quantity']: c['value'] for c in counts}, {'total': 10, 'positive': 5, 'negative': 5})
        self.assertEqual(residual, '')


if __name__ == '__main__':
    unittest.main()
