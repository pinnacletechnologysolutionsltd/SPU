# I Built a Zero-Drift φ-Arithmetic Co-Processor on a $30 FPGA

**The problem:** Any geometric computation running long enough will eventually
be wrong. Floating-point drift accumulates silently — π approximated, √5
truncated, φ rounded to 52 bits. After a million operations, the result has
drifted by enough to matter. In robotics kinematics, that means the arm misses
its target. In quantum control, it means the syndrome decode picks the wrong
correction.

**The insight:** φ² = φ + 1. That's the golden ratio's defining identity, and
it means multiplication by φ is a single integer add-compare — no multiplier,
no DSP, no approximation. Choose a Lucas prime as modulus (L₁₃ = 521) and you
get deterministic period closure: φ²⁶ ≡ 1 mod 521, so any φ-chain returns to
its exact starting value after 26 steps, forever.

I implemented this as a 242-line Verilog module (`spu13_lucas_mac.v`) targeting
a $30 Tang Primer 25K FPGA. The PSCALE operation (φ-multiply) completes in one
clock cycle at 200 MHz post-route, using zero DSP slices. Over 999,996 mixed
PSCALE/PMUL/PINV operations, the bit pattern returns to seed every time. Zero
drift.

The Python oracle that produces the same result is 10 lines. Run it yourself:

```python
def phi_mul(a, b, mod=521):
    return (b % mod, (a + b) % mod)

def zero_drift_test(steps=1000000):
    period = 26  # φ²⁶ ≡ 1 mod 521
    a, b = 3, 5
    for step in range(1, steps + 1):
        a, b = phi_mul(a, b)
        if step % period == 0: assert (a,b) == (3,5)
    print("PASS")
```

The hardware also implements PHSLK — a rational phase coherence predicate that
checks equality of two φ-weighted fractions by cross multiplication, without
computing a denominator inverse. That primitive maps directly to template-matching
in Fibonacci-anyon braid verification and bosonic QEC syndrome comparison.

Full RTL, testbenches, and oracles are open-source (CC0). The paper is on arXiv.

This isn't a simulation — it's a bitstream that runs on a $30 FPGA you can buy today. The same Verilog that produced these numbers is in the repository. No cloud account, no proprietary toolchain, no NDAs. Run the Python oracle in 10 seconds. Synthesize the RTL yourself. The result will be the same, because the arithmetic is exact.

The repo also contains the SPU-13's broader architecture: a deterministic rational-field processor for geometric computation, with silicon-proven SOM classification, RPLU v2 Padé evaluation over A₃₁, and an in-progress SU(3) extension for complex unitary group arithmetic. All open, all CC0.

---

*SPU-13 Project — [github.com/spu13](https://github.com/spu13)*
*Paper: arXiv:... (link when published)*
