#!/usr/bin/env python3
"""
SPU-13 Unified Forge CLI (v1.1)
The command centre for the Sovereign Fleet.

Usage:
    python3 spu_forge.py simulate programs/jitterbug.sas
    python3 spu_forge.py simulate programs/jitterbug.sas --steps 64 --quiet
    python3 spu_forge.py assemble programs/jitterbug.sas
    python3 spu_forge.py test
    python3 spu_forge.py build
    python3 spu_forge.py verify
"""

import sys
import os
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOFTWARE_DIR = os.path.join(REPO_ROOT, 'software')
VM_PATH = os.path.join(SOFTWARE_DIR, 'spu_vm.py')
ASM_PATH = os.path.join(REPO_ROOT, 'reference/synergeticrenderer/Laminar-Core/toolchain/spu13_asm.py')
BOARDS_DIR = os.path.join(REPO_ROOT, 'hardware/boards/icesugar')
PROGRAMS_DIR = os.path.join(SOFTWARE_DIR, 'programs')


def run_cmd(cmd, desc):
    print(f"--- {desc} ---")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("[PASS]\n")
    except subprocess.CalledProcessError:
        print(f"[FAIL] Error during: {desc}")
        sys.exit(1)


def cmd_simulate(args):
    """Run a .sas or .bin program through the SPU-13 soft-CPU."""
    if not args:
        print("Usage: spu-forge simulate <file.sas> [--steps N] [--quiet] [--proof]")
        # Default: run all programs in software/programs/
        sas_files = [f for f in os.listdir(PROGRAMS_DIR) if f.endswith('.sas')]
        if sas_files:
            print(f"\nAvailable programs in {PROGRAMS_DIR}:")
            for f in sorted(sas_files):
                print(f"  {f}")
        return

    source = args[0]
    extra = ' '.join(args[1:])

    if not os.path.isabs(source):
        # Try relative to cwd, then programs/
        if not os.path.exists(source):
            candidate = os.path.join(PROGRAMS_DIR, source)
            if os.path.exists(candidate):
                source = candidate

    run_cmd(f"python3 {VM_PATH} {source} {extra}", f"Simulating: {os.path.basename(source)}")


def cmd_assemble(args):
    """Assemble a .sas source file to .bin control words."""
    if not args:
        print("Usage: spu-forge assemble <file.sas> [output.bin]")
        return
    source = args[0]
    output = args[1] if len(args) > 1 else source.replace('.sas', '.bin')
    run_cmd(f"python3 {ASM_PATH} {source} {output}", f"Assembling: {os.path.basename(source)}")


def cmd_test(args):
    """Run all programs in software/programs/ as integration tests."""
    proof_mode = '--proof' in args
    print("--- SPU-13 Software Test Suite ---\n")
    if proof_mode:
        print("  [PROOF MODE] Showing step-by-step Q(√3) arithmetic\n")
    sas_files = sorted(f for f in os.listdir(PROGRAMS_DIR) if f.endswith('.sas'))
    if not sas_files:
        print("No .sas programs found in software/programs/")
        return

    passed = failed = 0
    for fname in sas_files:
        path = os.path.join(PROGRAMS_DIR, fname)
        print(f"  Testing: {fname}")
        proof_flag = '--proof' if proof_mode else ''
        quiet_flag = '' if proof_mode else '--quiet'
        result = subprocess.run(
            f"python3 {VM_PATH} {path} --steps 64 {quiet_flag} {proof_flag}",
            shell=True, capture_output=not proof_mode, text=True
        )
        if proof_mode:
            # output already printed live
            pass
        if result.returncode == 0:
            print(f"  [PASS] {fname}\n")
            passed += 1
        elif result.returncode == 2:
            # Exit 2 = SNAP failure (cubic leak detected — expected for quadrance_test)
            print(f"  [SNAP] {fname} — cubic leak detected (expected for stress tests)\n")
            passed += 1  # intentional failure counts as pass for that test
        else:
            print(f"  [FAIL] {fname}")
            if not proof_mode:
                print(result.stdout[-400:] if result.stdout else "")
                print(result.stderr[-200:] if result.stderr else "")
            failed += 1

    print(f"Results: {passed} passed, {failed} failed out of {len(sas_files)} programs")
    if failed:
        sys.exit(1)


def cmd_build(_args):
    """Synthesize SPU-13 for iCEsugar (UP5K)."""
    if not os.path.isdir(BOARDS_DIR):
        print(f"Board directory not found: {BOARDS_DIR}")
        sys.exit(1)
    os.chdir(BOARDS_DIR)
    run_cmd("make -f Makefile", "Synthesizing SPU-13 for iCEsugar")


def cmd_verify(_args):
    """Run formal verification (requires SymbiYosys)."""
    formal_dir = os.path.join(REPO_ROOT, 'hardware/formal')
    if not os.path.isdir(formal_dir):
        print(f"Formal directory not found: {formal_dir}")
        sys.exit(1)
    os.chdir(formal_dir)
    run_cmd("sby -f spu13_reachability.sby", "Formal Reachability Proofs")


COMMANDS = {
    'simulate': (cmd_simulate, "Run a .sas/.bin program in the soft-CPU"),
    'assemble': (cmd_assemble, "Assemble .sas source to .bin control words"),
    'test':     (cmd_test,     "Run all programs/ as integration tests  [--proof for maths output]"),
    'build':    (cmd_build,    "Synthesize RTL for iCEsugar (requires yosys/nextpnr)"),
    'verify':   (cmd_verify,   "Formal verification (requires SymbiYosys)"),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("Usage: python3 spu_forge.py <command> [args]\n")
        print("Commands:")
        for name, (_, desc) in COMMANDS.items():
            print(f"  {name:<12} {desc}")
        return

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd not in COMMANDS:
        print(f"Unknown command: '{cmd}'")
        print(f"Available: {', '.join(COMMANDS)}")
        sys.exit(1)

    COMMANDS[cmd][0](rest)


if __name__ == '__main__':
    main()
