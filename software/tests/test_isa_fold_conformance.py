"""Observable scalar outputs and Pell metadata survive canonical folding."""
import contextlib
import io
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software import spu_vm as vm
from software.tools import spu13_asm as asm

def execute(source, fold):
    words = asm.assemble(source, fold=fold)[0]
    core = vm.SPUCore(verbose=False)
    core.load(words)
    with contextlib.redirect_stdout(io.StringIO()):
        core.run()
    return core

for dest, second in [(0, 1), (25, 0)]:
    source = f'LD R{second}, 9, 0\nQLDI QR0, 3, 5, 0, 1\nHEX R{dest}, QR0\nADD R{second}, R{second}\nLOG R{second}'
    for fold in (False, True):
        core = execute(source, fold)
        assert (core.regs[second].a, core.regs[second].b) == (8, 0)
    source = f'LD R{second}, 9, 0\nQLDI QR0, 1, 0, 0, 0\nQLDI QR1, 0, 1, 0, 0\nSPREAD R{dest}, QR0, QR1\nADD R{second}, R{second}\nLOG R{second}'
    plain, folded = execute(source, False), execute(source, True)
    # Each unit vector has three unit pairwise differences: Q=3, denominator=9.
    for core in (plain, folded):
        assert (core.regs[second].a, core.regs[second].b) == (18, 0)

source = 'LD R0, 1, 0\n' + 'ROT R0\n'*9 + 'LOG R0'
for fold in (False, True):
    core = execute(source, fold)
    assert (core.regs[0].a, core.regs[0].b, core.regs[0].pell_step, core.regs[0].polarity) == (2, 1, 9, 1)
    assert sum(w >> 56 == 4 for w in asm.assemble(source, fold=fold)[0]) == 9

source = 'LD R0, 2, 3\nJINV R0\nJINV R0\nLOG R0'
for fold in (False, True):
    core = execute(source, fold)
    assert (core.regs[0].a, core.regs[0].b) == (2, 3)
for path in ('software/programs/pell_orbit_demo.sas', 'examples/02_quadray_orbit/quadray_orbit.sas'):
    source = (ROOT/path).read_text()
    for words in (vm.assemble_source(source), asm.assemble(source, fold=False)[0]):
        core = vm.SPUCore(verbose=False)
        core.load(words)
        with contextlib.redirect_stdout(io.StringIO()):
            core.run()
        assert (core.regs[3].a, core.regs[3].b) == (9, 5)
        assert (core.regs[4].a, core.regs[4].b) == (7, 4)
print('PASS folded HEX/SPREAD destinations, register wrap, Pell metadata and conjugation')
