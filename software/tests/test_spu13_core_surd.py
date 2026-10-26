#!/usr/bin/env python3
"""One recorded CPU compile/execution, with optional complete retained kernels."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments.surd_cpu_stream import Stream
from software.experiments.surd_cpu_directed import directed
from software.experiments.surd_cpu_verification_cases import verification_cases
from software.experiments.surd_cpu_kernel_schedule import kernels, CORPUS
from software.tools import spu13_asm as asm
from software.tools.surd_cpu_encoding import encode_surd


def assembler_checks():
    examples = [('SMUL',['S7','S3','S5']),('SADD',['S2','S1','S0']),
                ('SSUB',['S0','S0','S1']),('SNORM',['S2','S2']),
                ('SLI',['S7','5','0xffffffff']),('SLD',['S7']),
                ('SRD',['S7','5']),('SSTAT',[])]
    for name,args in examples:
        if asm._assemble_line([name,*args],{}) != encode_surd(name,args):
            raise AssertionError('assembler disagreement')
    for name,args in [('SMUL',['S8','S0','S1']),('SNORM',['R0','S1']),
                      ('SLI',['S0','6','0']),('SLI',['S0','0','-1'])]:
        try:
            asm._assemble_line([name,*args],{})
        except asm.AssemblyError:
            continue
        raise AssertionError('assembler accepted an invalid encoding')


def summarize(log, records):
    per = defaultdict(lambda: defaultdict(int))
    for row in re.findall(r'^INS (.*)$',log,re.M):
        g,op,tag,lat,norm,align,prod,rescue,starts,stalls,status = map(int,row.split())
        if g < 0:
            continue
        d = per[str(g)]
        d['retired_instructions'] += 1
        d['instruction_cycles'] += lat
        d['normalization_cycles'] += norm
        d['alignment_cycles'] += align
        d['product_check_cycles'] += prod
        d['rescue_requests'] += rescue
        d['normalizer_requests_all_reasons'] += starts
        d['stalls'] += stalls
        d['failures'] += int(status!=0)
        d['scheduled_boundary_reductions'] += int(op==0x76 and tag==1 and status==0)
        if op in (0x70,0x71,0x72):
            d['tuple_transfer_instructions'] += 1
            d['tuple_transfer_cycles'] += lat
    elapsed = dict(re.findall(r'^GROUP (\d+) (\d+)$',log,re.M))
    for group, expected in records.items():
        d = per[group]
        d.update(expected)
        d['total_cycles'] = int(elapsed[group])
        d['issuer_control_cycles'] = d['total_cycles']-d['instruction_cycles']
        d['exact_cpu_readback_agreement'] = True
        d['fallbacks'] = 0
        if d['scheduled_boundary_reductions'] != 8*expected['length'] or d['failures']:
            raise AssertionError('kernel boundary accounting/failure mismatch')
    by_length = {}
    for n in (1,3,6,12):
        cohort = [v for v in per.values() if v['length']==n]
        if not cohort:
            continue
        totals = {key:sum(v[key] for v in cohort) for key in (
            'total_cycles','retired_instructions','tuple_transfer_instructions',
            'tuple_transfer_cycles','normalization_cycles','alignment_cycles',
            'product_check_cycles','rescue_requests','scheduled_boundary_reductions',
            'normalizer_requests_all_reasons','failures','fallbacks','stalls','issuer_control_cycles')}
        by_length[str(n)] = {'records':len(cohort),'totals':totals,
                             'min_cycles':min(v['total_cycles'] for v in cohort),
                             'max_cycles':max(v['total_cycles'] for v in cohort)}
    return {'records':dict(per),'lengths':by_length}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path)
    p.add_argument('--kernels',action='store_true')
    p.add_argument('--verification-only',action='store_true',help='run only preservation/alias/fault cases')
    args = p.parse_args()
    if args.verification_only and args.kernels:
        p.error('--verification-only cannot include retained kernels')
    if args.output_dir:
        out = args.output_dir
        out.mkdir(exist_ok=False,parents=True)
    else:
        base = ROOT/'build/spu_surd_register/main_cpu_integration_20261007'
        base.mkdir(parents=True,exist_ok=True)
        out = Path(tempfile.mkdtemp(prefix='regression_directed_',dir=base))
    assembler_checks()
    stream = Stream()
    if not args.verification_only:
        directed(stream)
    verification_cases(stream)
    records = kernels(stream) if args.kernels else {}
    program = out/'program.txt'
    program.write_text('\n'.join(stream.lines)+'\n')
    (out/'reference_records.json').write_text(json.dumps(records,indent=2)+'\n')
    image = out/'cpu.vvp'
    compile_cmd = ['iverilog','-g2012','-s','spu13_core_surd_tb','-o',str(image)]
    directories = sorted({str(q.parent) for q in (ROOT/'hardware/rtl').rglob('*.v')})
    directories += ['hardware/vendor/gowin','hardware/vendor/ice40','hardware/tests/common']
    for d in directories:
        compile_cmd += ['-y',d,'-I',d]
    compile_cmd += ['-I',str(ROOT),'hardware/tests/spu13/spu13_core_surd_tb.v']
    (out/'compile_command.json').write_text(json.dumps(compile_cmd,indent=2)+'\n')
    with (out/'compile.log').open('w') as f:
        subprocess.run(compile_cmd,cwd=ROOT,check=True,stdout=f,stderr=subprocess.STDOUT)
    names = image.read_text().split('.file_names')[-1]
    used = [name for name in re.findall(r'"([^"]+)"',names)
            if name.endswith('.v') and 'hardware/rtl/' in name]
    if not used:
        raise AssertionError('missing compiled CPU source provenance')
    (out/'rtl_source_list.txt').write_text('\n'.join(sorted(set(used)))+'\n')
    with (out/'runtime.log').open('w') as f:
        subprocess.run(['vvp',str(image),f'+PROGRAM={program.resolve()}'],cwd=ROOT,
                       check=True,stdout=f,stderr=subprocess.STDOUT)
    log = (out/'runtime.log').read_text()
    if 'PASS canonical CPU directed execution and complete kernel stream' not in log:
        raise AssertionError('missing CPU runtime PASS')
    checks = re.search(r'^VERIFICATION preservation=(\d+) aliases=(\d+) injections=(\d+)$', log, re.M)
    if not checks or int(checks[1]) < 6 or int(checks[2]) != 17 or int(checks[3]) != 6:
        raise AssertionError('missing preservation/alias/fault verification coverage')
    report = summarize(log,records)
    report.update(status='PASS_DIRECTED_CPU_RTL',kernels_executed=bool(records),
                  tuple_input_sha256=hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
                  program_sha256=hashlib.sha256(program.read_bytes()).hexdigest(),
                  baseline='UNSUPPORTED_IN_ACTIVE_CANONICAL_CORE',speedup='UNMEASURED',
                  instruction_elimination='UNMEASURED',energy='UNMEASURED',
                  scope='canonical CPU dispatch-port execution; boot/reset excluded; all kernel transfer and issuer cycles included',
                  rational_only_joint_coefficients=True,nonzero_radical_cases='directed diagnostics only',
                  netlist_verified=False,hardware_operations=0,verification_only=args.verification_only)
    report['directed_verification_checks'] = dict(zip(
        ('failed_retirement_preservation', 'alias_cases', 'engine_failure_injections'),
        map(int, checks.groups())))
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS directed CPU execution; retained records={len(records)}; evidence={out}')
if __name__=='__main__':
    main()
