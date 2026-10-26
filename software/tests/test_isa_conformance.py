"""Literal canonical words and bounded Python/C++ execution; no WF/transport claims."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software import spu_vm as vm
from software.tools import spu13_asm as asm

# Literal words, independent of encoder helpers. Every C++ mnemonic is covered.
CASES = [
    ('LD R25, -32768, 32767', 0x00190080007fff00),
    ('ADD R3, R1', 0x0103010000000000),
    ('SUB R3, R1', 0x0203010000000000),
    ('MUL R3, R1', 0x0303010000000000),
    ('ROT R3, R3', 0x0403030000000000),
    ('LOG R3', 0x0503000000000000),
    ('JMP 65535', 0x060000ffff000000),
    ('SNAP', 0x0700000000000000),
    ('HALT', 0x0800000000000000),
    ('QADD QR12, QR1', 0x100c010000000000),
    ('QROT QR12, R0', 0x110c000000000000),
    ('QNORM QR12', 0x120c000000000000),
    ('QLOAD QR12, R22', 0x130c160000000000),
    ('QLOG QR12', 0x140c000000000000),
    ('SPREAD R3, QR2, QR1', 0x1503020000000100),
    ('HEX R25, QR12', 0x16190c0000000000),
    ('EQUIL', 0x1700000000000000),
    ('IDNT QR12', 0x180c000000000000),
    ('JINV R25', 0x1919000000000000),
    ('ANNE QR12', 0x1a0c000000000000),
    ('QSUB QR12, QR2, QR1', 0x1b0c020000000100),
    ('ROTC QR12, QR2, 5', 0x1c0c020005000000),
    ('QLDI QR12, -128, 127, -1, 0', 0x1d0c00807fff0000),
    ('DELTA QR12, 65535, 32768, 7', 0x1e0c07ffff800000),
    ('CALL 32768', 0x2000008000000000),
    ('RET', 0x2100000000000000),
    ('QREAD QR2, QR1', 0x2202010000000000),
    ('NOP', 0xff00000000000000),
]

def run_python(source):
    c = vm.SPUCore(verbose=False, max_steps=256)
    c.load(asm.assemble(source, fold=False)[0])
    with contextlib.redirect_stdout(io.StringIO()):
        c.run()
    rows = [('R', i, r.a, r.b) for i, r in enumerate(c.regs)]
    rows += [('Q', i, *(v for r in q.components() for v in (r.a, r.b)))
             for i, q in enumerate(c.qregs)]
    return c, rows

def reject(encode, source):
    try:
        encode(source)
    except (ValueError, asm.AssemblyError):
        return
    raise AssertionError(f'accepted invalid or unsupported source: {source}')

def main():
    with tempfile.TemporaryDirectory(prefix='spu_isa_') as directory:
        binary = Path(directory) / 'cpp'
        cli_binary = Path(directory) / 'spu_vm'
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra',
                        str(ROOT/'software/tests/isa_conformance_cpp.cpp'), '-o', str(binary)], check=True)
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra',
                        str(ROOT/'software/vm/spu_vm.cpp'), '-o', str(cli_binary)], check=True)
        for source, expected in CASES:
            assert asm.assemble(source, fold=False)[0] == [expected], source
            assert vm.assemble_source(source) == [expected], source
            result = subprocess.run([str(binary)], input=source, text=True, capture_output=True, check=True)
            assert result.stdout.strip() == f'WORD {expected:x}', (source, result.stdout)
        for source, expected in [('MIN4 QR12', 0x1f0c000000000000),
                                 ('REGEN 3', 0x0900000003000000)]:
            assert asm.assemble(source, fold=False)[0] == vm.assemble_source(source) == [expected]
        assert vm.assemble_source('QLDI QR12, 0x807f, 0xff00') == [0x1d0c00807fff0000]
        for source in ['ADD R0, R1, R2', 'SUB R0, R1, R2', 'MUL R0, R1, R2', 'COND R0, 0', 'TYPO']:
            for fold in (True, False):
                reject(lambda s: asm.assemble(s, fold=fold), source)
            reject(vm.assemble_source, source)
            result = subprocess.run([str(binary)], input=source, text=True, capture_output=True)
            assert result.returncode == 1, source
        for name, args in [('SLI','S0, 0, 0'), ('SLD','S0'), ('SRD','S0, 0'),
                           ('SMUL','S0, S1, S2'), ('SADD','S0, S1, S2'),
                           ('SSUB','S0, S1, S2'), ('SNORM','S0, S1'), ('SSTAT','')]:
            source = name + ' ' + args
            reject(vm.assemble_source, source)
            assert subprocess.run([str(binary)], input=source, text=True, capture_output=True).returncode == 1
        for opcode in range(0x70, 0x78):
            word = opcode << 56 | 1 << 48
            core = vm.SPUCore(verbose=False)
            core.regs[1] = vm.RationalSurd(9, -3)
            core.load([word])
            try:
                core.step()
            except ValueError:
                pass
            else:
                raise AssertionError('VM silently accepted unsupported Surd word')
            assert core.halted and core.pc == 0 and core.step_count == 0
            assert (core.regs[1].a, core.regs[1].b) == (9, -3)
            result = subprocess.run([str(binary), 'state', 'raw'], input=f'{word:x}', text=True, capture_output=True, check=True)
            assert result.stdout.strip() == 'REJECTED 0 1 9 -3 13'
        result = subprocess.run([str(binary), 'state', 'raw'], input='1c02010006000000', text=True, capture_output=True, check=True)
        assert result.stdout.strip() == 'REJECTED 0 1 9 -3 13'
        programs = [
            ('LD R1, -2, 3\nHALT\nLD R1, 9, 0', (1, -2, 3)),
            ('LD R1, 2, 1\nLD R2, 3, -1\nMUL R1, R2\nHALT', (1, 3, 1)),
            ('QLDI QR1, -4, 6, 2, 1\nQREAD QR2, QR1\nQSUB QR2, QR2, QR1\nHALT', None),
            ('DELTA QR2, 65535, 32768, 7\nHALT', None),
            ('JMP 65535', None),
            ('RET', None),
        ]
        for source, expected in programs:
            core, rows = run_python(source)
            result = subprocess.run([str(binary), 'state'], input=source, text=True, capture_output=True, check=True)
            got = [tuple([p[0], *map(int, p[1:])]) for line in result.stdout.splitlines()
                   if (p := line.split()) and p[0] in ('R', 'Q')]
            assert got == rows, source
            assert f'CONTROL {core.pc} {int(core.halted)} {len(core.call_stack)}' in result.stdout
            if expected:
                i, a, b = expected
                assert (core.regs[i].a, core.regs[i].b) == (a, b)
            if source.startswith('DELTA'):
                assert [r.a for r in core.qregs[2].components()] == [98303, 0, 7, 0]
            if source.startswith('QLDI'):
                assert all((r.a, r.b) == (0, 0) for r in core.qregs[2].components())
        step_file = Path(directory) / 'step_budget.sas'
        step_file.write_text('NOP\n')
        result = subprocess.run([str(cli_binary), str(step_file), '--steps', '1', '--quiet'],
                                text=True, capture_output=True)
        assert result.returncode == 3, (result.returncode, result.stdout, result.stderr)
        assert 'stopped at the --steps budget before HALT' in result.stderr
        halt_file = Path(directory) / 'halt_at_budget.sas'
        halt_file.write_text('HALT\n')
        result = subprocess.run([str(cli_binary), str(halt_file), '--steps', '1', '--quiet'],
                                text=True, capture_output=True)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        assert 'Execution complete' in result.stdout and 'budget' not in result.stderr
        for bad_steps in ('0', '-1', 'invalid', '1tail'):
            result = subprocess.run([str(cli_binary), str(halt_file), '--steps', bad_steps, '--quiet'],
                                    text=True, capture_output=True)
            assert result.returncode == 1, (bad_steps, result.returncode)
            assert 'requires a positive integer' in result.stderr
        result = subprocess.run([str(cli_binary), str(halt_file), '--steps'],
                                text=True, capture_output=True)
        assert result.returncode == 1 and 'requires a positive integer' in result.stderr
    print('PASS canonical literal words, bounded VM state, HALT and unsupported source rejection')

if __name__ == '__main__':
    main()
