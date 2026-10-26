"""Canonical source validation before encoding or folding; raw words unchanged."""
import re

# Kind strings: scalar R, Quadray Q, integer I, destination/label L.
KINDS = {'LD': 'RII', 'ADD': 'RR', 'SUB': 'RR', 'MUL': 'RR',
         'ROT': 'RR', 'LOG': 'R', 'JINV': 'R', 'JMP': 'L', 'CALL': 'L',
         'REGEN': 'I', 'QLOAD': 'QR', 'QADD': 'QQ', 'QREAD': 'QQ',
         'QSUB': 'QQQ', 'QROT': 'QR', 'ROTC': 'QQI', 'IROTC': 'QQI',
         'SCALE2': 'QQ', 'QLDI': 'QIIII', 'LOAD2X': 'QIIII',
         'DELTA': 'QIII', 'HEX': 'RQ', 'SPREAD': 'RQQ',
         **{m: 'Q' for m in ('QLOG', 'QNORM', 'MIN4', 'IDNT', 'ANNE')},
         **{m: '' for m in ('NOP', 'HALT', 'RET', 'SNAP', 'EQUIL')}}


def register(token, kind=None, brackets=False):
    match = re.fullmatch(r'(QR|R)(?:\[(\d+)\]|(\d+))' if brackets
                         else r'(QR|R)(\d+)', token.upper())
    if not match:
        raise ValueError('invalid register: '+token)
    family = match[1]
    index = int(next(v for v in match.groups()[1:] if v is not None))
    if kind and family != ('QR' if kind == 'Q' else 'R'):
        raise ValueError('wrong register type: '+token)
    if index > (12 if family == 'QR' else 25):
        raise ValueError('register index out of range: '+token)
    return index


def integer(token):
    return int(token[2:] if token.upper().startswith('PH') else token, 0)


def validate(mnemonic, args, labels=None, surface='vm'):
    labels = labels or {}
    # Every register-looking argument is checked, including VM extension args.
    for token in args:
        if token.upper() not in labels and re.match(r'^(QR|R)(?:[-+\d\[])', token.upper()):
            register(token, brackets=surface == 'standalone')
    if mnemonic not in KINDS:
        return  # Extension encoding is validated by its own existing encoder.
    pattern = KINDS[mnemonic]
    counts = {len(pattern)}
    if mnemonic in ('ROT', 'SCALE2', 'QROT'):
        counts = {1, 2}
    elif mnemonic == 'LD':
        counts = {1, 2, 3}
    elif mnemonic == 'QSUB':
        counts = {2, 3}
    elif mnemonic == 'ROTC':
        counts = {2, 3}
    elif mnemonic in ('QLDI', 'LOAD2X'):
        counts = {1, 2, 3, 4, 5} if surface == 'standalone' else {3, 5}
    elif mnemonic == 'DELTA' and surface == 'standalone':
        counts = {1, 2, 3, 4}
    if len(args) not in counts:
        raise ValueError(f'{mnemonic}: expected operand count in {sorted(counts)}, got {len(args)}')
    for kind, token in zip(pattern, args):
        if kind in 'RQ':
            register(token, kind, surface == 'standalone')
        elif kind == 'L' and token.upper() in labels:
            continue
        else:
            value = integer(token)
            if kind == 'L' and not 0 <= value <= 65535:
                raise ValueError('control destination out of range')
    if mnemonic == 'QLOAD' and register(args[1], 'R', surface == 'standalone') > 22:
        raise ValueError('QLOAD needs four consecutive scalar registers')
    if mnemonic in ('ROTC', 'IROTC') and len(args) == 3:
        value = integer(args[2])
        legal = 0 <= value < 64 if mnemonic == 'ROTC' else (0 <= value < 128 and value % 64 < 60)
        if not legal:
            raise ValueError(mnemonic+' selector out of range')
