#!/usr/bin/env python3
"""spu — SDK-0 command line for the frozen v0.3 `programmable-surd` profile (experimental developer interface).

  spu.py assemble SRC.spu -o OUT.spui --profile programmable-surd [--listing]
  spu.py disasm IMAGE.spui [--raw]
  spu.py run IMAGE.spui --backend oracle|sim|fpga [--budget N] [--port DEV] [--record-out F] [--json]
  spu.py verify IMAGE.spui [--expect EXPECT.json] [--backends oracle,sim[,fpga]] [--port DEV] [--budget N]

Backends: `oracle` = software/tests/psurd_oracle.py (independent Python reference); `sim` = the C++ simulator
software/vm/spu_vm (build with `make -C software/vm`; override with --spu-vm or $SPU_VM); `fpga` = a board running
the v0.3 image, through tools/psurd_uart_host.py (explicit --port only; no device discovery). `verify` requires
byte-identical result records from every backend and checks the expectations file, if given.
Exit status: 0 success, 1 failure or mismatch, 2 usage.
"""
import argparse, hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'software/tests'), str(ROOT / 'tools')]
import spu_asm as A, spu_record as REC

def run_oracle(img, budget):
    import psurd_oracle as O
    return O.record(O.run(A.parse_image(img), budget))
def run_sim(img, budget, vm):
    vm = Path(vm or os.environ.get('SPU_VM') or ROOT / 'software/vm/spu_vm')
    if not vm.exists(): raise RuntimeError(f'C++ simulator not found at {vm}; build it with: make -C software/vm')
    with tempfile.NamedTemporaryFile(suffix='.spui') as f:
        f.write(img); f.flush()
        p = subprocess.run([str(vm), '--profile', 'programmable-surd', f.name, '--budget', str(budget)], capture_output=True, text=True)
    if p.returncode: raise RuntimeError(f'simulator refused the image: {p.stderr.strip()}')
    return bytes.fromhex(p.stdout.split()[0])
def run_fpga(img, budget, port):
    if not port: raise RuntimeError('--port is required for the fpga backend (no device discovery)')
    import psurd_uart_host as H
    c = H.Client(H.Port(port)); time.sleep(c.t['startup_delay_s']); c.port.drain()
    st, pl, n = c.load(img)
    if st != H.OK: raise RuntimeError(f'board refused the image: status {st:#04x} {pl.hex()} after {n} frames')
    st, pl = c.start(budget)
    if st != H.OK: raise RuntimeError(f'board refused START: status {st:#04x} {pl.hex()}')
    c.wait(); st, pl = c.result()
    if st != H.OK: raise RuntimeError(f'RESULT answered {st:#04x}')
    return bytes(pl)
def execute(backend, img, a):
    return {'oracle': lambda: run_oracle(img, a.budget), 'sim': lambda: run_sim(img, a.budget, a.spu_vm),
            'fpga': lambda: run_fpga(img, a.budget, a.port)}[backend]()

def cmd_assemble(a):
    words, listing = A.assemble(Path(a.src).read_text(), a.profile); img = A.image(words)
    Path(a.output).write_bytes(img)
    if a.listing:
        for addr, ws, src in listing:
            for k, w in enumerate(ws): print(f'{addr + k:3d}  {w:016x}  {src if k == 0 else ""}')
    print(f'{a.output}: {len(words)} words, sha256 {hashlib.sha256(img).hexdigest()}', file=sys.stderr); return 0
def cmd_disasm(a): print(A.disassemble(A.parse_image(Path(a.image).read_bytes()), macros=not a.raw), end=''); return 0
def cmd_run(a):
    rec = execute(a.backend, Path(a.image).read_bytes(), a)
    if a.record_out: Path(a.record_out).write_bytes(rec)
    r = REC.decode(rec); print(json.dumps(r, indent=1) if a.json else REC.text(r)); return 0
def cmd_verify(a):
    img = Path(a.image).read_bytes(); exp = json.loads(Path(a.expect).read_text()) if a.expect else {}
    a.budget = exp.get('budget', a.budget); ok = True; recs = {}
    if 'image_sha256' in exp and hashlib.sha256(img).hexdigest() != exp['image_sha256']:
        print('FAIL image sha256 differs from the expectation file'); ok = False
    for b in a.backends.split(','):
        recs[b] = execute(b, img, a); print(f'{b:7s} record sha256 {hashlib.sha256(recs[b]).hexdigest()}')
    if len(set(recs.values())) != 1: print('FAIL backends returned different records'); ok = False
    rec = next(iter(recs.values())); r = REC.decode(rec)
    if 'record_sha256' in exp and hashlib.sha256(rec).hexdigest() != exp['record_sha256']:
        print('FAIL record differs from the expected record'); ok = False
    if 'cause' in exp and r['cause'] != exp['cause']: print(f"FAIL cause {r['cause']} != {exp['cause']}"); ok = False
    for name, val in exp.get('registers', {}).items():
        g = r['registers'][int(name[1:])]
        if not REC.same_value(g, val): print(f"FAIL {name} = {g['value']} != {REC.value_str(*val)}"); ok = False
    print(REC.text(r)); print('PASS' if ok else 'FAIL'); return 0 if ok else 1

def main(argv):
    p = argparse.ArgumentParser(prog='spu', description='SDK-0 for the frozen v0.3 programmable-surd profile')
    s = p.add_subparsers(dest='cmd', required=True)
    x = s.add_parser('assemble'); x.add_argument('src'); x.add_argument('-o', '--output', required=True)
    x.add_argument('--profile', required=True); x.add_argument('--listing', action='store_true')
    x = s.add_parser('disasm'); x.add_argument('image'); x.add_argument('--raw', action='store_true')
    for n in ('run', 'verify'):
        x = s.add_parser(n); x.add_argument('image'); x.add_argument('--budget', type=int, default=10000)
        x.add_argument('--port'); x.add_argument('--spu-vm')
        if n == 'run':
            x.add_argument('--backend', required=True, choices=('oracle', 'sim', 'fpga'))
            x.add_argument('--record-out'); x.add_argument('--json', action='store_true')
        else: x.add_argument('--expect'); x.add_argument('--backends', default='oracle,sim')
    a = p.parse_args(argv)
    try: return dict(assemble=cmd_assemble, disasm=cmd_disasm, run=cmd_run, verify=cmd_verify)[a.cmd](a)
    except (A.AsmError, ValueError, RuntimeError, OSError) as e: print(f'spu {a.cmd}: {e}', file=sys.stderr); return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
