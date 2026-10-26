# SOM RTL repair backlog (separate from RP0a; nothing here is implemented)

Owner direction 2026-10-20: the width discrepancy in `hardware/rtl/core/spu13/spu_som_bmu.v` is a **confirmed correctness
defect** for uploader-valid inputs; it is tracked here and repaired, if at all, by a separate RTL contract. RP0a changes no RTL,
uploader, firmware, simulator or product contract. Original audit: [HALT_RECORD.md](HALT_RECORD.md) (unchanged).

## Defect (evidence: HALT_RECORD.md; reproduced by `rtl_compare.py`)
For signed-18-bit inputs the RTL silently returns wrong distances (no flag) or flags overflow but still emits a truncated value.
In `rtl_compare.py`, 507 of 616 sampled in-domain vectors differ from the exact oracle in the real RTL; all 507 are classified
`RTL_UNSAFE` by the exact C code (and all 109 `RTL_OK` vectors equal the oracle in the real RTL).

## Mismatch classes (each has a test vector)
1. **DIFF** x−w is 19-bit but is passed as `signed [17:0]` (silent wrap, no flag).
2. **TERM** weighted term wraps in the 36-bit ring (silent). Intermediate s_p/s_q wraps are harmless by themselves.
3. **SUM** P is an unsigned 32-bit field and Q a signed 32-bit field; the flag fires on exact P outside [0, 2³²−1] or Q outside
   [−2³¹, 2³¹−1], but a truncated value is still emitted (a flag, not a refusal). Negative P (legal for signed weights) is flagged.
4. **GAP** gap fields are 32-bit modular; exact gap_p < 0 (a legal positive-valued gap) is reported as an unsigned value.
5. **THRESH** the reducer zero-extends the threshold's P.

## Width requirements for exact full-domain operation (derived in FINDINGS.md; not a design)
Δ 19 bits; s_p 39; weighted term P 58 / Q 57 bits signed; four-term P 60, Q 59 bits signed; gap 61/60; the exact order needs
da² vs 3·db² at about 122 bits (a serial comparator over 61-bit operands). A repair must choose between wider datapaths and a
declared refusal outside a named profile (a product decision), and needs a regression, board re-qualification and re-statement of
affected silicon claims. Existing evidence (Iris, features ×1000, unit weights, |Δ| ≲ 10⁴) lies inside the RTL-safe region.
