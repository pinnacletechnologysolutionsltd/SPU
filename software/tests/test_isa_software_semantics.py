"""Finite software subset: exact results, faults, warm reload and cold reset."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software import spu_vm as vm
from isa_semantics_oracle import MIN32, MAX32, add, subtract, multiply, rotc, seed, fits


def python_state(word, scalar, quadray, mode):
    core = vm.SPUCore(verbose=False)
    core.load([word])
    core.regs = [vm.RationalSurd(a, b, pell_step=None if ps < 0 else ps) for a, b, ps in scalar]
    core.qregs = [vm.QuadrayVector(*(vm.RationalSurd(*r) for r in q)) for q in quadray]
    core.call_stack, core.snap_failures = [19, 23], 2
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            core.step()
        except ValueError:
            assert core.fault_kind
        if mode == 'reload':
            core.load([0xff << 56])
        if mode == 'cold':
            core = vm.SPUCore(verbose=False)
        if mode == 'pell9':
            core = vm.SPUCore(verbose=False)
            core.load([0x0001000001000000] + [0x0401000000000000]*9)
            core.run()
    status = (core.fault_kind or 'OK', core.pc, int(core.halted), core.step_count,
              core.snap_failures, *core.call_stack)
    scalars = [(r.a, r.b, -1 if r.pell_step is None else r.pell_step) for r in core.regs]
    vectors = [[(r.a, r.b) for r in q.components()] for q in core.qregs]
    return status, scalars, vectors


def cpp_state(binary, word, scalar, quadray, mode):
    fields = [mode, f'{word:x}'] + [str(v) for r in scalar for v in r]
    fields += [str(v) for q in quadray for r in q for v in r]
    run = subprocess.run([str(binary)], input=' '.join(fields), text=True,
                         capture_output=True, check=True)
    rows = [line.split() for line in run.stdout.splitlines()]
    status = next(r for r in rows if r[0] == 'STATUS')
    scalars = [tuple(map(int, r[2:])) for r in rows if r[0] == 'R']
    vectors = [[tuple(map(int, r[j:j+2])) for j in range(2, 10, 2)] for r in rows if r[0] == 'Q']
    return (status[1], *map(int, status[2:])), scalars, vectors


def main():
    records = []
    with tempfile.TemporaryDirectory(prefix='spu_semantics_') as directory:
        binary = Path(directory)/'vm'
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-fsanitize=undefined',
                        '-fno-sanitize-recover=undefined', str(ROOT/'software/tests/isa_semantics_cpp.cpp'),
                        '-o', str(binary)], check=True)

        def check(name, word, scalar, quadray, expected, fault='', mode='step', python_fault=False):
            c = cpp_state(binary, word, scalar, quadray, mode)
            p = python_state(word, scalar, quadray, mode)
            if fault:
                assert c == ((fault, 0, 1, 0, 2, 19, 23), scalar, quadray), (name, c)
                if python_fault:
                    assert p == c, (name, p, c)
                else:
                    assert p[1:] == expected, (name, p, expected)
            else:
                assert c == p and c[1:] == expected, (name, c, p, expected)
                wanted_status = {
                    'halt': ('OK', 1, 1, 1, 2, 19, 23),
                    'snap-extreme-proof': ('OK', 1, 0, 1, 3, 19, 23),
                    'reload': ('OK', 0, 0, 0, 2, 19, 23),
                    'cold': ('OK', 0, 0, 0, 0),
                }.get(name, ('OK', 1, 0, 1, 2, 19, 23))
                assert c[0] == wanted_status, (name, c[0], wanted_status)
            records.append({'case': name, 'classification': 'unsupported' if fault and not python_fault else 'matching',
                            'cpp_fault': fault, 'python_fault': p[0][0]})

        for opcode, operation in [(1, add), (2, subtract), (3, multiply)]:
            for lhs, rhs in [((7, -4), (-2, 3)), ((MAX32, MIN32), (0, 0)),
                             ((MAX32, 0), (1, 0)), ((MIN32, 0), (-1, 0)),
                             ((MAX32, MAX32), (MAX32, MIN32))]:
                scalar, q = seed(); scalar[1] = (*lhs, -1); scalar[2] = (*rhs, -1)
                wanted = operation(lhs, rhs); out = copy.deepcopy(scalar); out[1] = (*wanted, -1)
                check(f'arithmetic-{opcode}-{lhs}-{rhs}', opcode << 56 | 1 << 48 | 2 << 40,
                      scalar, q, (out, q), '' if fits(wanted) else 'OVERFLOW')
        for angle in range(6):
            for value in (1, -1, MAX32, MIN32):
                scalar, q = seed(); q[1] = [(0, 0), (value, -value if value != MIN32 else MAX32), (0, 0), (0, 0)]
                for dst in (1, 2):
                    out = copy.deepcopy(q); out[dst] = rotc(q[1], angle)
                    check(f'rotc-{angle}-{value}-dst{dst}', 0x1c << 56 | dst << 48 | 1 << 40 | angle << 24,
                          scalar, q, (scalar, out))
        scalar, q = seed(); scalar[1] = (MAX32, 0, -1)
        check('scalar-alias-overflow', 0x0101010000000000, scalar, q,
              (scalar[:1] + [(2*MAX32, 0, -1)] + scalar[2:], q), 'OVERFLOW')
        scalar, q = seed(); q[1][3] = (MAX32, 0); q[2][3] = (1, 0)
        out = copy.deepcopy(q); out[1] = [add(x, y) for x, y in zip(q[1], q[2])]
        check('late-qadd-overflow', 0x1001020000000000, scalar, q, (scalar, out), 'OVERFLOW')
        scalar, q = seed(); q[1] = [(2, 0), (0, 1), (3, -1), (5, 0)]
        # sqrt(3) ordering selects 3-sqrt(3), not the smallest real coefficient.
        minimum = (3, -1)
        out = copy.deepcopy(q); out[1] = [subtract(r, minimum) for r in q[1]]
        check('qnorm-surd-order', 0x1201000000000000, scalar, q, (scalar, out))
        scalar, q = seed(); q[1] = [(MIN32, 0), (0, 0), (0, 0), (MAX32, 0)]
        out = copy.deepcopy(q); out[1] = [subtract(r, (MIN32, 0)) for r in q[1]]
        check('qnorm-overflow', 0x1201000000000000, scalar, q, (scalar, out), 'OVERFLOW')
        scalar, q = seed()
        for word, fault in [(0xfe << 56, 'UNSUPPORTED'), (0x1c << 56 | 36 << 24, 'UNSUPPORTED'),
                            (0x00 << 56 | 255 << 48, 'INVALID_REGISTER')]:
            check(f'fault-{word:x}', word, scalar, q, (scalar, q), fault, python_fault=True)
        word = 0x1c02010006000000; out = python_state(word, scalar, q, 'step')[1:]
        check('python-only-angle6', word, scalar, q, out, 'UNSUPPORTED')
        for mode in ('reload', 'cold'):
            expected = (scalar, q) if mode == 'reload' else ([(0, 0, -1)]*26, [[(0, 0)]*4 for _ in range(13)])
            check(mode, 0xfe << 56, scalar, q, expected, mode=mode)
        scalar = [(0, 0, -1)]*26; q = [[(0, 0)]*4 for _ in range(13)]
        scalar[1] = (0, MIN32, -1)
        check('snap-extreme-proof', 0x07 << 56, scalar, q, (scalar, q), mode='proof')
        check('halt', 0x08 << 56, scalar, q, (scalar, q))
        expected = python_state(0xff << 56, scalar, q, 'pell9')[1:]
        assert expected[0][1] == (2, 1, 9)
        # Reload resets retirement count in C++; compare the preserved Pell state.
        assert cpp_state(binary, 0xff << 56, scalar, q, 'pell9')[1:] == expected
        records.append({'case': 'pell9-mantissa-and-step', 'classification': 'matching'})
    result = {'status': 'PASS', 'cases': records, 'conflicting': 0,
              'scope': 'Python/C++ integer VM subset; no RTL rounding, tags, SDF or periodic recovery parity'}
    if len(sys.argv) == 3 and sys.argv[1] == '--output':
        Path(sys.argv[2]).write_text(json.dumps(result, indent=2)+'\n')
    print(f'PASS software semantics: {len(records)} cases; unsupported domains classified separately')


if __name__ == '__main__':
    main()
