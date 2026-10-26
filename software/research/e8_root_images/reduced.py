"""Conventional lowest-ID right-descent reduction with inversion-count witnesses."""
from .tables import context
from .descriptor import admit, right, from_word, simple_matrix


def length(images, ctx=None):
    ctx = context() if ctx is None else ctx
    matrix = simple_matrix(images,ctx)
    count = 0
    for i in ctx.positive_ids:
        coefficients = ctx.coefficients[i]
        result = tuple(sum(a*b for a,b in zip(row,coefficients)) for row in matrix)
        if all(v <= 0 for v in result) and any(result):
            count += 1
        elif not (all(v >= 0 for v in result) and any(result)):
            raise ValueError('IMAGE_ROOT_SIGN')
    return count


def reduced_word(images, ctx=None):
    ctx = context() if ctx is None else ctx
    original = admit(images,ctx)
    current, remaining, result, steps = original,length(original,ctx),[],[]
    if remaining > 120:
        raise ValueError('COXETER_LENGTH_BOUND')
    while current != ctx.basis_ids:
        if len(result) == 120:
            raise ValueError('REDUCTION_WORK_LIMIT')
        candidates = [j for j,i in enumerate(current)
                      if all(v <= 0 for v in ctx.coefficients[i]) and any(ctx.coefficients[i])]
        if not candidates:
            raise ValueError('NO_RIGHT_DESCENT')
        j = min(candidates)
        current = right(current,j,ctx)
        updated = length(current,ctx)
        if updated != remaining-1:
            raise ValueError('DESCENT_LENGTH_MISMATCH')
        steps.append((j,remaining,updated)); remaining = updated
        result.append(j)
    if remaining != 0 or from_word(result,ctx) != original:
        raise ValueError('REDUCED_WORD_RECONSTRUCTION')
    return dict(tokens=tuple(result), length=len(result), steps=tuple(steps),
                convention='chronological left action; right-stripping order retained',
                costs='NOT INSTRUMENTED; conventional exact reference only')
