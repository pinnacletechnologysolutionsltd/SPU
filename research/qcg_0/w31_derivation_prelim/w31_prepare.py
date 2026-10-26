"""Independent literal §5 P programs. No registered workload at import time."""
from w31_arithmetic import Q
from w31_poly import Program

SEQUENTIAL = ('Horner', 'Bezier', 'TS', 'FD', 'PH', 'PHFD', 'C1', 'C2')
CELL_B = ('B-COMP', 'E-COMP', 'E-BEZ', 'E-TS', 'C1')
A_LISTS = ('X', 'Y', 'dx', 'dy', 'sg', 'SS', 'Nk')
B_LISTS = ('U', 'V', 'U1', 'V1', 'X', 'Y', 'SS')
COMPOSITES = ('cx', 'cy', 'cdx', 'cdy', 'csg', 'cSS')


def prepare(trace, arm, U, V, phi=None):
    """Return committed preparation only after the entire program succeeds."""
    bcell = phi is not None
    if arm not in (CELL_B if bcell else SEQUENTIAL):
        raise ValueError('unknown arm')
    p = {}
    for name, values in [('U', U), ('V', V)] + ([('phi', phi)] if bcell else []):
        p[name] = [trace.import_q(x, f'{arm}.P.import.{name}.{i}') for i, x in enumerate(values)]
    # Integer index/divisor constants checked before their first use in primitives;
    # all such integers are bounded by the declared polynomial lengths.
    def run(step, dest, method, *args):
        p[dest] = getattr(Program(trace, f'{arm}.P.{step}'), method)(*args)
    for step, dest, method, names in [
        ('P1','UU','pmul',('U','U')), ('P2','VV','pmul',('V','V')),
        ('P3','UV','pmul',('U','V')), ('P4','dx','padd',('UU','VV')),
        ('P5','dy','pscale2',('UV',)), ('P6','sg','padd',('UU','VV')),
        ('P7','X','pint',('dx',)), ('P8','Y','pint',('dy',)),
        ('P9','SS','pint',('sg',))]:
        args = [p[n] for n in names]
        if step == 'P4':
            args.append(True)
        run(step, dest, method, *args)
    limit = 9 if bcell or arm == 'C2' else 11 if arm in ('PH','PHFD','C1') else 15
    if limit >= 11:
        run('P10','U1','pder',p['U'])
        run('P11','V1','pder',p['V'])
    if limit == 15:
        run('P12','NP1','pmul',p['U'],p['V1'])
        run('P13','NP2','pmul',p['U1'],p['V'])
        run('P14','Np','padd',p['NP1'],p['NP2'],True)
        run('P15','Nk','pscale2',p['Np'])
    if bcell:
        run('P16','phi1','pder',p['phi'])
        for number, dest, source in [(17,'cx','X'),(18,'cy','Y'),(19,'cdxp','dx'),
                                     (20,'cdyp','dy'),(21,'csgp','sg'),(22,'cSS','SS')]:
            if arm == 'B-COMP' or (arm == 'C1' and number not in (17,18,22)):
                continue
            run(f'P{number}',dest,'pcomp',p[source],p['phi'])
        if arm.startswith('E-'):
            for number, dest in [(23,'cdx'),(24,'cdy'),(25,'csg')]:
                run(f'P{number}',dest,'pmul',p['phi1'],p[dest+'p'])
        if arm == 'E-BEZ':
            for number, name in enumerate(COMPOSITES, 26):
                run(f'P{number}', name, 'bern', p[name], name)
        names = (('X','Y','dx','dy','sg','SS','phi','phi1') if arm == 'B-COMP' else
                 ('phi','phi1','cx','cy','cSS') if arm == 'C1' else COMPOSITES+('phi1',))
    else:
        names = ('U','V','X','Y','SS') if arm == 'C2' else B_LISTS if limit == 11 else A_LISTS
        if arm == 'Bezier':
            for name in names:
                run('BERN.'+name,name,'bern',p[name])
        if arm in ('FD','PHFD','C1'):
            trace.import_q(Q(1,16),f'{arm}.P.import.delta.0')
            for name in names:
                run('FDINIT.'+name,name,'fdinit',p[name],Q(1,16))
    return {n:p[n] for n in names}
