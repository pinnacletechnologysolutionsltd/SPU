"""Software experiment only: fixed orthographic, two opaque triangles.

Q bounds [-9,9] are set by the retained extent-8 rational-depth witness.
Native and square buffers both have 7x7 sites; common output is [-2,2]^2.
All comparisons, including square sampling and nearest-site maps, are exact.
"""
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction as F

QMAX = 9
SITE_RADIUS = 3
AXIS = range(-SITE_RADIUS, SITE_RADIUS+1)
OUTPUT = [(x, y) for y in range(-2, 3) for x in range(-2, 3)]
SITES = [(x, y) for y in AXIS for x in AXIS]
# Conservative bounds over the declared input domain, not observed maxima.
R, Z = 4*QMAX, 4*QMAX
DMAX = 8*R*R
NAB, NC = 6*R*Z, 6*R*R*Z
HAB, HC = 2*DMAX*NAB, 2*DMAX*NC
ACC = 6*SITE_RADIUS*HAB+HC
SQUARE_REAL, SQUARE_IMAG = 3*SITE_RADIUS*HAB+HC, 3*SITE_RADIUS*HAB
CAPS = dict(projection=6*QMAX, edge_ab=2*R, edge_product=R*R,
            edge_c=2*R*R, area=DMAX, N_product=2*R*R*Z, N=NC,
            H_product=DMAX*NC, H=HC, step=3*HAB, seed=ACC,
            sample=ACC, row=ACC, sign_square=SQUARE_REAL**2,
            sign_scaled_square=3*SQUARE_IMAG**2,
            sign_gap=SQUARE_REAL**2+3*SQUARE_IMAG**2)


def signed_bits(n):
    return max(1, n.bit_length()+1 if n >= 0 else (~n).bit_length()+1)


class Meter:
    def __init__(self):
        self.ops, self.bits = Counter(), Counter()

    def record(self, tag, value):
        if tag in CAPS and abs(value) > CAPS[tag]:
            raise OverflowError(f'{tag}: {value} exceeds declared bound {CAPS[tag]}')
        self.bits[tag] = max(self.bits[tag], signed_bits(value))
        return value

    def add(self, a, b, tag):
        self.ops['add_sub'] += 1
        return self.record(tag, a+b)

    def mul(self, a, b, tag):
        self.ops['multiply'] += 1
        return self.record(tag, a*b)

    def sign(self, a):
        self.ops['sign'] += 1
        return (a > 0)-(a < 0)

    def surd_sign(self, a, b):
        # Exact sign(a+b*sqrt(3)); no float and no approximation.
        sa, sb = self.sign(a), self.sign(b)
        if not sa:
            return sb
        if not sb or sa == sb:
            return sa
        aa = self.mul(a, a, 'sign_square')
        bb = self.mul(b, b, 'sign_square')
        gap = self.add(aa, -self.mul(3, bb, 'sign_scaled_square'), 'sign_gap')
        return sa*self.sign(gap)


@dataclass(frozen=True)
class Triangle:
    ident: int
    colour: int
    vertices: tuple


@dataclass(frozen=True)
class PreparedTriangle:
    epoch: int
    raw: Triangle
    uv: tuple
    depths: tuple
    edges: tuple
    numerator: tuple
    denominator: int


@dataclass(frozen=True)
class Scene:
    epoch: int
    triangles: tuple
    order_field: tuple
    order_epoch: int


def project(q, m):
    a, b, c, d = q
    U = m.add(m.add(m.mul(2, b, 'projection'), -c, 'projection'), -d, 'projection')
    V = m.add(m.add(-b, m.mul(2, c, 'projection'), 'projection'), -d, 'projection')
    h = m.add(m.add(m.add(m.mul(3, a, 'projection'), -b, 'projection'), -c, 'projection'), -d, 'projection')
    return U, V, h


def prepare_triangle(raw, epoch, m):
    if raw.ident not in (0, 1) or not 0 <= raw.colour < 4096:
        raise ValueError('id/colour')
    for q in raw.vertices:
        if len(q) != 4 or any(abs(v) > QMAX for v in q) or sum(q) != 0:
            raise ValueError('coordinate range/exact sum')
    vertices = [project(q, m) for q in raw.vertices]

    def setup(v):
        e = []
        for p, q in ((v[1], v[2]), (v[2], v[0]), (v[0], v[1])):
            e.append((m.add(p[1], -q[1], 'edge_ab'),
                      m.add(q[0], -p[0], 'edge_ab'),
                      m.add(m.mul(p[0], q[1], 'edge_product'),
                            -m.mul(p[1], q[0], 'edge_product'), 'edge_c')))
        D = m.add(m.add(e[0][2], e[1][2], 'area'), e[2][2], 'area')
        return tuple(e), D

    ee, D = setup(vertices)
    if D == 0:
        raise ValueError('degenerate')
    if D < 0:
        vertices[1], vertices[2] = vertices[2], vertices[1]
        ee, D = setup(vertices)
    nn = []
    for col in range(3):
        products = [m.mul(v[2], e[col], 'N_product') for v, e in zip(vertices, ee)]
        nn.append(m.record(f'N{col}',m.add(m.add(products[0], products[1], 'N'), products[2], 'N')))
    return PreparedTriangle(epoch, raw, tuple((v[0], v[1]) for v in vertices),
                            tuple(v[2] for v in vertices), ee, tuple(nn), D)


def prepare_scene(triangles, epoch, m):
    p, q = triangles
    H = tuple(m.record(f'H{col}',m.add(m.mul(q.denominator, a, 'H_product'),
                    -m.mul(p.denominator, b, 'H_product'), 'H')
              ) for col,(a,b) in enumerate(zip(p.numerator,q.numerator)))
    return Scene(epoch, tuple(triangles), H, epoch)


def ownership(e):
    return e[0] > 0 or (e[0] == 0 and e[1] > 0)


def render(scene, square=False):
    if any(t.epoch != scene.epoch for t in scene.triangles) or scene.order_epoch != scene.epoch:
        raise ValueError('mixed prepared epoch')
    m = Meter()
    fields = (*scene.triangles[0].edges, *scene.triangles[1].edges, scene.order_field)
    rows, dx, dy = [], [], []
    for A, B, C in fields:
        dx.append(m.mul(3, A, 'step'))
        if square:
            ystep = m.add(-A, m.mul(2, B, 'step'), 'step')
            rows.append((m.add(m.mul(-3*SITE_RADIUS, A, 'seed'), C, 'seed'), m.mul(-SITE_RADIUS, ystep, 'seed')))
            dy.append(ystep)
        else:
            rows.append(m.add(m.add(m.mul(-3*SITE_RADIUS, A, 'seed'), m.mul(-3*SITE_RADIUS, B, 'seed'), 'seed'), C, 'seed'))
            dy.append(m.mul(3, B, 'step'))
    result = []
    for y in AXIS:
        acc = list(rows)
        for x in AXIS:
            signs = [m.surd_sign(*v) if square else m.sign(v) for v in acc]
            cov = [all(signs[k] > 0 or (signs[k] == 0 and ownership(fields[k]))
                       for k in range(base, base+3)) for base in (0, 3)]
            winner = 0 if cov[0] and (not cov[1] or signs[6] <= 0) else (1 if cov[1] else None)
            result.append((scene.epoch, winner, 0 if winner is None else scene.triangles[winner].raw.colour))
            if x != SITE_RADIUS:
                acc = [(m.add(v[0], step, 'sample'), v[1]) if square else m.add(v, step, 'sample')
                       for v, step in zip(acc, dx)]
        if y != SITE_RADIUS:
            rows = [(v[0], m.add(v[1], step, 'row')) if square else m.add(v, step, 'row')
                    for v, step in zip(rows, dy)]
    return tuple(result), m


def make_adapter(square=False):
    m, indices, displacements = Meter(), [], []
    for x, y in OUTPUT:
        best = None
        for index, (i, j) in enumerate(SITES):
            if square:
                a, b = (x-i)**2+(y-j)**2, 0
            else:
                terms = [m.mul(k,l,'map_poly') for k,l in ((x,x),(y,y),(i,i),(i,j),(j,j))]
                terms += [-m.mul(2,m.mul(x,i,'map_poly'),'map_poly'),-m.mul(x,j,'map_poly')]
                a = terms[0]
                for term in terms[1:]: a=m.add(a,term,'map_poly')
                b = -m.mul(y,j,'map_poly')
            if best is None or m.surd_sign(m.add(a,-best[0],'map_delta'),m.add(b,-best[1],'map_delta')) < 0:
                best, chosen = (a, b), index
        indices.append(chosen)
        displacements.append(best)
    return tuple(indices), tuple(displacements), m


def adapt(samples, indices, epoch):
    selected = tuple(samples[i] for i in indices)
    if any(s[0] != epoch for s in selected):
        raise ValueError('mixed adapter epoch')
    return selected


def square_threshold_render(scene):
    """Same exact predicates, compiled into monotone row cuts during preparation.

    A counter-baseline: removes irrational arithmetic from square sample-time
    execution too. No geometry rounding; 3-bit cuts 0..7 plus field direction.
    Compilation is measured separately and reusable until the scene changes.
    """
    if any(t.epoch!=scene.epoch for t in scene.triangles) or scene.order_epoch!=scene.epoch:
        raise ValueError('mixed prepared epoch')
    m=Meter()
    fields=(*scene.triangles[0].edges,*scene.triangles[1].edges,scene.order_field)
    table=[[] for _ in AXIS]
    for k,(A,B,C) in enumerate(fields):
        dx=m.mul(3,A,'step')
        a0=m.add(m.mul(-3*SITE_RADIUS,A,'seed'),C,'seed')
        db=m.add(-A,m.mul(2,B,'step'),'step')
        b=m.mul(-SITE_RADIUS,db,'seed')
        rising=A>=0 if k<6 else A<=0
        for row,y in enumerate(AXIS):
            low,high=0,len(AXIS)
            while low<high:
                mid=(low+high)//2  # bounded software setup search, not RTL
                a=m.add(a0,m.mul(dx,mid,'threshold_product'),'threshold_real')
                s=m.surd_sign(a,b)
                pred=(s>0 or (s==0 and ownership(fields[k]))) if k<6 else s<=0
                if pred==rising: high=mid
                else: low=mid+1
            table[row].append((low,rising))
            if y!=SITE_RADIUS: b=m.add(b,db,'row')
    pixels=[]
    for row,y in enumerate(AXIS):
        for index,x in enumerate(AXIS):
            flags=[index>=cut if rising else index<cut for cut,rising in table[row]]
            c0,c1=all(flags[:3]),all(flags[3:6])
            winner=0 if c0 and (not c1 or flags[6]) else (1 if c1 else None)
            pixels.append((scene.epoch,winner,0 if winner is None else scene.triangles[winner].raw.colour))
    return tuple(pixels),m,dict(threshold_comparisons=7*len(SITES),field_arithmetic=0,row_cut_reads=7*len(AXIS))


def exact_reference(scene, point, square=False):
    # Rational interval enclosure of sqrt(3), independently used for all signs.
    # 1.7320508075688772935274463415058723 < sqrt(3) < next decimal.
    lo = F(17320508075688772935274463415058723, 10**34)
    hi = lo + F(1, 10**34)
    assert lo*lo < 3 < hi*hi

    def sign(a, b=0):
        if a == b == 0:
            return 0
        low, high = sorted((a+b*lo, a+b*hi))
        if low > 0:
            return 1
        if high < 0:
            return -1
        raise AssertionError('reference interval insufficient; no guessed answer')

    x, y = point
    P = ((3*x, -y), (0, 2*y)) if square else ((3*x, 0), (3*y, 0))
    candidates = []
    for index, t in enumerate(scene.triangles):
        # Solve barycentric coordinates as Fractions, independent of prepared fields.
        vv = []
        for a,b,c,d in t.raw.vertices:
            xw,yw,zw = a+b-c-d,a-b+c-d,a-b-c+d
            vv.append(((2*xw-yw-zw)//2,(2*yw-xw-zw)//2,xw+yw+zw))
        if ((vv[1][0]-vv[0][0])*(vv[2][1]-vv[0][1])-
            (vv[2][0]-vv[0][0])*(vv[1][1]-vv[0][1])) < 0:
            vv[1],vv[2] = vv[2],vv[1]
        uv = tuple((u,v) for u,v,h in vv)
        depths = tuple(h for u,v,h in vv)
        (u0,v0),(u1,v1),(u2,v2) = uv
        d = (u1-u0)*(v2-v0)-(u2-u0)*(v1-v0)
        px, py = (P[0][0]-u0,P[0][1]), (P[1][0]-v0,P[1][1])
        l1 = tuple(F(px[k]*(v2-v0)-py[k]*(u2-u0),d) for k in (0,1))
        l2 = tuple(F(py[k]*(u1-u0)-px[k]*(v1-v0),d) for k in (0,1))
        lambdas = ((1-l1[0]-l2[0],-l1[1]-l2[1]),l1,l2)
        # At exact boundaries use the same declared infinitesimal, derived from vertices.
        accepted = True
        for l, p, q in zip(lambdas, (uv[1],uv[2],uv[0]), (uv[2],uv[0],uv[1])):
            s = sign(*l)
            include = p[1] > q[1] or (p[1] == q[1] and q[0] > p[0])
            accepted &= s > 0 or (s == 0 and include)
        if accepted:
            z = tuple(sum(l[k]*h for l,h in zip(lambdas,depths)) for k in (0,1))
            candidates.append((index,z))
    if not candidates:
        return scene.epoch, None, 0
    winner, depth = candidates[0]
    for index,z in candidates[1:]:
        if sign(z[0]-depth[0],z[1]-depth[1]) < 0:
            winner, depth = index,z
    return scene.epoch, winner, scene.triangles[winner].raw.colour
