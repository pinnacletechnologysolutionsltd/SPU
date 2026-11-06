from research.qaf_expr_graph_0.model import X, CANCEL, CONJ_PRODUCT, NORM_X, FACTOR_ORIGINAL, FACTOR, Node
from research.qaf_ir_0.model import Constraint,build,compare,sampled_bounds

unknown=Constraint('unknown','unknown','unknown','unknown')
strict=Constraint('strict','toy-signed64','observable','observable')
for label,node in [('x',X),('cancel',CANCEL),('norm product',CONJ_PRODUCT),
                   ('norm',NORM_X),('factored original',FACTOR_ORIGINAL),('factored',FACTOR),
                   ('x times zero',Node('mul',(X,Node('const',(0,0)))) )]:
    r=build(node,unknown)
    print(label,'structural_dependencies=',sorted(r.syntax_deps),
          'value_dependencies=',sorted(r.value_deps),'canonical=',r.canonical,
          'constraint=',r.constraint)
print('cancel vs x, unknown=',compare(build(CANCEL,unknown),build(X,unknown)))
print('cancel vs x, strict=',compare(build(CANCEL,strict),build(X,strict)))
bounded=build(CANCEL,strict,((-2,2),(-2,2),(0,0),(0,0)))
print('cancel single record=',bounded)
m=(1<<63)-1; dom=((m,m),(0,0),(0,0),(0,0))
print('overflow first=',sampled_bounds(CANCEL.args[0],dom))
print('overflow final=',sampled_bounds(CANCEL,dom))
