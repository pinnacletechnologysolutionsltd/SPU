"""Separate preparation fixtures; the frozen D4/E8 120-case corpus is untouched."""


def plan():
    words = [('identity',())]+[(f'simple/{j}',(j,)) for j in range(8)]
    words += [('left-order',(0,2)),('reverse-order',(2,0)),
              ('inverse-pair',(0,2,2,0)),('diverse',(7,0,3,1,5,2,6,4)),
              ('repeated',(0,2)*4),('diverse-16',(7,0,3,1,5,2,6,4)*2)]
    return dict(status='PREPARATION_NOT_QUALIFIED',
                coordinate_scale=2, chronological_token_side='LEFT',
                cases=[dict(id=name,kind='word',tokens=list(word)) for name,word in words]+
                      [dict(id='longest-minus-identity',kind='negative_identity')],
                vectors=[(1,1,1,1,1,1,1,1),(2,2,0,0,0,0,0,0),(3,1,1,1,1,1,1,3)])
