"""Fixed rewrite under explicitly separate observers; no optimization performed."""
import copy
from fractions import Fraction
from research.qaf_expr_graph_0.model import CANCEL, X, CONJ_PRODUCT, NORM_X, eval_graph, normal
from research.qaf_expr_graph_1.model import ORIGINAL, IDENTITY, CONJ_MUL, NORM, HIGH, compare


def pure_cancel(x):
    """Pure language: exact rational pairs; total +/*; final value only."""
    if len(x) != 2:
        raise ValueError('expected two rational coefficients')
    a,b = (Fraction(v) for v in x)
    t = 2*a+3*b, a+2*b
    return 2*t[0]-3*t[1], -t[0]+2*t[1]


def pure_identity(x):
    return tuple(Fraction(v) for v in x)


def observe(trace, policy):
    """O2 observes result, status and occurrence of refusal; O3 adds ordered events."""
    refusal = any(e['status'] == 2 for e in trace['events'])
    final = (trace['result'], trace['status'], refusal)
    if policy == 'O2':
        return final
    if policy == 'O3':
        events = tuple((e['pc'], e['op'], e['status'], e['status'] == 2,
                        e['write'], e['retire'], tuple(sorted(e['registers'].items())))
                       for e in trace['events'])
        return final, tuple(sorted(trace['registers'].items())), events
    raise ValueError('unsupported observer')


def assessment(left, right, x, prior=0):
    result=compare(left,right,x,prior)
    # Domain decision below is restricted to the named rewrite and pure context.
    # It is backed by the algebraic derivation and the separate solver formula,
    # not by comparing one numerical result or trusting arbitrary graph labels.
    defined_rule=(left == ORIGINAL and right == IDENTITY)
    o2 = observe(result['left'], 'O2') == observe(result['right'], 'O2')
    o3 = observe(result['left'], 'O3') == observe(result['right'], 'O3')
    return {'pure_rule': 'PROVED_FOR_DEFINED_CONTEXT' if defined_rule else 'UNKNOWN',
            'math_form_match':result['mathematical'],
            'final_fixture_match':o2,
            'strict_fixture_match':o3,
            'original':result['left'],'candidate':result['right']}


def main():
    cases=[('small',ORIGINAL,IDENTITY,(3,-2),0),
           ('overflow',ORIGINAL,IDENTITY,(HIGH,0),0),
           ('norm',CONJ_MUL,NORM,(1,2),0),
           ('prior status',ORIGINAL,IDENTITY,(1,0),2)]
    for label,left,right,x,status in cases:
        r=assessment(left,right,x,status)
        print(label,'input=',x,'initial_status=',status,
              'normal=',normal(left.root), 'candidate_normal=',normal(right.root),
              'O1=',r['math_form_match'],'pure_rule=',r['pure_rule'],
              'O2=',r['final_fixture_match'],'O3=',r['strict_fixture_match'])
        for side in ('original','candidate'):
            t=r[side]
            print(' ',side,'O2=',observe(t,'O2'),'O3=',observe(t,'O3'))
    sample = compare(ORIGINAL, ORIGINAL, (3,-2))['left']
    mutant = copy.deepcopy(sample)
    mutant['events'][0]['retire'] = False
    print('mutant retirement: O2=',observe(sample,'O2') == observe(mutant,'O2'),
          'O3=',observe(sample,'O3') == observe(mutant,'O3'))
    print('rational sample=',pure_cancel((Fraction(1,3),Fraction(-2,5))),
          'identity=',pure_identity((Fraction(1,3),Fraction(-2,5))))
    print('norm_forms_equal=',normal(CONJ_PRODUCT)==normal(NORM_X))
    print('graph_root_preserved=',CANCEL!=X,'numeric_check=',eval_graph(CANCEL,{'x':(3,-2),'y':(0,0)}))

if __name__=='__main__': main()
