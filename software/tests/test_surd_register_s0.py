"""Focused executable contract tests for the software-only S0 model."""
from fractions import Fraction as F
from itertools import product
import random
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from software.experiments import surd_register_exact as ex
from software.experiments import surd_register_model as model
from software.experiments.surd_register_rotation import rotate_pair
from software.experiments.surd_register_candidates import FixedScale, SharedBlock


def value(r): return (F(r.a,r.d),F(r.b,r.d))
def oracle(op,x,y=None):
    a,b=value(x)
    if op=='NEG': return -a,-b
    if op=='CONJ': return a,-b
    c,d=value(y)
    if op=='ADD': return a+c,b+d
    if op=='SUB': return a-c,b-d
    if op=='MUL': return a*c+3*b*d,a*d+b*c
    if op=='EQ': return (a==c and b==d)
    raise ValueError(op)


def ok(op,x,y=None,w=8,policy='EAGER'):
    out=model.execute(op,x,y,w,policy)
    assert out['status']=='OK',out
    return out['result']


def test_exhaustive_small():
    rows=[ex.R(a,b,d) for a,b,d in product(range(-2,3),range(-2,3),range(1,4))]
    for x,y in product(rows,repeat=2):
        for op in ('ADD','SUB','MUL'):
            assert value(ok(op,x,y))==oracle(op,x,y),(op,x,y)
        assert ok('EQ',x,y)==oracle('EQ',x,y)


def test_validation_and_import():
    assert not ex.valid(ex.R(True,0,1),8)
    assert not ex.valid(ex.R(0,0,0),8)
    assert ex.import_signed(6,-9,-3,8)==ex.R(-2,3,1)
    assert ex.import_signed(1,0,0,8) is None
    assert ex.normalize(ex.R(0,0,17))==ex.R(0,0,1)
    assert ex.normalize(ex.R(6,12,18))==ex.R(1,2,3)
    old=ex.R(1,2,3)
    assert model.load(old,ex.R(0,0,0),16)=={'status':'INVALID_INPUT','operation':'LOAD','destination':old}
    assert ex.R(1,2,3)!=ex.R(2,4,6)
    assert value(ex.R(1,2,3))==value(ex.R(2,4,6))


def test_policy_and_failures():
    x=ex.R(64,0,128); y=ex.R(64,0,128)
    eager=model.execute('ADD',x,y,8,'EAGER')
    rescue=model.execute('ADD',x,y,8,'FIT_RESCUE')
    boundary=model.execute('ADD',x,y,8,'BOUNDARY')
    assert eager['status']==rescue['status']=='OK'
    assert eager['result']==rescue['result']==ex.R(1,0,1)
    assert boundary['status']=='DESTINATION_OVERFLOW'
    # A lane-capacity failure after exact evaluation is distinct from a
    # deliberately injected pre-normalization accumulator failure.
    assert boundary['required_widths']['raw_result']['a']==9
    out=model.execute('ADD',ex.R(127,0,255),ex.R(127,0,255),8,'EAGER',limits={'accumulator':8})
    assert out['status']=='INTERMEDIATE_OVERFLOW' and out['result'] is None
    fallback=model.execute_with_fallback('ADD',x,y,8,'FIT_RESCUE',limits={'accumulator':8})
    assert fallback['narrow']['status']=='INTERMEDIATE_OVERFLOW'
    assert fallback['fallback']['executed']
    assert fallback['resident'] and fallback['fallback']['reentry_eligible']
    assert ok('ADD',ex.R(1,0,3),ex.R(-1,0,3),8,'BOUNDARY')==ex.R(0,0,1)


def test_full_width_bounds():
    m=ex.R(-(1<<63),-(1<<63),1)
    result,_=ex.raw('MUL',m,m)
    assert result.a==1<<128 and ex.sw(result.a)==130
    assert result.b==1<<127 and ex.sw(result.b)==129
    assert ex.intermediate_limits('MUL',64)=={'product':129,'accumulator':130,'den_product':128}
    assert ex.intermediate_limits('ADD',64)=={'product':128,'den_product':128,'accumulator':129}
    rot=rotate_pair({'x':ex.R(1,0,(1<<64)-1),'y':ex.R(0,1,(1<<64)-2)},'x','y','u','v',64,'BOUNDARY')
    assert (rot['status']=='INTERMEDIATE_OVERFLOW' or
            (rot['status']=='DESTINATION_OVERFLOW' and
             max(rot['required_widths']['x']['d'],rot['required_widths']['y']['d'])==129))
    assert rot['registers']=={'x':ex.R(1,0,(1<<64)-1),'y':ex.R(0,1,(1<<64)-2)}


def test_rotation_and_candidates():
    regs={'x':ex.R(1,2,3),'y':ex.R(2,-1,5)}
    r=rotate_pair(regs,'x','y','x','z',16,'EAGER')
    assert r['status']=='OK' and regs['x']==ex.R(1,2,3)
    assert rotate_pair(regs,'x','y','z','z',16,'EAGER')['status']=='INVALID_INPUT'
    fixed=FixedScale(3); x=fixed.load(ex.R(1,0,3))['value']
    assert fixed.apply('MUL',x,x)['reason']=='FIXED_SCALE_NOT_DIVISIBLE'
    wrong_denominator=ex.R(4,2,3)
    assert value(wrong_denominator)!=oracle('MUL',ex.R(1,1,3),ex.R(1,1,3))
    assert fixed.apply('MUL',(1,1),(1,1))['reason']=='FIXED_SCALE_NOT_DIVISIBLE'
    block=SharedBlock.load((ex.R(1,1,2),ex.R(1,0,3)))
    assert block.scale==6 and block.logical_bits==5*64 and block.resident
    start={'x':ex.R(2,1,5),'y':ex.R(-1,2,5)}; original=dict(start)
    for _ in range(6):
        step=rotate_pair(start,'x','y','x','y',16,'EAGER')
        assert step['status']=='OK'; start=step['registers']
    assert tuple(value(start[k]) for k in ('x','y'))==tuple(value(original[k]) for k in ('x','y'))


def test_seeded_boundaries():
    rng=random.Random(60061006)
    for w in (16,32,64):
        lo,hi=-(1<<(w-1)),(1<<(w-1))-1
        for _ in range(40):
            x=ex.R(rng.randint(lo,hi),rng.randint(lo,hi),rng.randint(1,(1<<w)-1))
            y=ex.R(rng.randint(lo,hi),rng.randint(lo,hi),rng.randint(1,(1<<w)-1))
            for op in ('ADD','SUB','MUL'):
                exact,_=ex.raw(op,x,y)
                assert value(exact)==oracle(op,x,y)
    assert ex.sw(-(1<<63))==64 and ex.sw((1<<63)-1)==64


if __name__=='__main__':
    test_exhaustive_small(); test_validation_and_import(); test_policy_and_failures()
    test_full_width_bounds(); test_rotation_and_candidates(); test_seeded_boundaries()
    print('PASS: S0 algebra, policies, bounds, rotation and scale candidates')
