"""Fixed command programs (<= 32 commands each). Expected results live in test_rel1.py, not here."""
from fractions import Fraction as F


def M(a=0, b=0, c=0, diag=(1, 1, 1)):
    a, b, c = F(a), F(b), F(c)
    return ((diag[0], a, b), (a, diag[1], c), (b, c, diag[2]))


MA, MB = M(F(3, 5)), M(F(4, 5))
MHALF = M(F(1, 2))                       # needs sqrt(3): not in Q, in Q(sqrt3)
M2 = M(F(1, 3), F(1, 4), F(1, 5))        # relational-only (no coordinates in Q, Q(sqrt3), Q(sqrt5))
STEPS = [F(11, 61), F(9, 41), F(7, 25), F(12, 37), F(5, 13), F(8, 17), F(20, 29), F(3, 5)]   # Q-materialisable

P1 = (
    ('OBSERVE', 0), ('VALIDATE', 0), ('QUERY', 0, 'equilibrium'), ('OBSERVE', 0),
    ('TRANSFORM', MA), ('OBSERVE', 1), ('REUSE', 0, 'strut_lengths'), ('REUSE', 0, 'equilibrium'),
    ('REUSE', 0, 'realisable'), ('REUSE', 0, 'stability'), ('QUERY', 1, 'stability'),
    ('VALIDATE', 1), ('OBSERVE', 1), ('MOVE', (0, 1), (0, 0, 1)), ('QUERY', 2, 'equilibrium'),
    ('QUERY', 2, 'stability'), ('VALIDATE', 2), ('REUSE', 1, 'equilibrium'),
    ('REUSE', 1, 'strut_lengths'), ('OBSERVE', 1), ('TRANSFORM', MB), ('REUSE', 1, 'equilibrium'),
    ('TRANSFORM', M()), ('REUSE', 0, 'stability'), ('REUSE', 0, 'equilibrium'),
    ('REUSE', 0, 'realisable'), ('REUSE', 0, 'strut_lengths'), ('OBSERVE', 4),
    ('TRANSFORM', M(F(6, 5))), ('TRANSFORM', M(F(3, 5), diag=(F(9, 8), 1, 1))),
)
P2 = (('TRANSFORM', MHALF), ('VALIDATE', 1), ('QUERY', 1, 'stability'), ('OBSERVE', 1),
      ('TRANSFORM', M2), ('QUERY', 2, 'equilibrium'), ('QUERY', 2, 'stability'), ('OBSERVE', 2))
# P3 (run with lemma=True): six metric transitions, all four certificates carried, ONE observation.
P3 = (('VALIDATE', 0),) + tuple(
    c for k, m in enumerate(STEPS[2:]) for c in
    (('TRANSFORM', M(m)),) + tuple(('REUSE', k, n) for n in
                                   ('realisable', 'strut_lengths', 'equilibrium', 'stability'))) + (('OBSERVE', 6),)


def execute(machine, program):
    assert len(program) <= 32
    return tuple(machine.step(c) for c in program)
