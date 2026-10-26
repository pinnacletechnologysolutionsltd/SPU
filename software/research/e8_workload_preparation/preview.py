"""Short observer previews only; not cold/warm performance or context allocation."""
from ..e8_root_images import descriptor,reference
from ..e8_root_images.tables import context
from ..e8_root_images.reduced import reduced_word
from .fixtures import expand,checkpoints


def run(case):
    if case['length'] != 8 or case['clients'] not in (1,4):
        raise ValueError('PREVIEW_SCOPE')
    ctx=context()
    observations=[]
    for client in expand(case):
        images=ctx.basis_ids
        for tick,token in enumerate(client['tokens'],1):
            images=descriptor.left(images,token,ctx)
            if tick in checkpoints(case['length'],case['cadence']):
                actual=descriptor.apply(images,client['initial_vector'],ctx)
                prefix=client['tokens'][:tick]
                if actual != reference.word_apply(prefix,client['initial_vector']):
                    raise ValueError('PREFIX_OBSERVER_REFERENCE')
                reduced=reduced_word(images,ctx)
                if descriptor.from_word(reduced['tokens'],ctx) != images:
                    raise ValueError('PREFIX_REDUCED_REFERENCE')
                observations.append(dict(tick=tick,client=client['client'],value=actual))
        if case['family']=='inverse_pair' and images != ctx.basis_ids:
            raise ValueError('INVERSE_PAIR_FINAL_IDENTITY')
    observations.sort(key=lambda row:(row['tick'],row['client']))
    return dict(id=case['id'],status='OBSERVER_PREVIEW_PASS_NOT_MEASUREMENT',observations=observations,
                context_allocation='NOT SIMULATED',arithmetic_work='NOT MEASURED')
