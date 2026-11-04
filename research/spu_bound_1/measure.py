"""Small deterministic measurements. Timings are descriptive, not benchmarks."""
from time import perf_counter_ns
from . import model as m
from . import oracle as o

BOX = ((-2,2),)*4

def run(name):
    m.COUNTS.clear(); t = perf_counter_ns(); interval = m.intervals(name, BOX); ti = perf_counter_ns()-t; ic = dict(m.COUNTS)
    m.COUNTS.clear(); t = perf_counter_ns(); poly = m.polynomials(name); tb = perf_counter_ns()-t; pc = dict(m.COUNTS)
    m.COUNTS.clear(); t = perf_counter_ns(); pb = tuple(m.pbound(p, BOX) for p in poly); tpb = perf_counter_ns()-t; bc = dict(m.COUNTS)
    t = perf_counter_ns(); inputs = list(o.inputs(name)); traces = [o.calculate(name,v) for v in inputs]; te = perf_counter_ns()-t
    t = perf_counter_ns(); values = [t[-1] for t in traces]; exact = o.extrema(values)
    for inp, val in zip(inputs,values):
        assert tuple(m.peval(p,inp) for p in poly) == val
        assert all(lo <= z <= hi for (lo,hi),z in zip(interval,val))
        assert all(lo <= z <= hi for (lo,hi),z in zip(pb,val))
    tc = perf_counter_ns()-t
    allvalues = [z for trace in traces for pair in trace for z in pair]
    maxw = max(m.width(z) for z in allvalues)
    # Width of explicit oracle products and partial sums, with both stages.
    temps = []
    for inp, trace in zip(inputs, traces):
        a,b,c,d = inp
        y = (a,-b) if name in ('F2','F4') else (c,d)
        pairs = [((a,b),y)]
        if name == 'F3':
            pairs.append((trace[0],(y[0],-y[1])))
        for x, y0 in pairs:
            t0=x[0]*y0[0]; t1=3*x[1]*y0[1]
            t2=x[0]*y0[1]; t3=x[1]*y0[0]
            temps.extend((t0,t1,t2,t3,t0+t1,t2+t3))
    tempw = max(m.width(z) for z in temps)
    result = {'fixture':name, 'inputs':len(inputs), 'interval':interval, 'poly_bound':pb,
              'exact':exact, 'terms':[len(p) for p in poly], 'coeff_intermediate_bits':maxw,
              'oracle_product_sum_bits':tempw, 'interval_ops':ic, 'poly_build_ops':pc, 'poly_bound_ops':bc, 'retained_poly':poly, 'ns_interval':ti, 'ns_poly_build':tb,
              'ns_poly_bound':tpb, 'ns_oracle':te, 'ns_check':tc}
    if name == 'F3':
        t = perf_counter_ns(); bound = m.norm_bounds(BOX); result['norm_bound'] = bound
        result['ns_norm_bound'] = perf_counter_ns()-t
        assert all(lo <= z <= hi for val in values for (lo,hi),z in zip(bound,val))
    return result

def main():
    for name in ('F1','F2','F3','F4'):
        print(run(name))
    t5=perf_counter_ns()
    print('F5 square: interval',m.muli((-2,2),(-2,2)), 'polynomial',m.pbound(m.pmul(m.var(0),m.var(0)),BOX), 'corners=(4,4), oracle=(0,4)')
    print('F5 combined calculation ns',perf_counter_ns()-t5)
    t6=perf_counter_ns()
    M=(1<<63)-1
    first=o.multiply((M,0),(2,1)); last=o.multiply(first,(2,-1))
    products = (2*M, M, 2*first[0], -3*first[1], -first[0], 2*first[1])
    x=(m.var(0),m.var(1)); y=(m.const(2),m.const(1))
    poly=m.smul(m.smul(x,y),m.sconj(y))
    box=((M,M),(0,0),(0,0),(0,0))
    iv=m.imul(m.imul(box[:2],((2,2),(1,1))),((2,2),(-1,-1)))
    print('F6 input',M,'first',first,'final',last,'interval',iv,'poly bound',tuple(m.pbound(p,box) for p in poly),'terms',list(map(len,poly)), 'coefficient bits',max(map(m.width,first)),'final bits',max(map(m.width,last)), 'product/sum bits',max(map(m.width,products+first+last)))
    print('F6 combined calculation ns',perf_counter_ns()-t6)

if __name__ == '__main__': main()
