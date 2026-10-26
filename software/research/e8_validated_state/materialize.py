"""Metered exact coordinate export; vector admission/conversion/validation included."""
from ..lattice_drycount.admission import lattice
from ..lattice_drycount.exact import add,multiply,quotient


def materialize(owner,key,vector):
    m,ctx=owner._m,owner._ctx
    m.stage='export_vector/guard'
    _,images=owner._state(key)
    m.test(type(vector) in (tuple,list),'VECTOR_TYPE','type_check')
    m.test(len(vector)==8,'VECTOR_SHAPE','shape_compare')
    m.allocate('vector/input',64+8*64)
    copied=[0]*8
    for i in m.loop(8):
        m.write(copied,i,m.scalar(m.read(vector,i),committed=True))
    m.stage='export_vector/admission'
    lattice(m,copied,'E8')
    m.stage='export_vector/decode_basis'
    m.allocate('vector/coefficients',64+8*64)
    coefficients=[0]*8
    for i in m.loop(8):
        total=(m.constant(0),m.constant(1))
        row=m.read(ctx.inverse_basis,i)
        for j in m.loop(8):
            factor=m.read(row,j)
            m.charge('indexed_read',2)
            value=(m.read(copied,j),m.constant(1))
            total=add(m,total,multiply(m,(factor.numerator,factor.denominator),value))
        m.write(coefficients,i,m.scalar(quotient(m,total[0],total[1]),committed=True))
    m.stage='export_vector/apply'
    ticket=owner._ticket(); name='export/'+str(ticket)
    m.allocate(name,320+8*64)
    output=[0]*8
    for j in m.loop(8):
        total=m.constant(0)
        for i in m.loop(8):
            root=m.read(ctx.roots,m.read(images,i))
            total=m.op('add',total,m.op('multiply',m.read(coefficients,i),m.read(root,j)))
        m.write(output,j,m.scalar(total,committed=True))
    m.stage='export_vector/validation'
    lattice(m,output,'E8')
    m.stage='export_vector/publish'
    m.release('vector/coefficients'); m.release('vector/input')
    return owner._publish(name,tuple(output))
