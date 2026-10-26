"""Isolated metered left update; pairwise admission schedule, not frozen API costs."""
from ..lattice_drycount.meter import Meter
from ..lattice_drycount.ledger import replay
from ..e8_root_images.tables import context,storage_inventory
from ..e8_root_images.descriptor import left


def admit(m,images,ctx):
    m.test(type(images) in (list,tuple),'DESCRIPTOR_SHAPE','type_check')
    m.test(len(images)==8,'DESCRIPTOR_SHAPE','shape_compare')
    with m.frame(8,4):
        for i in m.loop(8):
            index=m.scalar(m.read(images,i),committed=True)
            m.test(0 <= index < 240,'DESCRIPTOR_INDEX','range_compare')
            for j in m.loop(i):
                m.test(index != m.read(images,j),'DESCRIPTOR_DUPLICATE')
        for i in m.loop(8):
            for offset in m.loop(8-i):
                j=m.op('add',i,offset)
                x=m.read(ctx.roots,m.read(images,i))
                y=m.read(ctx.roots,m.read(images,j))
                total=m.constant(0)
                for k in m.loop(8):
                    total=m.op('add',total,m.op('multiply',m.read(x,k),m.read(y,k)))
                gram=m.read(m.read(ctx.gram,i),j)
                m.test(total==m.op('multiply',m.constant(4),gram),'DESCRIPTOR_GRAM')


def run(images,j,trace=False):
    ctx=context()
    m=Meter(trace)
    m.allocate('context',storage_inventory(ctx)['static_total_bits'])
    m.allocate('input_descriptor',32+64)
    with m.frame(8,4):
        m.stage='admission'
        admit(m,images,ctx)
        m.scalar(j,committed=True)
        m.test(0 <= j < 8,'GENERATOR_INDEX','range_compare')
        m.stage='left_update'
        m.allocate('output_descriptor',32+64)
        updated=[0]*8
        for i in m.loop(8):
            root=m.read(images,i)
            table=m.read(ctx.reflections,j)
            m.write(updated,i,m.scalar(m.read(table,root),committed=True))
        m.stage='post_admission'
        admit(m,updated,ctx)
        m.release('input_descriptor')
    report=m.report()
    result=tuple(updated)
    if result != left(images,j,ctx):
        raise ValueError('LEFT_REFERENCE')
    for stage in ('admission','post_admission'):
        assert report['stages'][stage]['multiply']==324,'ADMISSION_MULTIPLY_COUNT'
        # Includes36 index additions as well as288 scalar dot additions.
        assert report['stages'][stage]['add']==324,'ADMISSION_ADD_COUNT'
    report.update(status='SHORT_KERNEL_PREPARATION_NOT_QUALIFICATION',output=result,
                  scope='context resident + paired Gram admission + left update; no setup/wire costs',
                  schedule='explicit pairwise duplicates; frozen reference uses set; not its measured cost',
                  lookup_payload_reads=8,independent_reviewer='PENDING')
    if trace:
        report['ledger_replay']=replay(m.events,report)
    return report,m.events
