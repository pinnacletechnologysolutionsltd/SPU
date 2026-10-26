"""§5 ordered sequential requests; caller provides an isolated state copy."""
from w31_arithmetic import Q
from w31_poly import Program


def evaluate(trace, arm, tape, state, k):
    if tape not in ('S1','S2','S3') or not 0 <= k <= 16:
        raise ValueError('invalid synthetic/registered route position')
    family = 'c' if arm == 'C2' else 'b' if arm in ('PH','PHFD','C1') else 'a'
    def prog(step):
        return Program(trace, f'{arm}.Q.q{k:02d}.{family}{step}')
    def scalar(step, method, *args):
        return prog(step).op(method, *args)
    def sub(step, x, y):
        return prog(step).sub(x, y)
    def read(step, name):
        p = prog(step)
        a = state[name]
        if arm in ('FD','PHFD','C1'):
            return state[name][0]
        if arm in ('TS','C2'):
            if k:
                state[name] = p.tshift(a, Q(1,16))
            return state[name][0]
        return (p.decas if arm == 'Bezier' else p.horner)(a,Q(k,16))
    # §5: selected FD tables advance before scalar sample arithmetic.
    if k and arm in ('FD','PHFD','C1'):
        selected = ([(1,'X'),(2,'Y'),(3,'dx'),(4,'dy'),(5,'sg'),(6,'SS'),(7,'Nk')]
                    if family=='a' else [(1,'U'),(2,'V'),(3,'U1'),(4,'V1'),(16,'X'),(17,'Y'),(18,'SS')])
        needed = (('X','Y') if tape=='S1' else ('X','Y','dx','dy','sg') if family=='a' and tape=='S2'
                  else ('U','V','X','Y') if tape=='S2' else tuple(n for _,n in selected))
        for step,name in selected:
            if name in needed:
                state[name] = prog(step).fdstep(state[name])
    v = {}
    if family == 'a':
        for step, name, out in [(1,'X','x'),(2,'Y','y'),(3,'dx','dx'),(4,'dy','dy'),
                                (5,'sg','sg'),(6,'SS','S'),(7,'Nk','Nk')]:
            if step <= (2 if tape == 'S1' else 5 if tape == 'S2' else 7):
                v[out] = read(step,name)
        if tape == 'S3':
            v['Dk'] = scalar(8,'mul',v['sg'],v['sg'])
        if tape != 'S1':
            v['ok'] = scalar(9,'sign',v['sg']) != 0
    elif family == 'b':
        if tape != 'S1':
            v['u'], v['v'] = read(1,'U'), read(2,'V')
            if tape == 'S3':
                v['u1'],v['v1'] = read(3,'U1'),read(4,'V1')
            uu = scalar(5,'mul',v['u'],v['u'])
            vv = scalar(6,'mul',v['v'],v['v'])
            uv = scalar(7,'mul',v['u'],v['v'])
            v['dx'] = sub(8,uu,vv)
            v['dy'] = scalar(9,'shift2',uv)
            v['sg'] = scalar(10,'add',uu,vv)
            if tape == 'S3':
                v['Dk'] = scalar(11,'mul',v['sg'],v['sg'])
                m1 = scalar(12,'mul',v['u'],v['v1'])
                m2 = scalar(13,'mul',v['u1'],v['v'])
                np = sub(14,m1,m2)
                v['Nk'] = scalar(15,'shift2',np)
        v['x'],v['y'] = read(16,'X'),read(17,'Y')
        if tape == 'S3':
            v['S'] = read(18,'SS')
        if tape != 'S1':
            v['ok'] = scalar(19,'sign',v['sg']) != 0
    else:
        for step, name in [(1,'U'),(2,'V'),(3,'X'),(4,'Y'),(5,'SS')]:
            if tape == 'S3' or name in (('X','Y') if tape == 'S1' else ('X','Y','SS')):
                read(step,name)
        v['x'],v['y'] = state['X'][0],state['Y'][0]
        if tape != 'S1':
            v['dx'],v['dy'],v['sg'] = [state[n][1] if len(state[n])>1 else Q(0) for n in ('X','Y','SS')]
        if tape == 'S3':
            v['S'] = state['SS'][0]
            v['Dk'] = scalar(7,'mul',v['sg'],v['sg'])
            m1 = scalar(8,'mul',state['U'][0],state['V'][1] if len(state['V'])>1 else Q(0))
            m2 = scalar(9,'mul',state['U'][1] if len(state['U'])>1 else Q(0),state['V'][0])
            v['Nk'] = scalar(11,'shift2',sub(10,m1,m2))
        if tape != 'S1':
            v['ok'] = scalar(12,'sign',v['sg']) != 0
    tangent_step = {'a':10,'b':20,'c':13}[family]
    if tape != 'S1':
        v['Tx'] = scalar(tangent_step,'div',v['dx'],v['sg'])
        v['Ty'] = scalar(tangent_step+1,'div',v['dy'],v['sg'])
    if tape == 'S3':
        # Increment ending at sample k is charged when this sample exists.
        v['increment_from_previous'] = sub(tangent_step+2,v['S'],state['_previous_S']) if k else None
        state['_previous_S'] = v['S']
    return {name:v[name] for name in ('x','y','dx','dy','sg','ok','Tx','Ty','S','Nk','Dk',
                                    'increment_from_previous') if name in v}
