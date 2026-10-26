"""Count instantiated resources and prove every synchronous clock's origin."""
import json
from collections import Counter
from pathlib import Path
def integer(value):
    if isinstance(value, int):
        return value
    return int(value, 2) if set(value) <= {'0', '1'} else int(value)


def bind_ports(module, bindings, scope, signal, union):
    """Unbound outputs remain private; only proven unused inputs may be omitted."""
    ports = module['ports']
    if set(bindings) - set(ports):
        raise ValueError('Unknown hierarchy port: '+scope)
    used = {bit for cell in module['cells'].values()
            for bits in cell['connections'].values() for bit in bits}
    used.update(bit for spec in ports.values() if spec['direction'] != 'input'
                for bit in spec['bits'])
    for port, spec in ports.items():
        if spec['direction'] not in ('input', 'output', 'inout'):
            raise ValueError('Unknown port direction: '+scope+'/'+port)
        if not bindings.get(port):
            if spec['direction'] == 'output':
                continue
            if spec['direction'] == 'input' and not used.intersection(spec['bits']):
                continue
            raise ValueError('Unbound required input/inout: '+scope+'/'+port)
        if len(spec['bits']) != len(bindings[port]):
            raise ValueError('Hierarchy port width mismatch: '+scope+'/'+port)
        for bit, outer in zip(spec['bits'], bindings[port]):
            union(signal(scope, bit), outer)

def audit(path, output, enabled):
    design = json.loads(Path(path).read_text())['modules']
    top = 'spu_a7_surd_cpu_bench_top'
    parent = {}
    def find(n):
        parent.setdefault(n,n)
        if parent[n] != n: parent[n] = find(parent[n])
        return parent[n]
    def union(a,b): parent[find(a)] = find(b)
    def signal(scope, bit):
        return 'constant:'+bit if isinstance(bit,str) else scope+'#'+str(bit)
    leaves=[]; ancestors=set()
    def walk(name, scope, bindings=None):
        module=design[name]
        if name in ancestors:
            raise ValueError('Recursive hierarchy: '+scope)
        ancestors.add(name)
        if bindings is not None:
            bind_ports(module, bindings, scope, signal, union)
        for instance,cell in module['cells'].items():
            location=scope+'/'+instance
            connections={p:[signal(scope,b) for b in v] for p,v in cell['connections'].items()}
            child=design.get(cell['type'])
            black=child and integer(child.get('attributes',{}).get('blackbox',0))
            white=child and integer(child.get('attributes',{}).get('whitebox',0))
            if child and not black and not white:
                walk(cell['type'],location,connections)
            else: leaves.append((location,cell,connections))
        ancestors.remove(name)
    walk(top,top)
    for location,cell,c in leaves:
        if cell['type'] in ('IBUF','BUFG'):
            union(c['O'][0],c['I'][0])
        elif cell['type'].startswith(('BUFG','MMCM','PLL')):
            raise ValueError('Unreviewed clock primitive: '+location)
        elif cell['type']=='GND':union(c['G'][0],'constant:0')
        elif cell['type']=='VCC':union(c['P'][0],'constant:1')
    clock_bit=design[top]['ports']['sys_clk']['bits']
    if len(clock_bit)!=1:raise ValueError('Expected one external CPU clock')
    clock=find(signal(top,clock_bit[0]))
    cpu_endpoints=[]; all_endpoints=[]; counts=Counter(); dsp_by_hierarchy=Counter(); required=[]
    for location,cell,c in leaves:
        kind=cell['type']; counts[kind]+=1
        if kind=='DSP48E1':
            hierarchy=location.rsplit('/',1)[0]; dsp_by_hierarchy[hierarchy]+=1
            keys=('AREG','BREG','CREG','DREG','ADREG','MREG','PREG','ACASCREG','BCASCREG',
                  'ALUMODEREG','OPMODEREG','INMODEREG','CARRYINREG','CARRYINSELREG')
            if not all(k in cell['parameters'] for k in keys):
                raise ValueError('Unspecified DSP register configuration: '+location)
            if not any(integer(cell['parameters'][k]) for k in keys):continue
            raise ValueError('Registered DSP configuration needs a timing-coverage amendment: '+location)
        elif kind.startswith('FD'):
            controls={'FDRE':'R','FDSE':'S','FDCE':'CLR','FDPE':'PRE'}
            if kind not in controls:
                raise ValueError('Unreviewed flop primitive: '+location)
            for pin in ('C','D','Q','CE',controls[kind]):
                if pin not in c or len(c[pin]) != 1:
                    raise ValueError('Missing/invalid required flop pin: '+location+'/'+pin)
            clocks=['C']; pins=[]
            if any(find(bit) not in (find('constant:0'),find('constant:1')) for bit in c['D']):pins.append('D')
            for pin in ('CE',)+(('R',) if kind=='FDRE' else ('S',) if kind=='FDSE' else ()):
                if pin in c and any(find(bit) not in (find('constant:0'),find('constant:1')) for bit in c[pin]):
                    pins.append('SR' if pin in ('R','S') else pin)
            required.append(dict(instance=location,cell_type=kind,clock_port='CLK',setup_ports=pins))
        elif kind.startswith(('SRL','RAM')):
            raise ValueError('Memory timing coverage requires a contract amendment: '+location)
        elif kind.startswith(('LD','$')):
            raise ValueError('Unreviewed sequential/unmapped cell: '+location)
        else:
            if any(p in c for p in ('CLK','CLKA','CLKB','C')):
                raise ValueError('Unknown timed primitive: '+location)
            continue
        for port in clocks:
            if port not in c or len(c[port])!=1 or find(c[port][0])!=clock:
                raise ValueError('Unconstrained or generated required clock: '+location+'/'+port)
            all_endpoints.append(location+'/'+port)
            if '/cpu/' in location:cpu_endpoints.append(location+'/'+port)
    if not cpu_endpoints:raise ValueError('Vacuous CPU clock audit')
    if enabled:
        # Use hierarchy module identity for product instance name variants.
        surd_locations=[n for n,v in dsp_by_hierarchy.items() if 'u_surd' in n and 'products' in n]
        if sum(dsp_by_hierarchy[n] for n in surd_locations)!=80:
            raise ValueError('Expected all 80 Surd product DSPs')
    if counts['DSP48E1']>240:raise ValueError('DSP capacity exceeded')
    report=dict(status='PASS_SYNCHRONOUS_CLOCK_ORIGIN',clock_domains=['sys_clk'],
                period_ns=40.0,cpu_clock_endpoints=cpu_endpoints,
                all_clock_endpoints=all_endpoints,primitive_counts=dict(counts),
                dsp_by_instance_hierarchy=dict(dsp_by_hierarchy),
                required_timing_endpoints=required,
                required_unconstrained_clocks=0,
                external_scope='rst_n asynchronous reset and checksum observation I/O have no board timing claim')
    Path(output).write_text(json.dumps(report,indent=2)+'\n')
    return report
