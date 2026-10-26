"""Five existing approaches; reports proposed-limit exceedances without changing limits."""
from ..lattice_symmetry.fixtures import simple_roots
from .meter import Meter
from .admission import admit, lattice
from .arrays import vector, row_copy, encode, decode
from . import spatial, matrices, signed, wire


def run(case, arm, trace=False):
    m = Meter(trace)
    m.allocate('dispatch_frame', 32+16*256+16*32)
    system, values, word = admit(m, case, arm)
    n = len(values)
    m.stage = 'input_wire'
    wire.measure(m, 'vector', system, values, 'wire/input')
    wire.measure(m, 'word', system, word, 'wire/word')
    m.release('wire/input'); m.release('wire/word')
    m.stage = 'setup'
    descriptor = None
    if arm == 'signed':
        descriptor = signed.build(m, word)
        m.stage = 'evaluation'
        out = signed.evaluate(m, descriptor, values)
        result_name = 'signed/output'
    else:
        roots = simple_roots(system)
        m.allocate('roots/table', 64+n*(64+n*64))
        for i in m.loop(n):
            for j in m.loop(n):
                m.charge('indexed_read'); m.charge('indexed_write')
        if arm == 'matrix':
            m.allocate('matrices/table', 64)
            table = []
            for i in m.loop(n):
                table.append(matrices.root_matrix(m, m.read(roots, i), 'generator/'+str(i)))
                m.charge('indexed_write')
            m.stage = 'construction'
            current = matrices.identity(m, 'matrix/identity', n)
            name = 'matrix/identity'
            for t in m.loop(len(word)):
                new = 'matrix/'+str(t)
                current = matrices.compose(m, m.read(table, m.read(word, t)), current, new)
                m.release(name); name = new
            descriptor = current
            m.stage = 'conversion'
            physical = encode(m, values, 'physical')
            m.stage = 'evaluation'
            output = matrices.evaluate(m, current, physical, 'rational/output')
            m.stage = 'conversion'
            out = decode(m, output, 'output')
            m.release('physical'); m.release('rational/output')
            result_name = 'output'
        else:
            if arm == 'surd':
                m.stage = 'setup_conversion'
                m.allocate('surds/table', 64)
                table = [encode(m, m.read(roots, i), 'surd/root/'+str(i), True) for i in m.loop(n)]
                m.charge('indexed_write', n)
                m.stage = 'conversion'
                current = encode(m, values, 'current', True)
            else:
                table = roots
                m.stage = 'construction'
                current = row_copy(m, values, vector(m, 'current', n))
            if arm == 'generator_word':
                m.stage = 'construction'
                descriptor = row_copy(m, word, vector(m, 'descriptor/word', len(word), 2 if n == 4 else 3))
            m.stage = 'evaluation' if arm != 'coordinates' else 'construction'
            output, name = spatial.evaluate(m, current, table, descriptor if descriptor is not None else word,
                                            'current', arm == 'surd')
            if arm == 'surd':
                m.stage = 'conversion'
                out = decode(m, output, 'output')
                m.release(name); result_name = 'output'
            else:
                out, result_name = output, name
    m.stage = 'commit'
    lattice(m, out, system)
    output_bytes = wire.measure(m, 'vector', system, out, 'wire/output')
    if descriptor is not None:
        kind = 'signed' if arm == 'signed' else 'matrix' if arm == 'matrix' else 'word'
        wire.measure(m, kind, system, descriptor, 'wire/descriptor')
        m.release('wire/descriptor')
    m.release('wire/output')
    names = list(m.live)  # observer ownership catalogue, not target data
    for i in m.loop(len(names)):
        name = m.read(names, i)
        if name != result_name:
            m.release(name)
    report = m.report()
    setup = sum(sum(v.values()) for k, v in m.stages.items() if k in ('setup', 'setup_conversion'))
    report.update(arm=arm, fixture=case.get('id', 'literal'), output=tuple(out), serialized_output_bytes=len(output_bytes),
                  setup_work=setup, case_work=report['work']-setup,
                  proposed_work_exceeded=report['work']-setup > m.profile.max_operations,
                  proposed_setup_exceeded=setup > m.profile.max_operations,
                  proposed_storage_exceeded=report['simultaneous_live_bits'] > m.profile.max_live_bits,
                  status='DIAGNOSTIC_DRY_COUNT_NOT_QUALIFICATION')
    return report, m.events
