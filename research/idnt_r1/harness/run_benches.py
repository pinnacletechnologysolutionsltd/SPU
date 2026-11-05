# Runner-equivalent compile+run for a bench list (verdict: any FAIL -> fail, else PASS, else NO VERDICT).
# usage: run_benches.py <root> <core_override|-> <bench_list> <out_dir>
import os, re, subprocess, sys, time
from pathlib import Path
root, core, blist, out = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3], Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
gather = Path(__file__).with_name('gather_srcs.py')
args = open(root / 'build/idnt-r1/iverilog_args.txt').read().split()
VARIANTS = {'spu13_core_regen_off_tb.v': [('REGEN_EN', '0')]}
results = []
for tb in [l.strip() for l in open(blist) if l.strip()]:
    srcs = subprocess.run([sys.executable, str(gather), str(root), tb], capture_output=True, text=True, check=True).stdout.split()
    if core != '-':
        srcs = [core if s.endswith('/hardware/rtl/core/spu13/spu13_core.v') else s for s in srcs]
    tbt = open(root / tb).read()
    inc = re.findall(r'^\s*`include\s+"([^"]+)"', tbt, re.M)
    srcs = [s for s in srcs if os.path.basename(s) not in inc]
    mods = re.findall(r'^\s*module\s+([A-Za-z_]\w*)', tbt, re.M)
    top = Path(tb).stem if Path(tb).stem in mods else mods[0]  # runner rule
    runs = [('', [])] + ([('variant', VARIANTS[Path(tb).name])] if Path(tb).name in VARIANTS else [])
    for label, ov in runs:
        name = Path(tb).stem + (f'_{label}' if label else '')
        vvp = out / f'{name}.vvp'; t0 = time.time()
        cmd = ['iverilog', '-g2012'] + args + ['-s', top] + [f'-P{top}.{k}={v}' for k, v in ov] + ['-o', str(vvp)] + srcs + [str(root / tb)]
        c = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        if c.returncode:
            verdict, log = 'COMPILE_ERROR', c.stderr
        else:
            try:
                r = subprocess.run(['vvp', '-n', str(vvp)], cwd=root, capture_output=True, text=True, timeout=15)
                log = r.stdout + r.stderr
                verdict = 'FAIL' if 'FAIL' in log else 'PASS' if 'PASS' in log else 'NO_VERDICT'
            except subprocess.TimeoutExpired:
                verdict, log = 'TIMEOUT', ''
        (out / f'{name}.log').write_text(log)
        results.append((name, verdict, time.time() - t0))
        print(f'{verdict:13s} {time.time()-t0:6.1f}s {name}', flush=True)
bad = [r for r in results if r[1] != 'PASS']
print(f'SUMMARY: {len(results)-len(bad)}/{len(results)} PASS')
sys.exit(1 if bad else 0)
