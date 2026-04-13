#!/usr/bin/env python3
"""
phinary_ref.py -- Golden reference implementation for packed phinary addition
Usage: python3 software/tools/phinary_ref.py

Implements the same semantics as chiral_phinary_adder_param.v and the
4-bit toy chiral_phinary_adder.v used in unit tests. Provides a small
self-test that mirrors hardware testbenches.
"""

from typing import Tuple

def add_phinary(surd_A: int, surd_B: int, width: int = 16, int_bits: int = 8,
                laminar_thr: int | None = None, chirality: bool = False,
                void_state_in: bool = False) -> Tuple[int, bool, bool]:
    """Add two packed phinary words. Returns (out_packed, void_out, overflow).

    packed layout: [SURD:W-INT_BITS | INT:INT_BITS]
    """
    if laminar_thr is None:
        laminar_thr = 10
    mask = (1 << width) - 1
    int_mask = (1 << int_bits) - 1
    surd_bits = width - int_bits
    surd_mask = (1 << surd_bits) - 1

    int_a = surd_A & int_mask
    int_b = surd_B & int_mask
    surd_a = (surd_A >> int_bits) & surd_mask
    surd_b = (surd_B >> int_bits) & surd_mask

    int_sum = int_a + int_b
    surd_sum = surd_a + surd_b

    sum_val = (surd_sum << int_bits) + int_sum

    overflow = False
    void_out = void_state_in

    if sum_val > laminar_thr:
        overflow = True
        if not chirality:
            void_out = not void_state_in
            tmp = sum_val - laminar_thr
            out_packed = tmp & mask
        else:
            new_int = (int_sum + 1) & int_mask
            new_surd = surd_sum & surd_mask
            out_packed = ((new_surd << int_bits) | new_int) & mask
    else:
        out_packed = sum_val & mask

    return out_packed, void_out, overflow


# Hardware TB golden model used by chiral_phinary_adder_tb.v
# compute_gold mirrors the Verilog testbench compute_gold task.

def compute_gold_small(a: int, b: int, chir: int, void_in: bool) -> Tuple[int, bool, bool]:
    tb_int_sum = (a & 0x3) + (b & 0x3)
    tb_surd_sum = ((a >> 2) & 0x3) + ((b >> 2) & 0x3)
    tb_sumv = (tb_surd_sum << 2) + tb_int_sum
    if tb_sumv > 10:
        if chir == 0:
            void_out = not void_in
            expected_sum = (tb_sumv - 10) & 0xF
        else:
            void_out = void_in
            expected_sum = (((tb_surd_sum & 0x3) << 2) | ((tb_int_sum + 1) & 0x3)) & 0xF
        overflow = True
    else:
        expected_sum = tb_sumv & 0xF
        void_out = void_in
        overflow = False
    return expected_sum, void_out, overflow


def run_small_tb() -> bool:
    """Run the same vector sequence as chiral_phinary_adder_tb.v."""
    tests = [
        (0b0001, 0b0001, 0),
        (0b0011, 0b0010, 0),
        (0b1111, 0b1111, 0),
        (0b1111, 0b1111, 1),
        (0b0101, 0b1011, 1),
        (0b0010, 0b0010, 0),
    ]
    void_state = False
    all_ok = True
    for idx, (a, b, chir) in enumerate(tests):
        expected_sum, expected_void, expected_ovf = compute_gold_small(a, b, chir, void_state)
        out, void_out, ovf = add_phinary(a, b, width=4, int_bits=2, laminar_thr=0b1010, chirality=bool(chir), void_state_in=void_state)
        ok = (out == expected_sum) and (void_out == expected_void) and (ovf == expected_ovf)
        print(f"T{idx}: A={a:04b} B={b:04b} chir={chir} -> out={out:04b} void={int(void_out)} ovf={int(ovf)}  expected out={expected_sum:04b} void={int(expected_void)} ovf={int(expected_ovf)}  {'OK' if ok else 'FAIL'}")
        if not ok:
            all_ok = False
        # Update void_state according to golden model for sequential tests
        void_state = expected_void
    return all_ok


if __name__ == '__main__':
    ok_small = run_small_tb()
    if ok_small:
        print('\nphinary_ref: SMALL TB PASS')
        raise SystemExit(0)
    else:
        print('\nphinary_ref: SMALL TB FAIL')
        raise SystemExit(2)
