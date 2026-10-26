"""Full external import validation; serialization export trusts registered state."""
from ..e8_workload_preparation.left_kernel import admit


def import_wire(owner,packet):
    m=owner._m
    m.stage='import/wire'
    m.test(type(packet) is bytes,'WIRE_TYPE','type_check')
    m.test(len(packet)==76,'WIRE_LENGTH','shape_compare')
    m.allocate('import/packet',64+76*8)
    m.allocate('import/images',32+64)
    copied=[0]*76
    for i in m.loop(76):
        m.write(copied,i,m.read(packet,i))
    for i in m.loop(68):
        m.test(m.read(copied,i)==m.read(owner._prefix,i),'WIRE_SCHEMA_OR_CONTEXT')
    images=[0]*8
    for i in m.loop(8):
        m.write(images,i,m.read(copied,m.op('add',68,i)))
    m.stage='import/gram'
    admit(m,images,owner._ctx)
    m.stage='import/publish'
    key=owner._mint(images)
    m.release('import/images'); m.release('import/packet')
    return key


def export_wire(owner,key):
    m=owner._m
    m.stage='export_wire/guard'
    _,images=owner._state(key)
    ticket=owner._ticket(); name='export/'+str(ticket)
    m.allocate(name,320+76*8)  # buffer metadata192 + registry128 + payload
    result=[0]*76
    m.stage='export_wire/copy'
    for i in m.loop(68):
        m.write(result,i,m.read(owner._prefix,i))
    for i in m.loop(8):
        value=m.scalar(m.read(images,i),committed=True)
        m.test(0 <= value < 240,'EXPORT_INDEX','range_compare')
        m.write(result,m.op('add',68,i),value)
    m.stage='export_wire/publish'
    return owner._publish(name,bytes(result))
