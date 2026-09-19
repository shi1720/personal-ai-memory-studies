"""Non-inference exhaustive checks of the grid-resolution derivation."""
import itertools
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from certificate_cost import oracle_certificate_cost

class GridCertificateTests(unittest.TestCase):
    def test_singleton_boundary_requires_every_uncached_row(self):
        patterns=[(0,0,0,0),(1,0,0,0),(1,1,0,0),(1,1,1,0)]
        checked=0
        for n in range(1,5):
            for rows in itertools.product(patterns,repeat=n):
                for alpha in [.1,.3,.5,.8]:
                    base=oracle_certificate_cost(rows,alpha)
                    j=base['policy']
                    if 0<j<3 and sum(r[j-1]-r[j] for r in rows)==1:
                        for mask in range(2**n):
                            cached=[i for i in range(n) if mask>>i&1]
                            self.assertEqual(oracle_certificate_cost(rows,alpha,cached)['calls'],n-len(cached))
                        checked+=1
        self.assertGreater(checked,0)

    def test_nested_grid_oracle_cost_never_decreases_with_refinement(self):
        patterns=[tuple(int(j<jump) for j in range(5)) for jump in range(5)]
        for n in range(1,5):
            for rows in itertools.product(patterns,repeat=n):
                for alpha in [.1,.3,.5,.8]:
                    for mask in [0,1,2**n-1]:
                        cached=[i for i in range(n) if mask>>i&1]
                        fine=oracle_certificate_cost(rows,alpha,cached)['calls']
                        for subset in [(0,4),(0,2,4),(0,1,3,4)]:
                            coarse=[tuple(r[j] for j in subset) for r in rows]
                            self.assertLessEqual(oracle_certificate_cost(coarse,alpha,cached)['calls'],fine)

if __name__=='__main__':unittest.main()
