import unittest
from dataclasses import replace
from research.qaf_expr_graph_0.model import Node,X,CANCEL,CONJ_PRODUCT,NORM_X
from research.qaf_ir_0.model import Constraint,build
from research.qaf_ir_1.checker import check,check_equal

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.c=Constraint('strict','toy-signed64','observable','observable')
        self.domain=((-2,2),(-2,2),(0,0),(0,0))
        self.r=build(CANCEL,self.c,self.domain)
    def test_verified_claims(self):
        r=check(self.r,CANCEL,self.domain)
        self.assertEqual(r,{'normal_form':'PASS','structural_dependencies':'PASS','mathematical_dependencies':'PASS','bounds':'PASS','execution_assumptions':'UNVERIFIED','rewrite_eligibility':'UNKNOWN'})
        self.assertEqual(check_equal(self.r,build(X,self.c),CANCEL,X),'PASS_EQUAL_FORM')
        self.assertEqual(check_equal(build(CONJ_PRODUCT,self.c),build(NORM_X,self.c),CONJ_PRODUCT,NORM_X),'PASS_EQUAL_FORM')
    def test_forged_normal_form_and_equality(self):
        root=Node('conj',(X,)); conj=build(root,self.c)
        fake=replace(conj,canonical=build(X,self.c).canonical)
        self.assertEqual(check(fake,root)['normal_form'],'FAIL')
        self.assertEqual(check_equal(fake,build(X,self.c),root,X),'FAIL_NOT_EQUAL_FORM')
    def test_false_dependency(self):
        self.assertEqual(check(replace(self.r,syntax_deps=frozenset()),CANCEL,self.domain)['structural_dependencies'],'FAIL')
        root=Node('mul',(X,Node('const',(0,0)))); zero=build(root,self.c)
        self.assertEqual(check(replace(zero,value_deps=frozenset({'x'})),root)['mathematical_dependencies'],'FAIL')
    def test_altered_bound_and_domain(self):
        e=self.r.bounds
        self.assertEqual(check(replace(self.r,bounds=replace(e,bounds=((-1,1),(-2,2)))),CANCEL,self.domain)['bounds'],'FAIL')
        self.assertEqual(check(replace(self.r,bounds=replace(e,max_signed_bits=(2,3))),CANCEL,self.domain)['bounds'],'FAIL')
        self.assertEqual(check(replace(self.r,bounds=replace(e,samples=24)),CANCEL,self.domain)['bounds'],'FAIL')
        changed=replace(e,domain=((-1,1),(-1,1),(0,0),(0,0)))
        self.assertEqual(check(replace(self.r,bounds=changed),CANCEL,self.domain)['bounds'],'FAIL_DOMAIN_MISMATCH')
        huge=replace(e,domain=((-100,100),)*4)
        self.assertEqual(check(replace(self.r,bounds=huge),CANCEL,huge.domain)['claims'],'UNKNOWN_UNSUPPORTED')
        self.assertEqual(check(self.r,CANCEL)['bounds'],'UNKNOWN_DOMAIN_SCOPE')
    def test_unknown_effects_and_unsupported(self):
        u=replace(self.r,constraint=Constraint('mathematical','exact','unobserved','unobserved'))
        self.assertEqual(check(u,CANCEL,self.domain)['execution_assumptions'],'UNVERIFIED')
        self.assertEqual(check(u,CANCEL,self.domain)['rewrite_eligibility'],'UNKNOWN')
        root=Node('divide',(X,X)); fake=replace(self.r,origin=root)
        self.assertEqual(check(fake,root,self.domain)['claims'],'UNKNOWN_UNSUPPORTED')
        self.assertEqual(check_equal(fake,self.r,root,CANCEL),'UNKNOWN_UNSUPPORTED')
        self.assertEqual(check(replace(self.r,bounds=None),CANCEL)['bounds'],'NOT_SUPPLIED')
        self.assertEqual(check(self.r)['claims'],'UNKNOWN_ORIGIN_SCOPE')
        self.assertEqual(check(replace(self.r,origin=X),CANCEL,self.domain)['claims'],'FAIL_ORIGIN_MISMATCH')
        self.assertEqual(check_equal(self.r,build(X,self.c)),'UNKNOWN_ORIGIN_SCOPE')
        self.assertEqual(check_equal(replace(self.r,origin=X),build(X,self.c),CANCEL,X),'FAIL_ORIGIN_MISMATCH')

if __name__=='__main__': unittest.main()
