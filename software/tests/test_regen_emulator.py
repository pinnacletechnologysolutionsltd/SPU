"""
test_regen_emulator.py — REGEN emulator gates (ISA_REGEN proposal, 2026-08-20).

Gate 1: reproduce Step 5 on the frozen operand stream (seed 13, m_K, band
        [1000,30000]): conditioned REGEN must recover 100% of valid trials at
        K in {1,2,4,8,16}, dT in {2,5}; uncompensated REGEN must reproduce the
        Step-5 Arm-A degradation (69.2 / 13.1 / 0 / 0 / 0 % at dT=2K).
Gate 2: backend abstraction — photonic / FPGA-reference / digital backends
        yield the IDENTICAL exact architectural state (== oracle) for the
        same block, despite different internal Sigma_total and scale.
Gate 3: block legality (.block K=4 with 3 or 5 ops must fail assembly) and
        REGEN idempotence (REGEN(REGEN(S)) == S).
"""
import os
import random

from regen_emulator import (
    PhotonicBackend, FpgaReferenceBackend, DigitalSurdBackend,
    run_block, parse_block, BlockValidationError, regen_idempotent, regen,
    oracle_block, oracle_exact,
)

M_K = {1: 100, 2: 25, 4: 9, 8: 4, 16: 2}
KS = [1, 2, 4, 8, 16]
BAND = (1000, 30000)

# Step-5 frozen Arm-A (unconditioned, dT=2K, band) for the degradation gate
STEP5_A_2K = {1: 69.17, 2: 13.09, 4: 0.0, 8: 0.0, 16: 0.0}


def frozen_trials(K, seed=13, N=6000):
    """Yield (S0, ops) from the frozen operand stream with the band filter.
    The trial index advances on EVERY draw (rejected trials included), exactly
    as in the frozen sweeps — the band filter must not stall the stream."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_photonic_models_smul import make_master_rng, trial_rng
    # interpreter-agnostic integer draw (numpy Generator vs stdlib Random)
    def rint(rng, lo, hi):
        if hasattr(rng, "integers"):
            return int(rng.integers(lo, hi + 1))
        return rng.randint(lo, hi + 1)
    m = M_K[K]
    master = make_master_rng(seed)
    n = 0
    trial = 0
    while n < N:
        rng = trial_rng(master, trial)
        trial += 1
        a = rint(rng, -m, m); b = rint(rng, -m, m)
        ops = [('smul', (rint(rng, -m, m), rint(rng, -m, m)))
               for _ in range(K)]
        xa, xb = oracle_exact((a, b), ops)
        if BAND[0] <= max(abs(xa), abs(xb)) <= BAND[1]:
            n += 1
            yield (a, b), ops


def gate1():
    print("== Gate 1: reproduce Step 5 ==")
    all_ok = True
    for deltaT in (2.0, 5.0):
        for K in KS:
            backend = PhotonicBackend(deltaT)
            cond_ok = 0
            uncond_ok = 0
            trials = 0
            for S0, ops in frozen_trials(K, N=6000):
                golden = oracle_block(S0, ops)
                trials += 1
                if run_block(backend, S0, ops, 'conditioned') == golden:
                    cond_ok += 1
                if run_block(backend, S0, ops, 'unconditioned') == golden:
                    uncond_ok += 1
            cond_pct = 100.0 * cond_ok / trials
            uncond_pct = 100.0 * uncond_ok / trials
            # degradation gate: at dT=2K, uncompensated REGEN must reproduce
            # the frozen Step-5 Arm-A recovery within MC noise (2.5pt @ 6k)
            if deltaT == 2.0:
                deg_ok = abs(uncond_pct - STEP5_A_2K[K]) <= 2.5
            else:
                deg_ok = True  # dT=5K: Step-5 A was 5.59%/0/0/0; checked loosely
                if K == 1:
                    deg_ok = abs(uncond_pct - 5.59) <= 2.5
            ok = (cond_pct == 100.0) and deg_ok
            all_ok &= ok
            print(f"  dT={deltaT:.1f}K K={K:2d}: conditioned={cond_pct:7.2f}% "
                  f"(must be 100)  unconditioned={uncond_pct:6.2f}% "
                  f"[Step-5 A={STEP5_A_2K[K]:5.2f}% @2K]  "
                  f"{'PASS' if ok else 'FAIL'}")
    print("  Gate 1 result:", "PASS" if all_ok else "FAIL")
    return all_ok


def gate2():
    print("== Gate 2: backend abstraction ==")
    random.seed(7)
    n_ok = n_total = 0
    sig_diff = 0
    for _ in range(3000):
        S0 = (random.randint(-4, 4), random.randint(-4, 4))
        ops = [('smul', (random.randint(-2, 2), random.randint(-2, 2)))
               for _ in range(4)]
        # non-saturated guard: only score trials in the faithful range
        xa, xb = oracle_exact(S0, ops)
        if max(abs(xa), abs(xb)) > 30000:
            continue
        golden = oracle_block(S0, ops)
        res = {}
        metas = {}
        for name, bk in (('photonic', PhotonicBackend(0.0)),
                         ('fpga', FpgaReferenceBackend()),
                         ('digital', DigitalSurdBackend())):
            meas, meta = bk.run(S0, ops)
            res[name] = regen(meas, meta, 'conditioned')
            metas[name] = meta
        n_total += 1
        if res['photonic'] == res['fpga'] == res['digital'] == golden:
            n_ok += 1
        if metas['photonic']['Sigma'] != metas['fpga']['Sigma']:
            sig_diff += 1
    pct = 100.0 * n_ok / n_total
    ok = pct == 100.0
    print(f"  identical exact state across 3 backends == oracle: {n_ok}/{n_total} "
          f"({pct:.1f}%)")
    print(f"  photonic Sigma != fpga Sigma in {sig_diff}/{n_total} trials "
          f"(metadata differs, semantics identical)")
    print("  Gate 2 result:", "PASS" if ok else "FAIL")
    return ok


def gate3():
    print("== Gate 3: block legality + REGEN idempotence ==")
    ok = True
    # K=4 declared, 3 ops -> must fail
    bad1 = """.block K=4
smul 1 0
srot60
smul 0 1
.regen"""
    try:
        parse_block(bad1)
        print("  FAIL: K=4 with 3 ops did not raise")
        ok = False
    except BlockValidationError as e:
        print(f"  PASS: K=4 with 3 ops rejected ({e})")
    # K=4 declared, 5 ops -> must fail
    bad2 = """.block K=4
smul 1 0
srot60
smul 0 1
smul 2 1
srot60
.regen"""
    try:
        parse_block(bad2)
        print("  FAIL: K=4 with 5 ops did not raise")
        ok = False
    except BlockValidationError as e:
        print(f"  PASS: K=4 with 5 ops rejected ({e})")
    # valid block parses
    good = """.block K=4
smul 1 2
srot60
smul 3 1
smul 0 1
.regen"""
    ops, K = parse_block(good)
    print(f"  PASS: valid K=4 block parsed ({len(ops)} ops)")
    # idempotence on all backends
    for name, bk in (('photonic', PhotonicBackend(2.0)),
                     ('fpga', FpgaReferenceBackend()),
                     ('digital', DigitalSurdBackend())):
        S = (12345, -6789)
        r = regen_idempotent(bk, S)
        if r != S:
            print(f"  FAIL: REGEN not idempotent on {name}: {r} != {S}")
            ok = False
        else:
            print(f"  PASS: REGEN(REGEN(S)) == S on {name}")
    print("  Gate 3 result:", "PASS" if ok else "FAIL")
    return ok


if __name__ == '__main__':
    g1 = gate1()
    g2 = gate2()
    g3 = gate3()
    print()
    print("ALL GATES:", "PASS" if (g1 and g2 and g3) else "FAIL")
