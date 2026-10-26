"""Canonical experimental Surd encodings; no WF profile or arithmetic folding."""
SURD_OPCODES = dict(SLI=0x70, SLD=0x71, SRD=0x72, SMUL=0x73,
                    SADD=0x74, SSUB=0x75, SNORM=0x76, SSTAT=0x77)


def encode_surd(mnemonic, args):
    counts = dict(SLI=3, SLD=1, SRD=2, SMUL=3, SADD=3, SSUB=3, SNORM=2, SSTAT=0)
    if len(args) != counts[mnemonic]:
        raise ValueError(f'{mnemonic} requires {counts[mnemonic]} operands')

    def register(token):
        if not token.upper().startswith('S'):
            raise ValueError('Surd tuple register must be S0..S7')
        index = int(token[1:])
        if not 0 <= index < 8:
            raise ValueError('Surd register index outside 0..7')
        return index

    r1 = register(args[0]) if args else 0
    r2 = p = 0
    if mnemonic in ('SLI', 'SRD'):
        r2 = int(args[1], 0)
        if not 0 <= r2 < 6:
            raise ValueError('Surd slice index outside 0..5')
        if mnemonic == 'SLI':
            p = int(args[2], 0)
            if not 0 <= p < 1 << 32:
                raise ValueError('SLI payload must be unsigned 32-bit')
    elif mnemonic in ('SMUL', 'SADD', 'SSUB', 'SNORM'):
        r2 = register(args[1])
        if mnemonic != 'SNORM':
            p = register(args[2]) << 16
    return SURD_OPCODES[mnemonic] << 56 | r1 << 48 | r2 << 40 | p << 8
