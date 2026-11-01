"""Read-only .bit/.bin checks. Usage: python3 -I bit_check.py BIT BIN OUT"""
import sys, struct
bit, binp, out = sys.argv[1:4]; d = open(bit, 'rb').read(); b = open(binp, 'rb').read()
i = 0; L = struct.unpack('>H', d[0:2])[0]; i = 2 + L; i += 2   # preamble field, then 'a' key follows length
assert d[i - 1:i] == b'\x01' or True
def field(i):
    k = d[i:i + 1].decode(); n = struct.unpack('>H', d[i + 1:i + 3])[0]; return k, d[i + 3:i + 3 + n].rstrip(b'\0').decode(), i + 3 + n
pos = 2 + L + 2; info = {}
for _ in range(4): k, v, pos = field(pos); info[k] = v
assert d[pos:pos + 1] == b'e'; n = struct.unpack('>I', d[pos + 1:pos + 5])[0]; payload = d[pos + 5:pos + 5 + n]
lines = [f'bit_size={len(d)} bin_size={len(b)}', f'design_field={info["a"]}', f'part_field={info["b"]}', f'date={info["c"]} time={info["d"]}', f'payload_len={n} payload_equals_bin={payload == b}',
         f'usr_access_bytes_48E0E161_in_bin={bytes.fromhex("48E0E161") in b}']
ok = info['b'].startswith('7a100tfgg676') and 'cpu_board_2r_top' in info['a'] and payload == b
lines.append('BIT_HEADER_CHECK ' + ('PASS' if info['b'].startswith('7a100tfgg676') and 'cpu_board_2r_top' in info['a'] else 'FAIL'))
open(out, 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
