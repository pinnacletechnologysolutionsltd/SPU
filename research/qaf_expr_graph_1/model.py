"""Small explicit observer over mathematical DAGs; not a Gen-1 interpreter."""
from dataclasses import dataclass
from research.qaf_expr_graph_0.model import Node, X, U, V, CANCEL, CONJ_PRODUCT, NORM_X, normal

LOW, HIGH = -(1 << 63), (1 << 63) - 1
OK, OVERFLOW = 0, 2

@dataclass(frozen=True)
class Instruction:
    op: str
    dst: str
    src: tuple
    expression: Node

@dataclass(frozen=True)
class Program:
    root: Node
    instructions: tuple
    result: str

# Explicit source-level designs, not an automatic graph lowerer. These operations
# have toy semantics; CONJ and NORM are not claimed as Gen-1 instructions.
FIRST = CANCEL.args[0]
ORIGINAL = Program(CANCEL, (
    Instruction('MUL','r0',('r0','u'), FIRST),
    Instruction('MUL','r0',('r0','v'), CANCEL)), 'r0')
IDENTITY = Program(X, (), 'r0')
CONJ = CONJ_PRODUCT.args[1]
CONJ_MUL = Program(CONJ_PRODUCT, (
    Instruction('CONJ','r1',('r0',),CONJ),
    Instruction('MUL','r0',('r0','r1'),CONJ_PRODUCT)), 'r0')
NORM = Program(NORM_X, (Instruction('NORM','r0',('r0',),NORM_X),), 'r0')


def bits(n):
    return (n if n >= 0 else ~n).bit_length() + 1


def calculate(op, args):
    a,b = args[0]
    if op == 'CONJ': return a,-b
    if op == 'NORM': return a*a-3*b*b,0
    if op == 'MUL':
        c,d = args[1]
        return a*c+3*b*d,a*d+b*c
    raise ValueError('unsupported operation')


def execute(program, x, initial_status=OK):
    """One retirement per issue, stop at refusal; initial regs preloaded.

    Coefficients are signed-64; denom=1. Scratch math is unbounded. Overflow
    refuses atomically, sets status=2, retires, and stops this toy controller.
    These are explicit model assumptions, not generally qualified CPU behavior.
    """
    if len(x) != 2 or any(type(v) is not int or not LOW <= v <= HIGH for v in x):
        raise ValueError('invalid initial value')
    if initial_status not in (OK, OVERFLOW): raise ValueError('invalid status')
    registers={'r0':tuple(x), 'r1':None, 'u':(2,1), 'v':(2,-1)}
    events=[]
    status=initial_status
    for pc, ins in enumerate(program.instructions):
        vals=tuple(registers[s] for s in ins.src)
        if any(v is None for v in vals): raise ValueError('uninitialized operand')
        exact=calculate(ins.op,vals)
        fits=all(LOW <= x <= HIGH for x in exact)
        status=OK if fits else OVERFLOW
        if fits: registers[ins.dst]=exact
        events.append({'pc':pc,'op':ins.op,'source_graph_op':ins.expression.op,
                       'exact':exact,'bits':tuple(map(bits,exact)),
                       'status':status,'write':(ins.dst,exact) if fits else None,
                       'retire':True,'registers':dict(registers)})
        if not fits: break
    return {'status':status,'result':registers[program.result],
            'registers':registers,'events':events}


def compare(left, right, x, initial_status=OK):
    """Three explicitly different observers; no authorization of real rewrites."""
    mathematical=normal(left.root)==normal(right.root)
    a,b=execute(left,x,initial_status),execute(right,x,initial_status)
    # Final-only observer deliberately ignores all other registers and events.
    final=(a['result'],a['status']) == (b['result'],b['status'])
    # Strict observer sees ordered write/retire/status and all bank values,
    # but not our explanatory exact scratch values or operation labels.
    def observable(trace):
        return [(e['status'],e['write'],e['retire'],e['registers']) for e in trace]
    strict=(a['status'],a['registers'],observable(a['events'])) == (b['status'],b['registers'],observable(b['events']))
    return {'mathematical':mathematical,'final_value_status':final,
            'strict_trace':strict,
            'permitted_in_fixture':{'math_only':mathematical,
                'final_value_status':mathematical and final,
                'strict_trace':mathematical and strict},'left':a,'right':b}
