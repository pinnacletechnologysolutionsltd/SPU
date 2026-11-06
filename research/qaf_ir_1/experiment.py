from dataclasses import replace
from research.qaf_expr_graph_0.model import Node,X,CANCEL
from research.qaf_ir_0.model import Constraint,build
from research.qaf_ir_1.checker import check,check_equal

c=Constraint('strict','toy-signed64','observable','observable')
domain=((-2,2),(-2,2),(0,0),(0,0))
r=build(CANCEL,c,domain)
other=build(X,c)
print('valid',check(r,CANCEL,domain))
print('equality',check_equal(r,other,CANCEL,X))
print('wrong bounds',check(replace(r,bounds=replace(r.bounds,bounds=((-1,1),(-2,2)))),CANCEL,domain))
print('wrong dependency',check(replace(r,syntax_deps=frozenset()),CANCEL,domain))
root=Node('conj',(X,)); conj=build(root,c)
fake=replace(conj,canonical=other.canonical)
print('forged equality form',check(fake,root),check_equal(fake,other,root,X))
print('domain not specified',check(r,CANCEL))
print('origin mismatch',check(replace(r,origin=X),CANCEL,domain))
print('unsupported',check(replace(r,origin=Node('divide',(X,X))),Node('divide',(X,X)),domain))
