"""Private exact product, norm and final publication schedules."""


def products(a, b, c, d, meter):
    """Execute seven scalar actions, each followed by its temporary check.

    The caller checks the raw exponent before entering this function.
    All reads use original private coefficients; no destination is touched.
    Keep 3bd as an explicit action so its charge and any refusal are visible.
    The returned pair is raw: normalization and storage checks follow later.
    This private boundary is also the isolated dropped3bd mutation seam.
    Mutants must change actual arithmetic here, not an unrelated final result.
    """
    ac = meter.scalar('product.ac', lambda: a*c, kind='mul')
    bd = meter.scalar('product.bd', lambda: b*d, kind='mul')
    triple = meter.scalar('product.3bd', lambda: 3*bd, kind='mul')
    first = meter.scalar('product.first', lambda: ac + triple)
    ad = meter.scalar('product.ad', lambda: a*d, kind='mul')
    bc = meter.scalar('product.bc', lambda: b*c, kind='mul')
    second = meter.scalar('product.second', lambda: ad + bc)
    return first, second


def norm(descriptor, meter):
    """Compute four checked actions in signed280, without norm publication.

    U has norm one, so k is irrelevant to this calculation.
    A valid descriptor can have a norm outside the signed128 output range.
    Its value and canonical equality are still valid in that case.
    Only the caller's separate publication check emits NORM_OVERFLOW.
    """
    a, b, _ = descriptor
    aa = meter.scalar('norm.aa', lambda: a*a, 280, 'mul')
    bb = meter.scalar('norm.bb', lambda: b*b, 280, 'mul')
    triple = meter.scalar('norm.3bb', lambda: 3*bb, 280, 'mul')
    return meter.scalar('norm.difference', lambda: aa - triple, 280)


def publish(descriptor, meter):
    """Check a, b, then k and charge the complete tuple publication last.

    The caller holds the old destination until this function succeeds.
    A budget exhausted before atomic.commit cannot publish a partial tuple.
    Temporary-width validity does not imply final stored-width validity.
    A zero result uses this same publication sequence after zero dispatch.
    Returning a tuple preserves the immutable descriptor representation.
    """
    a, b, k = descriptor
    meter.width('final.a', a, 64, 'MANTISSA_OVERFLOW')
    meter.width('final.b', b, 64, 'MANTISSA_OVERFLOW')
    meter.width('final.k', k, 32, 'EXPONENT_OVERFLOW')
    return meter.action('atomic.commit', lambda: descriptor)
