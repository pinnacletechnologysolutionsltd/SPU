"""Fixed paired host cohorts; each request is one freshly budgeted arithmetic case."""
from .bounded import execute
from .baseline import MantissaCounter

NAMES = ('million_forward', 'inverse_composition', 'mixed_mantissa', 'norm',
         'bounded_expansion', 'unavoidable_resource', 'different_exponents')


def run(name, representation):
    baseline = MantissaCounter() if representation == 'mantissa_counter' else None
    aor_destination, aor_norm = (17,-19,23),17
    value = (1,0,0)
    units = failures = requests = 0
    histogram = {}
    count = 1_000_000 if name == 'million_forward' else 128
    for i in range(count):
        operation, left, right, increment = 'STEP', value, None, 1
        if name == 'inverse_composition':
            operation,left,right,increment = 'MUL',(1,0,i+1),(1,0,-i-1),None
        elif name == 'mixed_mantissa':
            operation,left,right,increment = 'MUL',(5,2,1000+i),(5,-2,-1000-i),None
        elif name == 'norm':
            operation,left,increment = 'NORM',(5,2,1000+i),None
        elif name == 'bounded_expansion':
            operation,left,increment = 'EXPAND',(5,2,(i % 25)-12),None
        elif name == 'unavoidable_resource':
            operation,left,increment = 'EXPAND',(1,0,1_000_000+i),None
        elif name == 'different_exponents':
            operation,left,right,increment = 'ADD',(5,2,i),(3,-1,i+1),None
        if representation == 'aor':
            destination = aor_norm if operation == 'NORM' else aor_destination
            result = execute(operation,left,right,increment=increment,destination=destination)
            if result.committed:
                if operation == 'NORM':
                    aor_norm = result.value
                else:
                    aor_destination = result.value
        elif representation == 'mantissa_counter':
            result = baseline.apply(operation,left,right,increment=increment)
        else:
            raise ValueError(representation)
        units += result.attempted
        requests += 1
        histogram[result.status] = histogram.get(result.status,0) + 1
        if result.committed:
            value = result.value if operation != 'NORM' else left
        else:
            failures += 1
    return dict(final_tuple=baseline.tuple() if baseline else aor_destination,
                norm_destination=baseline.norm_destination if baseline else aor_norm,
                requests=requests,attempted_units=units,failures=failures,status_histogram=histogram,
                budget_scope='100,000 units per request; cohort aggregate is not one arithmetic case')
