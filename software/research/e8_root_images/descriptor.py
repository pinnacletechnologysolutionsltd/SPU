"""Exact Gram admission, sided composition, inverse and materialization references."""
from ..lattice_symmetry.roots import member
from .tables import context
from .linear import columns, multiply, transpose, apply as matvec, integers


def admit(images, ctx=None):
    ctx = context() if ctx is None else ctx
    if type(images) not in (list,tuple) or len(images) != 8:
        raise ValueError('DESCRIPTOR_SHAPE')
    if any(type(i) is not int or not 0 <= i < 240 for i in images):
        raise ValueError('DESCRIPTOR_INDEX')
    if len(set(images)) != 8:
        raise ValueError('DESCRIPTOR_DUPLICATE')
    for i in range(8):
        for j in range(i,8):
            dot = sum(a*b for a,b in zip(ctx.roots[images[i]],ctx.roots[images[j]]))
            if dot != 4*ctx.gram[i][j]:
                raise ValueError('DESCRIPTOR_GRAM')
    return tuple(images)


def token(j):
    if type(j) is not int or not 0 <= j < 8:
        raise ValueError('GENERATOR_INDEX')


def left(images, j, ctx=None):
    ctx = context() if ctx is None else ctx
    images = admit(images,ctx); token(j)
    return admit(tuple(ctx.reflections[j][i] for i in images),ctx)


def right(images, j, ctx=None):
    ctx = context() if ctx is None else ctx
    images = admit(images,ctx); token(j)
    beta = tuple(ctx.roots[i] for i in images)
    return admit(tuple(ctx.index(tuple(x-ctx.gram[i][j]*y for x,y in zip(beta[i],beta[j])))
                       for i in range(8)),ctx)


def from_word(word, ctx=None):
    ctx = context() if ctx is None else ctx
    if type(word) not in (list,tuple) or len(word) > 256:
        raise ValueError('WORD_LIMIT')
    result = ctx.basis_ids
    for j in word:
        result = left(result,j,ctx)
    return result


def cartesian(images, ctx=None):
    ctx = context() if ctx is None else ctx
    images = admit(images,ctx)
    return multiply(columns(tuple(ctx.roots[i] for i in images)),ctx.inverse_basis)


def simple_matrix(images, ctx=None):
    ctx = context() if ctx is None else ctx
    images = admit(images,ctx)
    return columns(tuple(ctx.coefficients[i] for i in images))


def apply(images, vector, ctx=None):
    ctx = context() if ctx is None else ctx
    images = admit(images,ctx)
    if type(vector) not in (list,tuple) or len(vector) != 8 or not member(vector):
        raise ValueError('E8_LATTICE_INPUT')
    coefficients = integers(matvec(ctx.inverse_basis,vector))
    result = tuple(sum(coefficients[i]*ctx.roots[images[i]][j] for i in range(8)) for j in range(8))
    if not member(result):
        raise ValueError('E8_LATTICE_OUTPUT')
    return result


def compose(left_images, right_images, ctx=None):
    ctx = context() if ctx is None else ctx
    u,v = admit(left_images,ctx),admit(right_images,ctx)
    return admit(tuple(ctx.index(apply(u,ctx.roots[i],ctx)) for i in v),ctx)


def inverse(images, ctx=None):
    ctx = context() if ctx is None else ctx
    matrix = transpose(cartesian(images,ctx))
    return admit(tuple(ctx.index(integers(matvec(matrix,alpha))) for alpha in ctx.basis),ctx)
