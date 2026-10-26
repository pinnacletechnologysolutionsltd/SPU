"""Private GCR-1 transformations; production packet/evaluator paths unchanged."""
from dataclasses import dataclass, asdict, replace
from functools import reduce
from math import gcd
from software.spu_gpu_eval.scene import parse_scene_data, PROFILE
from software.spu_gpu_eval.packet import compile_packet
from software.spu_gpu_eval.device_packet import decode_packet, DeviceScene
from software.spu_gpu_eval.device_arithmetic import prepare_depth


@dataclass(frozen=True)
class ConstantDepth:
    a_z: int
    b_z: int
    c_z: int
    frac_bits: int


@dataclass(frozen=True)
class SceneView:
    decoded: object
    depth: tuple


def cache_key(triangle, identities):
    return (triangle.edges, triangle.z, PROFILE, identities['rom_sha256'],
            identities['preparation_sha256'])


def check_depth(record):
    for name in ('a_z','b_z','c_z'):
        value = getattr(record,name)
        if type(value) is not int or not -(1 << 55) <= value < (1 << 55):
            raise ValueError('Prepared coefficient outside signed56')
    if type(record.frac_bits) is not int or not 0 <= record.frac_bits <= 127:
        raise ValueError('Prepared shift outside uint7')


def prepare(data, candidate, identities, cache=None):
    if candidate not in ('ORIGINAL','C1','C2','C3'):
        raise ValueError('Unknown private candidate')
    # Complete scene validation and packet admission precede any cache access.
    scene = parse_scene_data(data)
    decoded = decode_packet(compile_packet(scene))
    for triangle in decoded.triangles:
        if (sum(edge[2] for edge in triangle.edges) <= 0
                or any(type(z) is not int or not 0 <= z <= 65535 for z in triangle.z)):
            raise ValueError('Invalid depth/edge association')
    if cache is None:
        cache = {}
    triangles, depths, diagnostics = [], [], []
    counts = dict(validated_triangles=2,gcd_calls=0,cache_lookups=0,cache_hits=0,prepare_calls=0)
    eligible = False
    for index, triangle in enumerate(decoded.triangles):
        mode, reason, applied = 'ORIGINAL','INELIGIBLE',False
        if candidate == 'C1':
            counts['gcd_calls'] += 1
            common = reduce(gcd,(abs(v) for edge in triangle.edges for v in edge))
            if common > 1:
                triangle = replace(triangle,edges=tuple(tuple(v//common for v in edge)
                                                        for edge in triangle.edges))
                applied,reason = True,'COMMON_FACTOR'
        if candidate == 'C2' and len(set(triangle.z)) == 1:
            record = ConstantDepth(0,0,triangle.z[0],0)
            mode,reason,applied = 'CONSTANT_BYPASS','NOT_COMPUTED_CONSTANT_BYPASS',True
        elif candidate == 'C3':
            counts['cache_lookups'] += 1
            key = cache_key(triangle,identities)
            if key in cache:
                record = cache[key]
                counts['cache_hits'] += 1
                applied,reason = True,'IMMUTABLE_PREPARATION_HIT'
            else:
                record = prepare_depth(triangle)
                counts['prepare_calls'] += 1
                cache[key] = record
        else:
            record = prepare_depth(triangle)
            counts['prepare_calls'] += 1
        check_depth(record)
        metadata = None if mode == 'CONSTANT_BYPASS' else asdict(record)
        diagnostics.append(dict(triangle=index,mode=mode,reason=reason,applied=applied,
                                reciprocal_metadata=metadata))
        triangles.append(triangle)
        depths.append(record)
        eligible |= applied
    return scene,SceneView(DeviceScene(tuple(triangles)),tuple(depths)),dict(
        eligible=eligible,triangles=diagnostics,operations=counts)
