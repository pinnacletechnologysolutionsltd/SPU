"""Frozen CPU-BOARD-4C parser. Scans a raw byte stream for 33-byte v1 records: a5 01 status mask pc | 6 x u32le | crc32le (zlib.crc32 of bytes 0-28)."""
import struct, zlib
EXPECTED = bytes.fromhex('a5 01 01 3f 0e' '0d000000 00000000 04000000 00000000 09000000 00000000' '422b6b75'.replace(' ', ''))
assert len(EXPECTED) == 33 and zlib.crc32(EXPECTED[:29]) == int.from_bytes(EXPECTED[29:], 'little') == 0x756b2b42
def scan(data):
    """Return (records, bad, covered): records = [(offset, bytes)] with valid CRC; bad = [(offset, why)] for a5 01 headers that do not form a valid record."""
    recs, bad, covered, i = [], [], bytearray(len(data)), 0
    while i < len(data):
        if data[i:i + 2] == b'\xa5\x01':
            w = data[i:i + 33]
            if len(w) < 33: bad.append((i, 'truncated')); i += 1; continue
            if zlib.crc32(w[:29]) == int.from_bytes(w[29:], 'little') and w[2] in (1, 2): recs.append((i, bytes(w))); covered[i:i + 33] = b'\x01' * 33; i += 33; continue
            bad.append((i, 'crc_or_status')); i += 1; continue
        i += 1
    return recs, bad, covered
def decode(r): return {'status': r[2], 'mask': r[3], 'pc': r[4], 'slices': list(struct.unpack('<6I', r[5:29])), 'crc': '%08x' % int.from_bytes(r[29:], 'little')}
def judge(data, min_offset=0):
    """PASS iff a valid record equal to EXPECTED starts at offset >= min_offset and no valid record with different content exists anywhere at/after it."""
    recs, bad, covered = scan(data)
    good = [o for o, r in recs if r == EXPECTED and o >= min_offset]
    contra = [(o, decode(r)) for o, r in recs if r != EXPECTED]
    first = good[0] if good else None
    contra_after = [c for c in contra if first is not None and c[0] > first] if first is not None else contra
    verdict = 'PASS' if first is not None and not contra_after else 'FAIL'
    unexpected = bytes(b for b, c in zip(data, covered) if not c)
    return {'verdict': verdict, 'valid_records': [(o, decode(r)) for o, r in recs], 'expected_offsets': good, 'contradictory_valid_records': contra, 'bad_headers': bad, 'unexpected_bytes': len(unexpected), 'unexpected_hex': unexpected.hex()}
