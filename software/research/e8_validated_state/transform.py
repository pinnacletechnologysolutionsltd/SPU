"""LEFT-only internal transition with trusted-table closure; no repeated Gram check."""


def transform(owner,key,j,side):
    m,ctx=owner._m,owner._ctx
    m.stage='transform/guard'
    m.test(type(side) is str,'SIDE_TYPE','type_check')
    m.test(side=='left','UNSUPPORTED_INTERNAL_OPERATION')
    uid,images=owner._state(key)
    m.scalar(j,committed=True)
    m.test(0 <= j < 8,'GENERATOR_INDEX','range_compare')
    m.stage='transform/update'
    name='transform/scratch'
    m.allocate(name,32+64)
    updated=[0]*8
    for i in m.loop(8):
        root=m.read(images,i)
        row=m.read(ctx.reflections,j)
        value=m.scalar(m.read(row,root),committed=True)
        m.test(0 <= value < 240,'TRANSFORM_TABLE_RANGE','range_compare')
        m.write(updated,i,value)
    m.stage='transform/commit'
    # All guards precede publication; old immutable tuple remains valid on refusal.
    m.charge('move',8); m.charge('indexed_write')
    owner._states[key]=(uid,tuple(updated))
    m.release(name)
    return key
