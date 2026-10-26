"""Focused exact Lorentz experiment on frozen Surd CPU dispatch RTL."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import re
import subprocess
import sys
import time

ROOT=Path('/home/john/Projects/hardware/SPU')
OUT=Path(__file__).resolve().parent
SNAP=ROOT/'build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/preparation_03/source_snapshot'
sys.path.insert(0,str(ROOT))
from software.experiments.surd_cpu_stream import Stream

def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')

literal=[(2,1),(7,4),(26,15),(97,56),(362,209),(1351,780),
         (5042,2911),(18817,10864),(70226,40545),(262087,151316)]
s=Stream();s.load(0,(1,0,1));s.load(1,(2,1,1))
s.load(2,(1,0,1));s.load(3,(2,-1,1))
rows=[];a,b=1,0
for n,expected in enumerate(literal,1):
    a,b=2*a+3*b,a+2*b
    assert (a,b)==expected and a*a-3*b*b==1
    s.command('SMUL',['S0','S0','S1']);s.command('SMUL',['S2','S2','S3'])
    assert s.bank[0]==(a,b,1) and s.bank[2]==(a,-b,1)
    s.read_tuple(0);s.read_tuple(2)
    s.command('SMUL',['S4','S0','S2']);assert s.bank[4]==(1,0,1);s.read_tuple(4)
    s.load(5,(1,0,2))
    s.command('SADD',['S6','S0','S2']);s.command('SMUL',['S6','S6','S5'])
    s.command('SNORM',['S6','S6']);assert s.bank[6]==(a,0,1);s.read_tuple(6)
    s.command('SSUB',['S7','S2','S0']);s.command('SMUL',['S7','S7','S5'])
    s.command('SNORM',['S7','S7']);assert s.bank[7]==(0,-b,1);s.read_tuple(7)
    s.command('SMUL',['S5','S6','S6']);s.command('SMUL',['S4','S7','S7'])
    s.command('SSUB',['S5','S5','S4']);assert s.bank[5]==(1,0,1);s.read_tuple(5)
    rows.append(dict(boosts=n,gamma=a,radical_coefficient=b,interval=1,
                     mistaken_gamma=2**n,arrival_model_disagrees=(a!=2**n)))
# Correct arithmetic accepts a malformed boost; the physical invariant rejects it.
s.reset();s.load(0,(2,2,1));s.load(1,(2,-2,1))
s.command('SMUL',['S2','S0','S1']);assert s.bank[2]==(-8,0,1)
s.read_tuple(2);s.command('SSTAT',[])
# Independent recurrence determines the first unrepresentable accumulator.
s.reset();s.load(0,(1,0,1));s.load(1,(2,1,1));a,b,n=1,0,0
while True:
    next_a,next_b=2*a+3*b,a+2*b;n+=1
    saved=s.bank[0];s.command('SMUL',['S0','S0','S1'])
    if next_a>=2**63 or next_b>=2**63:
        assert n==34 and s.status==2 and s.bank[0]==saved==(a,b,1)
        s.command('SSTAT',[]);s.read_tuple(0);break
    a,b=next_a,next_b;assert s.bank[0]==(a,b,1) and s.status==0
    s.read_tuple(0)
program=OUT/'program.txt';program.write_text('\n'.join(s.lines)+'\n')
write('oracle.json',dict(rows=rows,first_unrepresentable_boost=n,preserved_tuple=list(saved),
                        model_error_ratio=str(Fraction(literal[-1][0],1024))))
image=OUT/'cpu.vvp'
argv=['iverilog','-g2012','-s','spu13_core_surd_tb','-o',str(image)]
for directory in sorted({q.parent for q in (SNAP/'hardware/rtl').rglob('*') if q.suffix in ('.v','.vh')}):
    argv+=['-y',str(directory),'-I',str(directory)]
for directory in ['hardware/vendor/gowin','hardware/vendor/ice40','hardware/tests/common']:
    argv+=['-y',str(ROOT/directory),'-I',str(ROOT/directory)]
argv+=['-I',str(SNAP),'-I',str(ROOT),str(ROOT/'hardware/tests/spu13/spu13_core_surd_tb.v')]
write('compile_command.json',argv)
source_files=list((SNAP/'hardware/rtl').rglob('*.v'))+list((SNAP/'hardware/rtl').rglob('*.vh'))
source_files+=list((ROOT/'hardware/tests/spu13').glob('spu13_core_surd*'))
source_files+=[ROOT/'software/experiments/surd_cpu_stream.py',ROOT/'software/tools/surd_cpu_encoding.py',Path(__file__),program]
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
write('source_hashes.json',hashes)
deadline=time.monotonic()+50
def execute(args,log):
    with (OUT/log).open('w') as f:
        return subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,
                              timeout=max(0.1,deadline-time.monotonic())).returncode
assert execute(argv,'compile.log')==0
compiled_names=re.findall(r'"([^"]+)"',image.read_text().split('.file_names')[-1])
used=sorted({str((ROOT/name).resolve()) for name in compiled_names if name.endswith(('.v','.vh'))})
write('compiled_sources.json',used)
assert all(name.startswith(str(SNAP/'hardware/rtl')) for name in used if '/hardware/rtl/' in name)
run=['vvp',str(image),'+PROGRAM='+str(program)];write('run_command.json',run)
assert execute(run,'runtime.log')==0
log=(OUT/'runtime.log').read_text()
assert 'PASS canonical CPU directed execution and complete kernel stream' in log
instructions=re.findall(r'^INS (.*)$',log,re.M)
assert len(instructions)==sum(int(line.split()[0]) not in (8,9,10) for line in s.lines)
assert sum(int(line.split()[-1])!=0 for line in instructions)==2
# Poison one expected arithmetic write; the same harness must fail.
poison=s.lines.copy()
index=next(i for i,line in enumerate(poison) if line.split()[1].startswith('73'))
fields=poison[index].split();fields[4]=f'{int(fields[4],16)^1:016x}';poison[index]=' '.join(fields)
bad=OUT/'poisoned_program.txt';bad.write_text('\n'.join(poison)+'\n')
assert execute(['vvp',str(image),'+PROGRAM='+str(bad)],'negative_control.log')!=0
assert 'atomic tuple mismatch' in (OUT/'negative_control.log').read_text()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
write('results.json',dict(status='PASS_FOCUSED_LORENTZ_CPU_SIMULATION',boost_cases=10,
    rtl_retired_instructions=len(instructions),overflow_boost=34,failed_destination_preserved=True,
    malformed_boost_invariant=-8,poisoned_expectation_rejected=True,arrival_model_disagreements=9,
    final_gamma=262087,wrong_final_gamma=1024,model_error_ratio='262087/1024',
    scope='Dispatch-port RTL simulation; c=1 and unit-proper-time final cruise; acceleration duration excluded',
    full_repository_qualification=False,physical_trajectory_qualification=False,
    board_timing='UNMEASURED',energy='UNMEASURED',silicon_verified=False))
print('PASS exact Lorentz CPU simulation:',len(instructions),'retirements; overflow at boost34; model counterexample confirmed')
