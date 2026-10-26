"""Deterministic reuse/materialization plans; preparing a plan does not execute it."""
from ..e8_root_images.tables import context

CLIENTS = (1,4,16,64)
LENGTHS = (8,32,128,256)
CADENCES = (1,4,16,'final')
REGIMES = ('cold_serial','private_lockstep','shared_lockstep')
FAMILIES = ('scrambled','inverse_pair')


def checkpoints(length, cadence):
    if type(length) is not int or length not in LENGTHS:
        raise ValueError('FIXTURE_LENGTH')
    if not (type(cadence) is int and cadence in (1,4,16) or type(cadence) is str and cadence=='final'):
        raise ValueError('FIXTURE_CADENCE')
    return (length,) if cadence == 'final' else tuple(sorted(set(range(cadence,length+1,cadence))|{length}))


def xorshift(value):
    value ^= (value << 13) & 0xffffffff
    value ^= value >> 17
    value ^= (value << 5) & 0xffffffff
    return value & 0xffffffff


def validate(case):
    if type(case) is not dict:
        raise ValueError('FIXTURE_TYPE')
    for field,allowed in (('clients',CLIENTS),('length',LENGTHS),('regime',REGIMES),('family',FAMILIES)):
        expected_type = int if field in ('clients','length') else str
        if field not in case or type(case[field]) is not expected_type or case[field] not in allowed:
            raise ValueError('FIXTURE_'+field.upper())
    checkpoints(case['length'],case.get('cadence'))


def expand(case):
    validate(case)
    ctx = context()
    result = []
    for client in range(case['clients']):
        state = (0xE8000001+client*0x9E3779B9) & 0xffffffff
        state = state or 1
        words = []
        count = case['length']//2 if case['family']=='inverse_pair' else case['length']
        for _ in range(count):
            state = xorshift(state); words.append(state & 7)
        if case['family']=='inverse_pair':
            words += list(reversed(words))
        # Separate deterministic vector seed; words match across every regime/cadence.
        first = xorshift((0xE8123456+client) & 0xffffffff) % 240
        second = (first+17+client) % 240
        scale = (1,17,(1 << 20)-1,(1 << 30)-1)[client % 4]
        vector = tuple(scale*a+b for a,b in zip(ctx.roots[first],ctx.roots[second]))
        if any(abs(v) > (1 << 31) for v in vector):
            raise ValueError('FIXTURE_INPUT_BOUND')
        result.append(dict(client=client,tokens=tuple(words),initial_vector=vector))
    return tuple(result)


def ownership(case):
    validate(case)
    k = case['clients']
    active = 1 if case['regime']=='cold_serial' else k
    contexts = k if case['regime']=='private_lockstep' else 1
    setups = 1 if case['regime']=='shared_lockstep' else k
    return dict(active_clients=active,context_instances_at_peak=contexts,setup_instances=setups,
                root_image_static_lower_bound_bits=contexts*307680,
                limitation='root-image context only; excludes descriptors/workspace; other arms need own inventory')


def plan():
    ctx = context()
    cases=[]
    for family in FAMILIES:
        for length in LENGTHS:
            for k in CLIENTS:
                for cadence in CADENCES:
                    for regime in REGIMES:
                        case=dict(id=f'{family}/L{length}/K{k}/M{cadence}/{regime}',family=family,
                                  length=length,clients=k,cadence=cadence,regime=regime)
                        case['checkpoints']=checkpoints(length,cadence)
                        case['ownership']=ownership(case)
                        cases.append(case)
    return dict(status='PREPARED_NOT_EXECUTED',schema=1,seed_policy='xorshift32 / fixed per-client seeds',
                chronological_token_side='LEFT',observation='w_t(initial_vector), no descriptor reset',
                arms=('eager_coordinates','dense_matrix','ordinary_word','reduced_word','root_images'),
                configs=cases,root_hash=ctx.root_hash,basis_hash=ctx.basis_hash,
                corpus_evaluation='NOT RUN', qualification='HOLD')
