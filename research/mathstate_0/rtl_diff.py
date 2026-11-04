"""Run selected fixture traces against frozen CPU and established TB."""
from pathlib import Path
import subprocess
import tempfile
from software.experiments.surd_cpu_stream import Stream
from research.mathstate_0.experiment import U, INV, NEG, fixtures

ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT/'hardware/boards/artix7/wukong_v3/cpu_v02/rtl/spu13_core.v'
CONSTANTS = {U: (2, 1, 1), INV: (2, -1, 1), NEG: (-1, 0, 1)}


def program():
    s = Stream()
    for name, (initial, seq) in fixtures().items():
        s.reset()
        s.load(0, (*initial, 1))
        # Distinct initialized destination and an uninitialized S7 exercise
        # preservation and validity through the existing full-bank guard.
        s.load(3, (17, -19, 23))
        for m in sorted(set(seq)):
            s.load({U: 1, INV: 2, NEG: 4}[m], CONSTANTS[m])
        for n, m in enumerate(seq, 1):
            s.command('SMUL', ['S0', 'S0', f'S{ {U: 1, INV: 2, NEG: 4}[m]}'])
            status = s.status
            s.command('SSTAT', [])
            if status:
                if name != 'F3' or n != 1 or status != 2:
                    raise AssertionError((name, n, status))
                break
        s.read_tuple(0)
        s.command('SRD', ['S7', 0])  # uninitialized; status 1
    # F5: retain old identity in S5, overwrite S0, materialize from S5.
    s.reset()
    s.load(0, (3, -2, 1)); s.load(5, (3, -2, 1)); s.load(1, (2, 1, 1))
    s.load(0, (7, 8, 1)); s.command('SMUL', ['S3', 'S5', 'S1'])
    s.read_tuple(0); s.read_tuple(3)
    # F7 substitution: under a final-state-only boundary retain the initial
    # value instead of issuing u then u^-1; loads match the eager fixture.
    s.reset()
    s.load(0, (3, -2, 1)); s.load(3, (17, -19, 23))
    s.load(2, (2, -1, 1)); s.load(1, (2, 1, 1))
    s.command('SSTAT', []); s.read_tuple(0); s.command('SRD', ['S7', 0])
    return '\n'.join(s.lines) + '\n'


def main():
    with tempfile.TemporaryDirectory(prefix='mathstate0_') as temp:
        out = Path(temp)
        program_path = out/'program.txt'
        program_path.write_text(program())
        image = out/'cpu.vvp'
        cmd = ['iverilog', '-g2012', '-s', 'spu13_core_surd_tb', '-o', str(image), str(RTL)]
        for d in sorted({p.parent for p in (ROOT/'hardware/rtl').rglob('*.v')}):
            cmd += ['-y', str(d), '-I', str(d)]
        for d in ('hardware/vendor/gowin', 'hardware/vendor/ice40', 'hardware/tests/common'):
            cmd += ['-y', d, '-I', d]
        cmd += ['-I', str(ROOT), 'hardware/tests/spu13/spu13_core_surd_tb.v']
        subprocess.run(cmd, cwd=ROOT, check=True)
        result = subprocess.run(['vvp', str(image), '+PROGRAM=' + str(program_path)],
                                cwd=ROOT, check=True, capture_output=True, text=True)
        lines = result.stdout.splitlines()
        if not any('PASS canonical CPU directed execution' in line for line in lines):
            raise AssertionError('missing testbench pass')
        print('RTL_DIFF PASS fixtures=F1,F2,F3,F4,F5,F7,eager_and_noop instructions=',
              sum(line.startswith('INS ') for line in lines))
        print(next(line for line in lines if line.startswith('VERIFICATION ')))


if __name__ == '__main__':
    main()
