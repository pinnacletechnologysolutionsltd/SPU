"""Invalid canonical source never silently aliases or produces partial output."""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software import spu_vm as vm
from software.tools import spu13_asm as asm

INVALID = [
    'ROTC QR0, QR1, 64', 'ROTC QR0, QR1, -1', 'ROTC QR0, QR1, 256',
    'ROTC QR0, QR1, 1, 2', 'ROTC R0, QR1, 1',
    'LD R26, 1', 'LD R256, 1', 'LD R-1, 1', 'LD R1junk, 1',
    'LD QR0, 1', 'LD R0, nope', 'LD R0, 1, 2, 3',
    'ADD R0, QR1', 'ADD R0, 2', 'ADD R0',
    'QSUB QR0', 'QSUB QR0, R1', 'QSUB QR0, QR1, R2',
    'QSUB QR0, QR1, QR13', 'QSUB QR0, QR1, QR256',
    'QSUB QR0, QR1, QR-1', 'QSUB QR0, QR1, QR2junk',
    'QSUB QR0, QR1, QR2, QR3', 'QSUB 0, QR1',
    'QREAD QR13, QR0', 'QREAD R0, QR1',
    'QLOAD QR0, R23', 'QLOAD QR0, QR1',
    'HALT 1', 'NOP R0', 'RET R0', 'SNAP R0', 'EQUIL QR0',
    'LOG R0, R1', 'HEX QR0, QR1', 'SPREAD R0, QR1',
    'QLDI QR13, 0, 0, 0, 0', 'QLDI QR0, 1, 2, 3, 4, 5',
    'DELTA QR0, 1, 2, 3, 4', 'CALL 65536', 'JMP -1',
]


def reject(encoder, source):
    try:
        encoder(source)
    except (ValueError, asm.AssemblyError):
        return
    raise AssertionError('invalid source accepted: '+source)


def main():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='spu_operand_') as directory:
        cpp = Path(directory)/'assembler'
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra',
                        str(ROOT/'software/tests/isa_conformance_cpp.cpp'), '-o', str(cpp)], check=True)
        for source in INVALID:
            for fold in (False, True):
                reject(lambda s: asm.assemble(s, fold=fold), 'LD R0, 1\n'+source)
                checks += 1
            reject(vm.assemble_source, 'LD R0, 1\n'+source)
            checks += 1
            result = subprocess.run([str(cpp)], input='LD R0, 1\n'+source,
                                    text=True, capture_output=True)
            assert result.returncode == 1 and not result.stdout, (source, result)
            checks += 1
        for selector in (60, 63, 124, 127, 128, -1):
            source = f'IROTC QR0, QR1, {selector}'
            reject(vm.assemble_source, source)
            for fold in (False, True):
                reject(lambda s: asm.assemble(s, fold=fold), source)
            checks += 3
        positives = [
            ('QSUB QR0, QR1', 0x1b00000000000100),
            ('QSUB QR0, QR2, QR1', 0x1b00020000000100),
            ('ROTC QR0, QR1, 63', 0x1c0001003f000000),
            ('ROTC QR0, QR1, 0x5', 0x1c00010005000000),
            ('rotc qr0, qr1, 0X5', 0x1c00010005000000),
            ('qload qr0, r22', 0x1300160000000000),
            ('LD R25, -32768, 32767', 0x00190080007fff00),
        ]
        for source, word in positives:
            assert asm.assemble(source, fold=False)[0] == [word]
            assert vm.assemble_source(source) == [word]
            result = subprocess.run([str(cpp)], input=source, text=True, capture_output=True, check=True)
            assert result.stdout.strip() == f'WORD {word:x}'
            checks += 3
        assert vm.assemble_source('QLDI QR12, 0x807f, 0xff00') == [0x1d0c00807fff0000]
        assert vm.assemble_source('LOAD2X QR12, 0x807f, 0xff00') == [0xd70c00807fff0000]
        assert asm.assemble('LD R[25], 1', fold=False)[0] == [0x0019000001000000]
        assert asm.assemble('QLDI QR0', fold=False)[0] == [0x1d00000000000000]
        assert vm.assemble_source('ROTC QR0, QR1') == [0x1c00010000000000]
        assert asm.assemble('ROTC QR0, QR1', fold=False)[0] == [0x1c00010000000000]
        checks += 6
    print(f'PASS canonical operand rejection and named legacy forms: {checks} checks')


if __name__ == '__main__':
    main()
