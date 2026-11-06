import unittest
from dataclasses import FrozenInstanceError
from fractions import Fraction
from research.qaf_expr_graph_0.model import Node, X, Y, CANCEL, CONJ_PRODUCT, NORM_X, FACTOR_ORIGINAL, FACTOR
from research.qaf_ir_0.model import Constraint,build,compare,sampled_bounds

class IntermediateRepresentationTests(unittest.TestCase):
    def setUp(self):
        self.pure=Constraint('mathematical','exact','unobserved','unobserved')
        self.strict=Constraint('strict','toy-signed64','observable','observable')
    def test_norm_and_conjugation(self):
        a,b=build(CONJ_PRODUCT,self.pure),build(NORM_X,self.pure)
        self.assertEqual(a.canonical,b.canonical)
        self.assertNotEqual(a.origin,b.origin)
        self.assertEqual(a.canonical[1],())
        self.assertEqual(a.syntax_deps,frozenset({'x'}))
        self.assertEqual(build(FACTOR_ORIGINAL,self.pure).canonical,build(FACTOR,self.pure).canonical)
    def test_provenance_not_lost(self):
        a,b=build(CANCEL,self.strict),build(X,self.strict)
        self.assertEqual(a.canonical,b.canonical)
        self.assertNotEqual(a.origin,b.origin)
        self.assertEqual(compare(a,b)['rewrite'],'NOT_DECIDED')
        self.assertEqual(compare(a,build(X,self.pure))['rewrite'],'UNKNOWN_CONSTRAINT_MISMATCH')
        with self.assertRaises(FrozenInstanceError): a.origin=X
    def test_structural_vs_value_dependencies(self):
        zero=Node('const',(0,0)); root=Node('mul',(X,zero))
        r=build(root,self.pure)
        self.assertEqual(r.syntax_deps,frozenset({'x'}))
        self.assertEqual(r.value_deps,frozenset())
        self.assertNotEqual(r.origin,zero)
        self.assertEqual(r.canonical,build(zero,self.pure).canonical)
    def test_bounds_and_width_witness(self):
        domain=((-2,2),(-2,2),(0,0),(0,0))
        self.assertEqual(sampled_bounds(CANCEL,domain)['bounds'],((-2,2),(-2,2)))
        record=build(CANCEL,self.strict,domain)
        self.assertEqual(record.bounds.domain,domain)
        self.assertEqual(record.bounds.samples,25)
        self.assertEqual(record.bounds.bounds,((-2,2),(-2,2)))
        self.assertEqual(record.bounds.max_signed_bits,(3,3))
        self.assertIsNone(build(X,self.pure).bounds)
        maximum=(1<<63)-1
        witness=((maximum,maximum),(0,0),(0,0),(0,0))
        first=sampled_bounds(CANCEL.args[0],witness)
        end=sampled_bounds(CANCEL,witness)
        self.assertEqual(first['max_signed_bits'],(65,64))
        self.assertEqual(end['max_signed_bits'],(64,1))
    def test_fail_closed(self):
        with self.assertRaises(ValueError): Constraint('automatic','exact','unobserved','unobserved')
        with self.assertRaises(ValueError): sampled_bounds(X,((-100,100),)*4)
        with self.assertRaises(ValueError): sampled_bounds(Node('const',(Fraction(1,2),0)),((0,0),)*4)
        bad=Node('divide',(X,Y))
        with self.assertRaises(ValueError): build(bad,self.pure)

if __name__=='__main__': unittest.main()
