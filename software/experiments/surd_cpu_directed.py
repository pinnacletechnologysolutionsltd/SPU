"""Directed CPU contract checks; all arithmetic is performed by the RTL stream."""
from software.experiments.surd_wide_correctness_vectors import vectors


def directed(stream):
    for row in vectors(64):
        stream.reset()
        stream.load(2,(17,-19,23))
        x = row['operands'][:3]
        y = row['operands'][3:]
        stream.load(0,x)
        stream.load(1,y)
        stream.command('SMUL',['S2','S0','S1'])
        stream.command('SSTAT',[])
        stream.read_tuple(2)
    for op, x, y in (
        ('SADD',(3,-4,5),(-2,7,11)),
        ('SSUB',(-(1<<63),0,1),(1,0,1)),
        ('SADD',(1,0,(1<<64)-1),(-1,0,2)),
        ('SADD',(-1,-2,1),(1,2,(1<<64)-1)),
        ('SSUB',(-1,2,(1<<64)-1),(-1,2,1)),
        ('SADD',(2,-1,3),(-2,1,3)),
        ('SSUB',(2,-1,3),(2,-1,3)),
        ('SMUL',(0,0,2),(7,-3,3)),
        ('SMUL',(-(1<<63),0,1),(1,0,1))):
        stream.reset()
        stream.load(0,x);stream.load(1,y)
        stream.command(op,['S0','S0','S1'])
        stream.read_tuple(0)
        stream.command('SNORM',['S0','S0'])
        stream.read_tuple(0)
    stream.reset()
    stream.command('SNORM',['S0','S0'])
    stream.load(0,(0,0,6));stream.command('SNORM',['S1','S0'])
    stream.command('SNORM',['S1','S1']);stream.read_tuple(1)
    stream.load(0,(6,-9,3));stream.command('SNORM',['S1','S0'])
    stream.read_tuple(1)
    for word in (0x7308000000000000,0x7300080000000000,0x7300000008000000,
                 0x7300000800000000,0x7300000000080000,
                 0x7600000000000001,0x7000060000000000):
        stream.row(1,word,code=4)
        stream.status=4;stream.command('SSTAT',[])
    stream.load(2,(17,-19,23));stream.load(2,(0,0,0));stream.read_tuple(2)
    for kind in (4,3):
        stream.reset()
        stream.load(0,((1<<63)-1,(1<<63)-1,(1<<64)-1))
        stream.load(1,((1<<63)-1,(1<<63)-1,(1<<64)-1))
        stream.command('SMUL',['S2','S0','S1'],kind=kind)
        if kind==3:
            # The testbench cancels this operation and resets all tuple validity.
            stream.bank=[None]*8;stream.status=0;stream.staged={};stream.target=None
            stream.command('SNORM',['S2','S2'])
        else:
            stream.read_tuple(2) if stream.bank[2] else stream.command('SNORM',['S2','S2'])
