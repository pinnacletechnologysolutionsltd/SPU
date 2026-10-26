"""C0 storage adapter for the maintained sample_robot_vector / joint_60 input."""
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'software'))
from lib import rational_robotics as robot
from software.experiments import spu_lossless_storage as storage

PREFIX = b'C0\x00\x03\x01'  # schema 0; axis 3; one ordered block
MODES = {0: 'fixed_i64', 2: 'packed', 3: 'factored', 4: 'maintained_json', 5: 'automatic'}


def original():
    return robot.sample_robot_vector(), robot.joint_60(axis_id=3)


def flatten(inputs):
    vector, joint = inputs
    if joint.axis_id != 3:
        raise ValueError('C0 only supports the retained axis-3 workload')
    values = []
    for surd in (*vector.components(), joint.f, joint.g, joint.h):
        for coefficient in (surd.p, surd.q):
            values.extend((coefficient.numerator, coefficient.denominator))
    return storage.checked(values)


def reconstruct(values):
    values = storage.checked(values)
    if len(values) != 28:
        raise ValueError('C0 requires 28 numerator/denominator integers')
    fractions = []
    for n, d in zip(values[::2], values[1::2]):
        if d <= 0 or math.gcd(abs(n), d) != 1:
            raise ValueError('noncanonical or nonpositive rational denominator')
        fractions.append(Fraction(n, d))
    surds = [robot.Q3(*fractions[i:i+2]) for i in range(0, 14, 2)]
    return robot.QuadrayQ(*surds[:4]), robot.CirculantJoint(3, *surds[4:])


def kernel(inputs):
    vector, joint = inputs
    rotated = robot.apply_joint(vector, joint)
    return rotated, robot.apply_inverse_joint(rotated, joint)


def maintained_value(inputs):
    vector, joint = inputs
    return {'vector': robot.quadray_to_trace_value(vector),
            'joint': {name: robot.q3_to_trace_value(getattr(joint, name)) for name in ('f', 'g', 'h')}}


def json_payload(inputs):
    return json.dumps(maintained_value(inputs), separators=(',', ':'), ensure_ascii=True).encode('ascii')


def candidate_streams(values):
    values = storage.checked(values)
    streams, exclusions = {}, {}
    for mode in (0, 2, 3):
        try:
            streams[mode] = PREFIX + storage.encode(values, mode)
        except ValueError as error:
            exclusions[MODES[mode]] = str(error)
    return streams, exclusions


def encode(inputs, mode):
    values = flatten(inputs)
    if mode == 4:
        payload = json_payload(inputs)
        return PREFIX + b'\x04' + len(payload).to_bytes(4, 'little') + payload
    if mode not in (0, 2, 3, 5):
        raise ValueError('unsupported C0 mode')
    if mode != 5:
        return PREFIX + storage.encode(values, mode)
    streams, _ = candidate_streams(values)
    if mode == 5:
        mode = min(streams, key=lambda m: (len(streams[m]), m))
    if mode not in streams:
        raise ValueError('unsupported factor')
    return streams[mode]


def decode(stream):
    if not isinstance(stream, bytes) or not stream.startswith(PREFIX) or len(stream) < 10:
        raise ValueError('invalid C0 schema/axis/block count')
    mode, body = stream[5], stream[5:]
    if mode in (0, 2, 3):
        return reconstruct(storage.decode(body))
    if mode != 4 or int.from_bytes(body[1:5], 'little') != len(body)-5:
        raise ValueError('invalid JSON tag or length')
    try:
        value = json.loads(body[5:])
        surds = []
        for group, names in ((value['vector'], ('a', 'b', 'c', 'd')), (value['joint'], ('f', 'g', 'h'))):
            for name in names:
                surds.append(robot.Q3(*(Fraction(group[name][part]) for part in ('p', 'q'))))
        inputs = robot.QuadrayQ(*surds[:4]), robot.CirculantJoint(3, *surds[4:])
        if encode(inputs, 4) != stream:
            raise ValueError('noncanonical JSON')
        return reconstruct(flatten(inputs))
    except (KeyError, TypeError, ZeroDivisionError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid maintained JSON') from error


def independent_sizes(values):
    """Complete lengths derived without using the candidate encoder."""
    values = storage.checked(values)
    unsigned = [2*v if v >= 0 else -2*v-1 for v in values]
    width = max((u.bit_length() for u in unsigned), default=0)
    packed = 5 + 1 + 4 + (1 if values else 0) + (len(values)*width+7)//8
    g = math.gcd(*values) if values else 0
    g = abs(g) or 1
    reduced = [v//g for v in values]
    reduced_width = max(((2*v if v >= 0 else -2*v-1).bit_length() for v in reduced), default=0)
    factored = 5 + 1 + 8 + 4 + (1 if values else 0) + (len(values)*reduced_width+7)//8
    return {0: 10+8*len(values), 2: packed, 3: factored}
