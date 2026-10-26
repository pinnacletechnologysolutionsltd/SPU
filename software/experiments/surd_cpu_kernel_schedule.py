"""Complete retained CPU schedule, including CPU inverse generation and transfers."""
import json
from fractions import Fraction
from pathlib import Path
from software.experiments.surd_cpu_stream import Stream, canonical
from software.lib import rational_robotics as ref
from software.experiments.surd_register_workload import from_q3

CORPUS = Path('build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json')


def pair(row):
    return ref.Q3(Fraction(row[0],row[1]),Fraction(row[2],row[3]))


def tuple_of(q):
    r = from_q3(q)
    return r.a, r.b, r.d


def rotate(stream, joint=None, cached_joint=None):
    orders = ((0,2,1),(1,0,2),(2,1,0))
    for out, order in zip((4,5,6), orders):
        for term, (coefficient, source) in enumerate(zip(order,(1,2,3))):
            stream.load(7, joint[coefficient] if joint else None,
                        cached_joint=cached_joint, component=coefficient)
            stream.command('SMUL', [f'S{out if term==0 else 7}', 'S7', f'S{source}'])
            if term:
                stream.command('SADD', [f'S{out}', f'S{out}', 'S7'])
    stream.command('SNORM', ['S0','S0'], tag=1)
    for dst, src in zip((1,2,3),(4,5,6)):
        stream.command('SNORM', [f'S{dst}',f'S{src}'], tag=1)


def kernels(stream):
    data = json.loads(CORPUS.read_text())
    records = {}
    for length, names in data['chains'].items():
        for index, row in enumerate(data['records']):
            group = len(records)
            stream.group = group
            stream.reset()
            stream.row(9)
            joints = [tuple(tuple_of(pair(q)) for q in data['catalog'][name]) for name in names]
            for n, joint in enumerate(joints):
                for register, coefficient in enumerate(joint):
                    stream.load(register, coefficient)
                for dst, lhs, rhs, other_lhs, other_rhs in ((3,0,0,1,2),(4,2,2,0,1),(5,1,1,0,2)):
                    stream.command('SMUL',[f'S{dst}',f'S{lhs}',f'S{rhs}'])
                    stream.command('SMUL',['S6',f'S{other_lhs}',f'S{other_rhs}'])
                    stream.command('SSUB',[f'S{dst}',f'S{dst}','S6'])
                for coefficient, register in enumerate((3,4,5)):
                    stream.read_tuple(register,n*18+coefficient*6)
            vector = ref.QuadrayQ(*(pair(q) for q in row['vector']))
            for register, component in enumerate(vector.components()):
                stream.load(register,tuple_of(component))
            for joint in joints:
                rotate(stream,joint=joint)
            forward = tuple(stream.bank[:4])
            for register in range(4):
                stream.read_tuple(register)
            for n in reversed(range(len(joints))):
                rotate(stream,cached_joint=n)
            recovered = tuple(stream.bank[:4])
            for register in range(4):
                stream.read_tuple(register)
            js = tuple(ref.CirculantJoint(3,*(pair(q) for q in data['catalog'][name])) for name in names)
            expected = ref.fk_chain(vector,js)
            back = ref.inverse_fk_chain(expected,js)
            if forward != tuple(canonical(tuple_of(q)) for q in expected.components()):
                raise ValueError('retained forward reference mismatch')
            if recovered != tuple(canonical(tuple_of(q)) for q in back.components()):
                raise ValueError('retained recovery reference mismatch')
            stream.row(10)
            records[str(group)] = {'length':int(length),'index':index,'name':row['name'],
                                  'forward':forward,'recovered':recovered}
    return records
