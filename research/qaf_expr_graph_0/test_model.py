import unittest
from fractions import Fraction
from itertools import product
from research.qaf_expr_graph_0.model import (Node, X, Y, U, V, CANCEL, CONJ_PRODUCT,
    NORM_X, FACTOR_ORIGINAL, FACTOR, normal, eval_graph, eval_poly, exact_box, nodes)

class ExpressionGraphTests(unittest.TestCase):
    def test_identities_and_original_graph(self):
        self.assertEqual(normal(CANCEL), normal(X))
        self.assertNotEqual(CANCEL, X)
        self.assertEqual(len(nodes(CANCEL)), 5)
        self.assertEqual(normal(CONJ_PRODUCT), normal(NORM_X))
        self.assertEqual(normal(NORM_X)[1], {})
        self.assertEqual(normal(FACTOR_ORIGINAL), normal(FACTOR))
        self.assertNotEqual(FACTOR_ORIGINAL, FACTOR)

    def test_exhaustive_and_fraction_values(self):
        roots = [CANCEL, CONJ_PRODUCT, NORM_X, FACTOR_ORIGINAL, FACTOR,
                 Node('add', (X, Y)), Node('mul', (X, Y))]
        forms = [normal(n) for n in roots]
        for v in product(range(-2, 3), repeat=4):
            inputs = {'x': v[:2], 'y': v[2:]}
            for n, f in zip(roots, forms):
                self.assertEqual(eval_graph(n, inputs), eval_poly(f, inputs))
        inputs = {'x': (Fraction(1, 2), Fraction(-2, 3)),
                  'y': (Fraction(3, 5), Fraction(4, 7))}
        for n, f in zip(roots, forms):
            self.assertEqual(eval_graph(n, inputs), eval_poly(f, inputs))

    def test_bounds_and_nonimplications(self):
        box = ((-2,2),)*4
        self.assertEqual(exact_box(FACTOR_ORIGINAL, box), ((-24,24),(-24,24)))
        self.assertEqual(exact_box(CANCEL, box), ((-2,2),(-2,2)))
        self.assertNotEqual(normal(X), normal(Node('conj', (X,))))
        self.assertEqual(normal(Node('norm', (X,))), normal(Node('norm', (Node('conj',(X,)),))))
        self.assertNotEqual(normal(Node('mul',(X,Y))), normal(Node('mul',(X,Node('conj',(Y,))))))

    def test_growth_and_refusal_boundary(self):
        seq = X
        for _ in range(34):
            seq = Node('mul', (seq, U))
        result = eval_graph(seq, {'x': (1,0), 'y': (0,0)})
        self.assertEqual(result[0], 13969685227624439047)
        self.assertGreater(result[0], (1<<63)-1)
        start={'x': ((1<<63)-1, 0), 'y': (0,0)}
        self.assertEqual(eval_graph(CANCEL,start),eval_graph(X,start))
        intermediate=eval_graph(CANCEL.args[0],start)
        self.assertGreater(intermediate[0],(1<<63)-1)
        self.assertNotEqual(CANCEL, X)  # provenance; no instruction-equivalence claim

    def test_mutant_false_rule(self):
        # conj(x) is not generally x, and norm equality cannot imply value equality.
        x=(1,2)
        value={'x':x,'y':(0,0)}
        self.assertNotEqual(eval_graph(X,value),eval_graph(Node('conj',(X,)),value))
        self.assertEqual(eval_graph(Node('norm',(X,)),value),eval_graph(Node('norm',(Node('conj',(X,)),)),value))
        with self.assertRaises(ValueError): normal(Node('divide',(X,Y)))

if __name__ == '__main__': unittest.main()
