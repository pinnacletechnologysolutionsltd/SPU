"""Focused actual-core dispatch and intermediate read/status observation."""
from pathlib import Path
import subprocess
import tempfile
from software.experiments.surd_cpu_stream import Stream

ROOT = Path(__file__).resolve().parents[2]


def main():
    s = Stream()
    s.load(0, (3, -2, 1))
    s.load(1, (2, 1, 1))
    s.load(2, (2, -1, 1))
    s.command('SMUL', ['S0', 'S0', 'S1'])
    if s.bank[0] != (0, -1, 1):
        raise AssertionError('intermediate oracle')
    s.read_tuple(0)  # observe the intermediate value through actual SRD
    s.command('SMUL', ['S0', 'S0', 'S2'])
    if s.bank[0] != (3, -2, 1):
        raise AssertionError('final oracle')
    s.read_tuple(0)
    s.command('SRD', ['S7', 0])  # uninitialized gives status 1
    s.command('SSTAT', [])       # observe the immediately prior status
    with tempfile.TemporaryDirectory(prefix='obs0_') as temp:
        out = Path(temp)
        program = out/'program.txt'
        program.write_text('\n'.join(s.lines)+'\n')
        image = out/'cpu.vvp'
        cmd = ['iverilog', '-g2012', '-s', 'spu13_core_surd_tb', '-o', str(image),
               'hardware/boards/artix7/wukong_v3/cpu_v02/rtl/spu13_core.v']
        for directory in sorted({p.parent for p in (ROOT/'hardware/rtl').rglob('*.v')}):
            cmd += ['-y', str(directory), '-I', str(directory)]
        for directory in ('hardware/vendor/gowin', 'hardware/vendor/ice40', 'hardware/tests/common'):
            cmd += ['-y', directory, '-I', directory]
        cmd += ['-I', str(ROOT), 'hardware/tests/spu13/spu13_core_surd_tb.v']
        subprocess.run(cmd, cwd=ROOT, check=True)
        proc = subprocess.run(['vvp', str(image), '+PROGRAM='+str(program)], cwd=ROOT,
                              capture_output=True, text=True, check=True)
        if 'PASS canonical CPU directed execution' not in proc.stdout:
            raise AssertionError('missing PASS')
        print('OBS0 PASS: intermediate (0,-1,1), final (3,-2,1), invalid read status 1')
        print(next(x for x in proc.stdout.splitlines() if x.startswith('VERIFICATION ')))


if __name__ == '__main__':
    main()
