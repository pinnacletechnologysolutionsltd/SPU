**Status:** COMPLETE — measured 2026-08-25. Supersedes
`contract_gpu_mult42_isolation_probe_2026-08-25.md`.

# Corrected Shared-Multiplier Probe: 35×17, not 42×42

## Why the original probe was wrong
External review of the architecture contract caught it: the 42×42 sizing
was derived from `A_z/B_z/C_z`'s *output* width (~41-45 bits, measured
from the depth-v2 oracle) rather than the actual operand widths feeding
the final-scale multiply. The real widest multiply is `|Sa|` (dot-
product sum, ~35-bit magnitude from three ~32-bit terms) `× y1`
(reciprocal output, ~17-bit magnitude) — **35×17, not 42×42.** Confused
a multiply's output register with its input operands.

## Corrected result
`build_25k_spu13_mult35_probe.sh` — magnitude-only (unsigned) 35×17,
matching the actual design (sign extracted and reapplied separately,
outside the shared multiplier, per the architecture contract's §1
correction to magnitude-only handling):

| Resource | Used | Total | % |
|---|---|---|---|
| LUT4 | **3,532** | 23,040 | **15.3%** |
| ALU | 96 | 17,280 | 0.6% |
| DFF | 115 | 23,040 | 0.5% |
| DSP | 0 | 28 each | 0% |

Max frequency (final line): 63.12 MHz. Routes clean.

**~3.2× cheaper than the wrong 42×42 measurement (11,259 LUT4).**
Combined with the raster baseline: 1,317 + 3,532 = **4,849 LUT4 = 21.0%
used, 18,191 LUT4 (79.0%) headroom** — much closer to the original
"comfortable margin" picture than the 45.4%-headroom alarm the wrong
sizing produced. Still not the full 94.3% raster-only figure, since the
LOD/barrel-shifter, 256-entry ROM, and FSM control logic remain
unmeasured (see `contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md`
§6, updated).

## Lesson
Deriving a shared resource's size from a *consumer's* register width
instead of the *specific operation's* actual operand widths is exactly
the kind of error the halt-and-flag review process exists to catch
before it costs real synthesis time or, worse, gets built into RTL.
Caught here by external review before any of the three real modules
were written — the mult42 probe's LUT/time cost was real but bounded;
building `spu_shared_mult42.v` at the wrong width and discovering it
during integration would have cost much more.
