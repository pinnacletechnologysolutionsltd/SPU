#!/usr/bin/env python3
"""
phinary_vm_helpers.py

VM helpers for packed phinary values.
Provides: pack_phinary, unpack_phinary, add_phinary wrapper (calls phinary_ref.add_phinary).
This file loads the existing software/tools/phinary_ref.py golden reference.
"""
from __future__ import annotations
import os
import importlib.util
from typing import Tuple

# Load phinary_ref (golden reference) from the same directory
_this_dir = os.path.dirname(__file__)
_ph_ref_path = os.path.join(_this_dir, 'phinary_ref.py')
if not os.path.exists(_ph_ref_path):
    raise FileNotFoundError(f"phinary_ref.py not found at {_ph_ref_path}")

_spec = importlib.util.spec_from_file_location('phinary_ref', _ph_ref_path)
_ph = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ph)  # type: ignore


def pack_phinary(surd: int, integer: int, width: int = 16, int_bits: int = 8) -> int:
    """Pack surd and integer components into a single packed phinary word.

    surd: upper component (non-negative integer)
    integer: lower INT_BITS component (non-negative integer)
    Returns packed word: (surd << int_bits) | integer
    """
    if int_bits < 0 or width <= int_bits:
        raise ValueError('Invalid width/int_bits')
    surd_mask = (1 << (width - int_bits)) - 1
    int_mask = (1 << int_bits) - 1
    return ((surd & surd_mask) << int_bits) | (integer & int_mask)


def unpack_phinary(packed: int, width: int = 16, int_bits: int = 8) -> Tuple[int, int]:
    """Unpack a packed phinary word into (surd, integer) components.

    Returns (surd, integer)
    """
    int_mask = (1 << int_bits) - 1
    surd_mask = (1 << (width - int_bits)) - 1
    integer = packed & int_mask
    surd = (packed >> int_bits) & surd_mask
    return surd, integer


def add_phinary(packed_a: int, packed_b: int, width: int = 16, int_bits: int = 8,
                laminar_thr: int | None = None, chirality: bool = False,
                void_state: bool = False) -> Tuple[int, bool, bool]:
    """Wrapper around phinary_ref.add_phinary. Returns (out_packed, void_out, overflow).

    Parameters mirror the golden reference. laminar_thr defaults to None -> golden defaults.
    """
    # delegate to the golden reference implementation
    out_packed, void_out, overflow = _ph.add_phinary(
        packed_a, packed_b, width=width, int_bits=int_bits,
        laminar_thr=laminar_thr, chirality=chirality, void_state_in=void_state
    )
    return out_packed, void_out, overflow


# convenience main for quick local checks
if __name__ == '__main__':
    import json
    vec_file = os.path.join(_this_dir, 'phinary_vectors.json')
    if not os.path.exists(vec_file):
        print('No phinary_vectors.json found; nothing to test')
        raise SystemExit(1)
    data = json.load(open(vec_file))
    # run toy vectors
    toy = data.get('toy_4_2', [])
    mismatches = 0
    for v in toy:
        a = int(v['A'])
        b = int(v['B'])
        chir = int(v['chir'])
        exp = int(v['out'])
        out, void, ovf = add_phinary(a, b, width=4, int_bits=2, laminar_thr=10, chirality=bool(chir), void_state=False)
        if out != exp:
            print('MISMATCH', v, '-> got', out)
            mismatches += 1
    if mismatches == 0:
        print('phinary_vm_helpers: self-check OK')
    else:
        print('phinary_vm_helpers: failures', mismatches)
