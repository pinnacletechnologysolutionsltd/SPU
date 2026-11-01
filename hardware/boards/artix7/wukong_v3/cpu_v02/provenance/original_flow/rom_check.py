"""Independent ROM-initialization check on a mapped design (RAMB36E1, TDP, x36 ports). Usage:
python3 -I rom_check.py PROPS LOADS FRONTEND_V TB_V OUT
Reconstructs the 16 logical 64-bit ROM words from INIT_xx/INITP_xx and the netlist (address pins, output-pin -> held_word bit),
compares them with two independent sources (frontend.v initial block; testbench expected[]), then proves rejection via negative controls."""
import re, sys, copy
props, loads, fe, tb, outp = sys.argv[1:6]
def parse_props(path):
    cells, cur = {}, None
    for l in open(path):
        p = l.rstrip('\n').split(' ', 2)
        if p[0] == 'CELL': cur = cells.setdefault(p[1], {'prop': {}, 'pin': {}}); cur['ref'] = l.split()[3]
        elif p[0] == 'PROP': cur['prop'][p[1]] = p[2].strip() if len(p) > 2 else ''
        elif p[0] == 'PIN': q = l.split(None, 2); cur['pin'][q[1]] = q[2].strip() if len(q) > 2 else ''
    return cells
def hexval(s): return int(s.split("'h")[1], 16)
def parse_map(path):
    m = {}
    for l in open(path):
        mm = re.match(r'LOAD (\w+)\[(\d+)\] net=\S* loads=(.*)', l)
        if not mm: continue
        j = re.findall(r'held_word_reg\[(\d+)\]/D', mm[3])
        if len(j) == 1: m[(mm[1], int(mm[2]))] = int(j[0])
    return m
def reconstruct(cells, pmap):
    names = [n for n, c in cells.items() if c['ref'] == 'RAMB36E1']
    assert len(names) == 1, f'expected exactly one RAMB36E1, found {names}'
    c = cells[names[0]]; P = c['prop']
    assert P['RAM_MODE'] == 'TDP' and P['READ_WIDTH_A'] == '36' and P['READ_WIDTH_B'] == '36', 'unsupported layout'
    init = sum(hexval(P[f'INIT_{k:02X}']) << (256 * k) for k in range(128))
    initp = sum(hexval(P[f'INITP_{k:02X}']) << (256 * k) for k in range(16))
    def widx(port, pc):  # word index = ADDR[14:5]; non-address-bit pins must be constant
        pre = 'ADDRARDADDR' if port == 'A' else 'ADDRBWRADDR'; idx = 0
        for b in range(5, 15):
            n = c['pin'][f'{pre}[{b}]']
            if n.endswith('<const1>'): v = 1
            elif n.endswith('<const0>'): v = 0
            else: v = (pc >> int(re.search(r'Q\[(\d)\]', n)[1])) & 1 if False else None
            if v is None: break
            idx |= v << (b - 5)
        return pre
    # address bits: constants contribute fixed value; Q[k] pins carry pc bit k
    def index(port, pc):
        pre = 'ADDRARDADDR' if port == 'A' else 'ADDRBWRADDR'; idx = 0
        for b in range(5, 15):
            n = c['pin'][f'{pre}[{b}]']
            v = 1 if n.endswith('<const1>') else 0 if n.endswith('<const0>') else (pc >> int(re.search(r'Q\[(\d)\]$', n)[1])) & 1
            idx |= v << (b - 5)
        return idx
    words = []
    for pc in range(16):
        w = 0; ia, ib = index('A', pc), index('B', pc)
        for (pin, i), L in pmap.items():
            if pin == 'DOADO': bit = (init >> (ia * 32 + i)) & 1
            elif pin == 'DOPADOP': bit = (initp >> (ia * 4 + i)) & 1
            elif pin == 'DOBDO': bit = (init >> (ib * 32 + i)) & 1
            elif pin == 'DOPBDOP': bit = (initp >> (ib * 4 + i)) & 1
            else: continue
            w |= bit << L
        words.append(w)
    return words, sorted(set(pmap.values())), (init, initp)
def src_words():
    f = open(fe).read(); a = {int(k): int(v, 16) if v != '0' else 0 for k, v in re.findall(r"rom\[(\d+)\]=(?:64'h)?([0-9a-fA-F]+|0)\s*;", f)}
    t = open(tb).read(); b = {int(k): int(v, 16) for k, v in re.findall(r"expected\[(\d+)\]=64'h([0-9a-fA-F]+)", t)}
    assert sorted(a) == list(range(16)) and sorted(b) == list(range(14)), (sorted(a), sorted(b))
    assert all(a[k] == b[k] for k in range(14)), 'frontend.v and testbench disagree'
    assert a[14] == 0 and a[15] == 0
    return [a[k] for k in range(16)]
cells = parse_props(props); pmap = parse_map(loads); exp = src_words()
words, bits, (init, initp) = reconstruct(cells, pmap)
ok = words == exp
# bits of the 64-bit word with no load/mapping (trimmed by the tool) must be zero in every expected word
unmapped = [L for L in range(64) if L not in bits]
trim_ok = all(((w >> L) & 1) == 0 for w in exp for L in unmapped)
mapped_mask = sum(1 << L for L in bits)
stray = (init & ~sum(((1 << 32) - 1) << (32 * k) for k in list(range(16)) + list(range(512, 528)))) != 0 or (initp & ~sum(0xF << (4 * k) for k in list(range(16)) + list(range(512, 528)))) != 0
lines = [f'cell {list(cells)[0]} mapped_logical_bits={len(bits)} unmapped_bits={unmapped}']
for pc in range(16): lines.append(f'word[{pc:2d}] hw={words[pc]:016x} expected={exp[pc]:016x} {"OK" if words[pc] == exp[pc] else "MISMATCH"}')
lines.append(f'words_match_all16={ok} unmapped_bits_zero_in_expected={trim_ok} stray_nonzero_init_outside_rom_words={stray}')
# negative controls: each must make the same comparison fail
def rerun(mut):
    c2 = copy.deepcopy(cells); name = list(c2)[0]; mut(c2[name]['prop']); w, _, _ = reconstruct(c2, pmap); return w != exp
def flip(prop, key, bit):
    s = prop[key]; v = hexval(s) ^ (1 << bit); prop[key] = f"256'h{v:064x}"
def zero(p):
    for k in p:
        if k.startswith('INIT'): p[k] = "256'h" + '0' * 64
def swap(p):  # exchange logical words 1 and 2 low halves (INIT_00 words 1,2)
    v = hexval(p['INIT_00']); w1, w2 = (v >> 32) & 0xffffffff, (v >> 64) & 0xffffffff
    v = (v & ~(0xffffffff << 32) & ~(0xffffffff << 64)) | (w2 << 32) | (w1 << 64); p['INIT_00'] = f"256'h{v:064x}"
ctl = {'corrupt_one_bit_word0_low': lambda p: flip(p, 'INIT_00', 8),
       'corrupt_one_bit_word13_high_half': lambda p: flip(p, 'INIT_40', 32 * 13 + 24),
       'corrupt_parity_bit_word0': lambda p: flip(p, 'INITP_00', 0),
       'nonzero_unused_word14': lambda p: flip(p, 'INIT_01', 32 * 6 + 3),
       'swap_words_1_2': swap, 'all_zero_rom': zero}
for n, m in ctl.items(): lines.append(f'negative_control {n}: {"REJECTED" if rerun(m) else "NOT_REJECTED"}')
rej = all(l.endswith('REJECTED') and 'NOT_' not in l for l in lines if l.startswith('negative_control'))
lines.append(f'ROM_CHECK {"PASS" if ok and trim_ok and not stray and rej and len(bits) >= 60 else "FAIL"}')
open(outp, 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
