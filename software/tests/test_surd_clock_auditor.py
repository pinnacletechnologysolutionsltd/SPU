"""Port and retained-clock controls for the repaired hierarchy walker."""
import copy
import json
from pathlib import Path
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.audit_surd_cpu_mapping import bind_ports, audit

module = dict(ports=dict(clk=dict(bits=[1],direction='input'),
                        optional=dict(bits=[2],direction='output'),
                        unused=dict(bits=[3],direction='input')),
              cells=dict(ff=dict(connections=dict(C=[1], Q=[2]))))
unions = []
def bind(m,b):
    bind_ports(m,b,'child',lambda scope,bit:(scope,bit),lambda a,b:unions.append((a,b)))
bind(module, {'clk':['parent-clock']})
assert unions == [(('child',1),'parent-clock')]
bind(module, {'clk':['parent-clock'], 'optional':[]})
for bindings in ({}, {'clk':[]}, {'clk':['a'],'unknown':['b']}):
    try:bind(module,bindings)
    except ValueError:pass
    else:raise AssertionError('Malformed/missing required binding accepted')
used=copy.deepcopy(module);used['cells']['ff']['connections']['D']=[3]
try:bind(used,{'clk':['a']})
except ValueError:pass
else:raise AssertionError('Consumed omitted input accepted')
# Aliased child ports union to the same parent signal without dropping either.
alias=dict(ports=dict(a=dict(bits=[1],direction='input'),b=dict(bits=[1],direction='input')),cells={})
unions.clear();bind(alias,{'a':['clock'],'b':['clock']});assert len(unions)==2
invalid=copy.deepcopy(module);invalid['ports']['clk']['direction']='unknown'
try:bind(invalid,{'clk':['clock']})
except ValueError:pass
else:raise AssertionError('Unknown direction accepted')
source=ROOT/'build/spu_surd_register/main_cpu_integration_20261007/integrated_build_04/cpu_1.json'
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    result=audit(source,tmp/'valid.json',1)
    assert result['required_unconstrained_clocks']==0 and result['cpu_clock_endpoints']
    design=json.loads(source.read_text())
    for m in design['modules'].values():
        ff=next((c for c in m['cells'].values() if c['type'].startswith('FD')),None)
        if ff:ff['connections']['C']=['0'];break
    (tmp/'bad.json').write_text(json.dumps(design))
    try:audit(tmp/'bad.json',tmp/'invalid.json',1)
    except ValueError:pass
    else:raise AssertionError('Untimed required endpoint accepted')
print('PASS optional ports, required inputs, width/unknown-port rejection and retained clock controls')
