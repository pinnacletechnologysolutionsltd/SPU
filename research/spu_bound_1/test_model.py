import unittest
from . import model as m
from . import oracle as o
from .measure import BOX, run

class Checks(unittest.TestCase):
    def test_all_registered_cases(self):
        for name in ('F1','F2','F3','F4'):
            with self.subTest(name=name):
                result=run(name)
                self.assertEqual(result['inputs'],25 if name in ('F2','F4') else 625)
    def test_non_linear_relations(self):
        self.assertEqual(run('F2')['poly_bound'],((-12,4),(0,0)))
        self.assertEqual(run('F3')['exact'],((-24,24),(-24,24)))
        self.assertEqual(run('F4')['exact'],((-12,4),(0,0)))
        self.assertEqual(m.pbound(m.pmul(m.var(0),m.var(0)),BOX),(0,4))
    def test_independent_oracle_basics(self):
        self.assertEqual(o.multiply((2,3),(4,5)),(53,22))
        self.assertEqual(o.multiply((3,-2),(3,2)),(-3,0))
    def test_f5_and_f6(self):
        values=[a*a for a in range(-2,3)]
        self.assertEqual((min(values),max(values)),(0,4))
        big=(1<<63)-1
        first=o.multiply((big,0),(2,1))
        final=o.multiply(first,(2,-1))
        self.assertEqual(first,(2*big,big))
        self.assertEqual(final,(big,0))
        self.assertEqual(max(map(m.width,first)),65)
        x=(m.var(0),m.var(1)); y=(m.const(2),m.const(1))
        p=m.smul(m.smul(x,y),m.sconj(y))
        self.assertEqual(tuple(m.peval(q,(big,0,0,0)) for q in p),final)
        self.assertEqual(m.imul(m.imul(((big,big),(0,0)),((2,2),(1,1))),((2,2),(-1,-1))),((big,big),(0,0)))

    def test_wrong_formula_control(self):
        a,b,c,d=1,1,1,1
        self.assertNotEqual(a*c+b*d,o.multiply((a,b),(c,d))[0])

if __name__ == '__main__': unittest.main()
