"""Compare a CPU-REPRO-1 run directory with the golden build. Read-only.
Usage: python3 -I compare.py RUNDIR [OUTFILE]   (default OUTFILE = RUNDIR/COMPARE_DETAIL.txt; pass another path to leave a finished run untouched; env GOLDEN_VIVADO = golden build/vivado directory containing board3_01, board3p_01, board4b_01)
Verdict is decided ONLY by the .bin / bitstream payload hash. Report differences are listed for diagnosis and never upgrade a verdict."""
import hashlib, os, re, struct, sys
G_BIN = 'cc259988b32dcd890a25c8a1765c6a28e3fafa280bcaed1aa5073f552dbc156c'
G_BIT = '442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea'
G_SYN = '938f0772eb82f5f4bcbdb33def00b4363b11bfdb8749a257d592aab2ffd42f20'
G_RTE = '48e0e1613a76315592852d8462bf2f91680c2ed87bfa5575ea690a941988a5c8'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
run = os.path.abspath(sys.argv[1]); gold = os.path.abspath(os.environ['GOLDEN_VIVADO'])
gold_root = os.path.dirname(os.path.dirname(gold))   # clone root that contains build/vivado
out, diffs = [], []
def say(s): out.append(s); print(s)
def norm(path):
    keep = []
    for l in open(path, errors='replace').read().splitlines():
        if re.match(r'\|\s*(Date|Host|Command)\s*:', l): continue
        if re.fullmatch(r'-{20,}', l.strip()): continue   # separator width follows the (ignored) Command line length
        l = re.sub(r'\S*/cpu_board_3\.xdc', '<XDC>', l)    # same constraint file bytes at a different path (hash checked via run_manifest)
        keep.append(l.replace(gold, '<ROOT>').replace(run, '<ROOT>').replace(gold_root, '<ROOT>'))
    return keep
def cmp_file(tag, g, n):
    if not os.path.exists(g) or not os.path.exists(n): diffs.append(f'{tag}: missing ({"golden" if not os.path.exists(g) else "run"})'); return
    a, b = norm(g), norm(n)
    if a == b: say(f'SAME  {tag}'); return
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    diffs.append(f'{tag}: differs at normalized line {first + 1} (golden {len(a)} lines, run {len(b)} lines)'); say(f'DIFF  {tag} line {first + 1}')
say(f'run={run}\ngolden={gold}')
# golden identity (a stale or wrong golden directory must not produce a verdict)
for p, h in (('board3_01/synth/synth.dcp', G_SYN), ('board3p_01/route/routed.dcp', G_RTE), ('board4b_01/bit/cpu_board_2r_top.bin', G_BIN), ('board4b_01/bit/cpu_board_2r_top.bit', G_BIT)):
    if sha(os.path.join(gold, p)) != h: say(f'GOLDEN_IDENTITY_FAIL {p}'); sys.exit(3)
say('golden identity OK')
# Phase S manifest: tool, args, XDC and source-hash multiset (paths of the five moved files and the filelist hash legitimately differ)
def manifest(p):
    d = {'src': [], 'args': []}
    for l in open(p):
        k, _, v = l.rstrip('\n').partition(' ')
        if k == 'source_sha256': d['src'].append(v.split()[0])
        elif k == 'arg' and not v.startswith(('-filelist', '-xdc')): d['args'].append(v)
        elif k in ('tool_version', 'xdc_sha256'): d[k] = v
    d['src'].sort(); return d
mg, mn = manifest(os.path.join(gold, 'board3_01/synth/run_manifest.txt')), manifest(os.path.join(run, 'synth/run_manifest.txt'))
for k in ('tool_version', 'xdc_sha256', 'src', 'args'):
    (say if mg[k] == mn[k] else diffs.append)(f'{"SAME  " if mg[k] == mn[k] else "manifest: "}run_manifest {k}')
# reports
for f in ('synth_cdc.rpt', 'synth_check_timing.rpt', 'synth_clock_networks.rpt', 'synth_clocks.rpt', 'synth_drc.rpt', 'synth_methodology.rpt', 'synth_timing_summary.rpt', 'synth_utilization.rpt', 'synth_utilization_hier.rpt', 'structure.rpt'):
    cmp_file('synth/' + f, os.path.join(gold, 'board3_01/synth', f), os.path.join(run, 'synth', f))
ga = os.path.join(gold, 'board3_01/analysis')
for f in ('ports.txt', 'async_inventory.txt', 'asyncreg.txt', 'packet_cells.txt', 'tx_chain.txt', 'est_recovery.rpt', 'est_removal.rpt'):
    if os.path.exists(os.path.join(run, 'analysis', f)): cmp_file('analysis/' + f, os.path.join(ga, f), os.path.join(run, 'analysis', f))
cmp_file('analysis/synth_rom_props.txt', os.path.join(ga, 'rom_props.txt'), os.path.join(run, 'analysis/synth_rom_props.txt'))
cmp_file('analysis/synth_rom_loads.txt', os.path.join(ga, 'rom_loads.txt'), os.path.join(run, 'analysis/synth_rom_loads.txt'))
gr = os.path.join(gold, 'board3p_01/route')
for f in sorted(os.listdir(gr)):
    if f.endswith(('.rpt', '.txt')): cmp_file('route/' + f, os.path.join(gr, f), os.path.join(run, 'route', f))
cmp_file('analysis/route_rom_props.txt', os.path.join(gold, 'board3p_01/analysis/rom_props.txt'), os.path.join(run, 'analysis/route_rom_props.txt'))
cmp_file('analysis/route_rom_loads.txt', os.path.join(gold, 'board3p_01/analysis/rom_loads.txt'), os.path.join(run, 'analysis/route_rom_loads.txt'))
gb = os.path.join(gold, 'board4b_01/bit')
for f in ('bitstream_properties.txt', 'pre_bitstream_drc.rpt', 'waivers.rpt'): cmp_file('bit/' + f, os.path.join(gb, f), os.path.join(run, 'bit/out', f))
# informational: checkpoints are not expected to be byte-identical (checkpoint serialisation), .bit differs by header date/time
for tag, g, n in (('synth.dcp', 'board3_01/synth/synth.dcp', 'synth/synth.dcp'), ('routed.dcp', 'board3p_01/route/routed.dcp', 'route/routed.dcp')):
    say(f'INFO  {tag} sha256 {"EQUAL" if os.path.exists(os.path.join(run, n)) and sha(os.path.join(run, n)) == sha(os.path.join(gold, g)) else "differs or missing"} (informational)')
# bitstream
bitp, binp = os.path.join(run, 'bit/out/cpu_board_2r_top.bit'), os.path.join(run, 'bit/out/cpu_board_2r_top.bin')
if not (os.path.exists(bitp) and os.path.exists(binp)): say('VERDICT HOLD: bitstream files missing'); sys.exit(2)
d, b = open(bitp, 'rb').read(), open(binp, 'rb').read()
L = struct.unpack('>H', d[0:2])[0]; pos = 2 + L + 2; info = {}
for _ in range(4):
    k = d[pos:pos + 1].decode(); n = struct.unpack('>H', d[pos + 1:pos + 3])[0]; info[k] = d[pos + 3:pos + 3 + n].rstrip(b'\0').decode(); pos += 3 + n
n = struct.unpack('>I', d[pos + 1:pos + 5])[0]; payload = d[pos + 5:pos + 5 + n]
say(f'bit header: design={info["a"].split(";")[0]} part={info["b"]} date={info["c"]} time={info["d"]}; payload_equals_bin={payload == b}')
say(f'.bin sha256 {sha(binp)} ({"EQUAL" if sha(binp) == G_BIN else "DIFFERENT"} to golden)')
say(f'.bit sha256 {sha(bitp)} ({"EQUAL" if sha(bitp) == G_BIT else "different"} to golden; header date/time is expected to differ)')
say(f'report differences: {len(diffs)}'); [say('  ' + x) for x in diffs]
if sha(binp) == G_BIN and payload == b: say('VERDICT PASS-BIT-EXACT (configuration payload identical to golden)'); code = 0
else: say('VERDICT HOLD (payload differs or is inconsistent; functional equivalence is NOT established by this tool)'); code = 1
open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(run, 'COMPARE_DETAIL.txt'), 'w').write('\n'.join(out) + '\n'); sys.exit(code)
