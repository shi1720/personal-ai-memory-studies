from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from coat_baselines import population_fit, predictions, score_users, user_split


class CoatBaselineTests(unittest.TestCase):
    def fixture(self):
        features = np.column_stack([np.ones(8), np.arange(8) % 2, np.arange(8) // 4])
        train = np.array([[1,4,0,0,0,0,0,0], [0,0,3,2,0,0,0,0],
                          [0,4,0,2,0,0,0,0], [2,0,3,0,0,0,0,0],
                          [0,0,0,0,1,5,0,0], [0,0,0,0,0,0,2,3]], dtype=float)
        test = np.array([[0,4,2,0,0,0,3,0], [1,0,0,0,4,0,0,2],
                         [0,4,0,0,0,1,3,0], [0,0,3,0,4,0,0,2],
                         [4,3,0,0,0,0,0,0], [0,0,5,1,0,0,0,0]], dtype=float)
        return train, test, features

    def test_user_partition_exact_and_disjoint(self):
        split = user_split()
        self.assertEqual([len(split[k]) for k in ['fitting','development','reserved_evaluation']], [60,30,200])
        joined = sum(split.values(), [])
        self.assertEqual(sorted(joined), list(range(290)))
        self.assertEqual(len(set(joined)), 290)
        self.assertEqual(user_split(), split)

    def test_reserved_labels_and_histories_cannot_change_development(self):
        train, test, features = self.fixture()
        first = population_fit(train, test, features, [0,1])
        before = score_users(train, test, features, first, [2,3], 'exposure_positive', 1.)
        train[4:] = 5
        test[4:] = 1
        second = population_fit(train, test, features, [0,1])
        after = score_users(train, test, features, second, [2,3], 'exposure_positive', 1.)
        np.testing.assert_array_equal(first['beta'], second['beta'])
        np.testing.assert_array_equal(first['propensities'], second['propensities'])
        self.assertEqual(before, after)

    def test_targets_do_not_enter_personalization(self):
        train, test, features = self.fixture()
        pop = population_fit(train, test, features, [0,1])
        a = predictions(train[2], features, pop, 'uniform', 1.)
        test[2] = 5
        b = predictions(train[2], features, pop, 'uniform', 1.)
        np.testing.assert_array_equal(a,b)

    def test_constant_gate_has_same_regularization(self):
        train, test, features = self.fixture()
        pop = population_fit(train, test, features, [0,1])
        history = np.array([4.,5.,0,4.,0,0,5.,0])
        np.testing.assert_allclose(predictions(history,features,pop,'positive',1.),
                                   predictions(history,features,pop,'uniform',1.), rtol=1e-14, atol=1e-14)

    def test_cache_separates_recall_from_prediction(self):
        train, test, features = self.fixture()
        pop = population_fit(train, test, features, [0,1])
        cached = score_users(train,test,features,pop,[2,3],'exact_cache')
        base = score_users(train,test,features,pop,[2,3],'population_features')
        self.assertEqual(cached['summaries']['known']['macro_mae'],0.)
        self.assertEqual(cached['summaries']['new'],base['summaries']['new'])
        self.assertEqual(cached['summaries']['new']['targets'],4)
        self.assertEqual(cached['summaries']['known']['targets'],2)


if __name__ == '__main__':
    unittest.main()
