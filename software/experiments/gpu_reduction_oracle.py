"""Independent exact-expression checks and required finite observation validator.

Does not import candidate rewriting, packet encoding or preparation arithmetic.
"""
from fractions import Fraction
from software.spu_gpu_eval.reference import pixel_decision as vertex_decision


class MissingObservation(ValueError):
    pass


def observe(row):
    if type(row) is not dict:
        raise MissingObservation('INVALID_OBSERVATION_RECORD')
    for name in ('coverage','covered_by','depths','winner','rgb'):
        if name not in row:
            raise MissingObservation('MISSING_REQUIRED_OBSERVABLE:' + name)
    covered, depths, winner, rgb = row['covered_by'],row['depths'],row['winner'],row['rgb']
    if type(covered) is not list or any(type(v) is not int or v not in (0,1) for v in covered):
        raise MissingObservation('INVALID_COVERED_BY')
    if covered != sorted(set(covered)) or type(depths) is not list or len(depths) != len(covered):
        raise MissingObservation('INVALID_DEPTH_INVENTORY')
    values = []
    for expected,depth in zip(covered,depths):
        if not isinstance(depth,dict) or 'triangle' not in depth or 'value' not in depth:
            raise MissingObservation('MISSING_REQUIRED_OBSERVABLE:depth')
        if (type(depth['triangle']) is not int or depth['triangle'] != expected
                or type(depth['value']) is not int or not -(1 << 55) <= depth['value'] < (1 << 55)):
            raise MissingObservation('INVALID_DEPTH')
        values.append((expected,depth['value']))
    coverage = 'background' if not covered else 'overlap' if len(covered)==2 else f'triangle{covered[0]}'
    if row['coverage'] != coverage or (winner is None) != (not covered):
        raise MissingObservation('INVALID_COVERAGE_OR_WINNER')
    if winner is not None and (type(winner) is not int or winner not in covered):
        raise MissingObservation('INVALID_WINNER')
    if type(rgb) is not list or len(rgb)!=3 or any(type(v) is not int or not 0<=v<=15 for v in rgb):
        raise MissingObservation('INVALID_RGB')
    return coverage,tuple(covered),tuple(values),winner,tuple(rgb)


def expression(view,x,y):
    depths = []
    for index,triangle in enumerate(view.decoded.triangles):
        weights = [a*x+b*y+c for a,b,c in triangle.edges]
        if all(w>=0 for w in weights):
            denominator = sum(weights)
            if denominator <= 0:
                raise ValueError('Nonpositive exact plane denominator')
            depths.append((index,Fraction(sum(w*z for w,z in zip(weights,triangle.z)),denominator)))
    winner = min(depths,key=lambda item:(item[1],item[0]))[0] if depths else None
    return (tuple(i for i,_ in depths),tuple(depths),winner,
            tuple(view.decoded.triangles[winner].rgb) if winner is not None else (0,0,0))


def exact_original(scene,x,y):
    row = vertex_decision(scene,x,y)
    depths = tuple((d['triangle'],Fraction(d['numerator'],d['denominator'])) for d in row['depths'])
    return tuple(row['covered_by']),depths,row['winner'],tuple(row['rgb'])


def exact_equal(scene,view,x,y):
    return exact_original(scene,x,y) == expression(view,x,y)


def plane_identity(scene,view):
    # Vertex and centroid samples are exact; coverage additionally needs positive
    # per-edge proportionality to independently reconstructed oriented edges.
    for index,triangle in enumerate(scene.triangles):
        vertices = triangle.vertices
        originals = []
        for i in range(3):
            p,q,r = vertices[i],vertices[(i+1)%3],vertices[(i+2)%3]
            edge = (q.y-p.y,p.x-q.x,(p.y-q.y)*p.x+(q.x-p.x)*p.y)
            if sum(v*w for v,w in zip(edge,(r.x,r.y,1))) < 0:
                edge = tuple(-v for v in edge)
            originals.append(edge)
        candidate = view.decoded.triangles[index]
        scales = []
        for original,reduced in zip(originals,candidate.edges):
            pivot = next(i for i,v in enumerate(original) if v)
            scale = Fraction(reduced[pivot],original[pivot])
            scales.append(scale)
            if scale <= 0 or any(Fraction(v)*scale != w for v,w in zip(original,reduced)):
                return False
        if len(set(scales)) != 1:
            return False
        for i,vertex in enumerate(vertices):
            weights = [a*vertex.x+b*vertex.y+c for a,b,c in candidate.edges]
            value = Fraction(sum(w*z for w,z in zip(weights,candidate.z)),sum(weights))
            if value != vertex.z:
                return False
    return True
