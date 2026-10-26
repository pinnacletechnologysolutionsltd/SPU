"""Manual literal outcomes transcribed from the ratified fixture document."""
L, H = -(1 << 63), (1 << 63)-1
KMIN, KMAX = -(1 << 31), (1 << 31)-1
D = (17, -19, 23)
# id, operation, left, right, increment, status, successful value, charged units
ROWS = (
    ('F01','MUL',(5,2,1000),(5,-2,-1000),None,'OK',(13,0,0),4),
    ('F02','MUL',(1,0,1000),(1,0,-1000),None,'OK',(1,0,0),4),
    ('F03','ADD',(5,2,7),(3,-1,7),None,'OK',(8,1,7),4),
    ('F04','SUB',(5,2,7),(3,-1,7),None,'OK',(2,3,7),4),
    ('F05','ADD',(5,2,7),(3,-1,8),None,'UNSUPPORTED_OPERATION',None,1),
    ('F06','SUB',(5,2,7),(3,-1,8),None,'UNSUPPORTED_OPERATION',None,1),
    ('F07','EXPAND',(0,0,1000),None,None,'OK',(0,0,0),0),
    ('F08','EXPAND',(0,0,KMIN),None,None,'OK',(0,0,0),0),
    ('F09','STEP',(0,0,KMAX),None,1,'OK',(0,0,0),0),
    ('F10','EXPAND',(0,0,KMAX+1),None,None,'INVALID_INPUT',None,0),
    ('F11','STEP',(1,0,KMAX),None,1,'EXPONENT_OVERFLOW',None,1),
    ('F12','MUL',(0,0,KMAX),(1,0,1),None,'EXPONENT_OVERFLOW',None,1),
    ('F13','MUL',(0,0,7),(1,0,8),None,'OK',(0,0,0),4),
    ('F14','MUL',(L,L,0),(L,L,0),None,'MANTISSA_OVERFLOW',None,4),
    ('F15','CONJ',(0,L,KMIN),None,None,'EXPONENT_OVERFLOW',None,1),
    ('F16','CONJ',(0,L,0),None,None,'MANTISSA_OVERFLOW',None,2),
    ('F17','NORM',(5,2,1000),None,None,'OK',13,3),
    ('F18','NORM',(0,L,0),None,None,'NORM_OVERFLOW',None,3),
    ('F19','EXPAND',(2,-1,1),None,None,'OK',(1,0,0),6),
    ('F20','EXPAND',(1,0,1),None,None,'OK',(2,1,0),6),
    ('F21','EXPAND',(1,0,-1),None,None,'OK',(2,-1,0),6),
    ('F22','EXPAND',(H,0,1),None,None,'EXPANSION_OVERFLOW',None,6),
    ('F23','EXPAND',(5,2,0),None,None,'OK',(5,2,0),1),
    ('F24','MUL',(True,0,0),(1,0,0),None,'INVALID_INPUT',None,0),
    ('F25','UNKNOWN',(1,0,0),None,None,'UNSUPPORTED_OPERATION',None,0),
)


def check(row, result):
    name, operation, _, _, _, status, value, units = row
    destination = 17 if operation == 'NORM' else D
    expected = value if status == 'OK' else destination
    if (result.status, result.value, result.attempted, result.admitted, result.committed) != (
            status, expected, units, units, status == 'OK'):
        raise AssertionError((name, 'Literal mismatch', result))
