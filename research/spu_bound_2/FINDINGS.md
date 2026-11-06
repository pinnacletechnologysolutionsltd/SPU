# SPU-BOUND-2: prefix certificates and refusal boundary

**Result: PARTIAL / NO GENERAL REWRITE.** A machine-readable certificate and a
separately coded checker establish exact signed coefficient bounds for a narrow
family of finite boxes and sequences of multiplication by `2 ± √3`. Four
focused tests passed. The certificate does **not** establish an architecturally
legal instruction elimination: refusal and observable dispatch events can differ.
This is exploratory software evidence, not an ISA, RTL, hardware, or release claim.

## Scope and results

Inputs are independent integer boxes, with signed-64-bit coefficients and
initial denominator 1. The candidate operations are SMUL by initialized
`(2,±1,1)` tuples. The producer composes prefix matrices and emits exact extrema,
independent interval bounds, and minimum signed bits for each output coefficient
at every prefix. The checker independently recomputes the recurrence, extrema,
intervals and widths from the inputs and sequence, rejecting altered fields.
The exact endpoint argument depends on independent rectangular integer inputs;
it is not a generic expression prover. Matrix-computation and multiplier product,
sum, control and scratch widths are **not** certified. A 64-bit output bound is
a sufficient no-rescue condition here only under the stated valid-input,
denominator-one, supported-instruction assumptions; it is not a certificate for
general Gen-1 multiplication, all arithmetic stages or normalization.

| Fixture | Exact prefix signed widths (a,b) | Final ordinary interval | Result |
|---|---|---|---|
| [-2,2]²; U,U⁻¹ | (5,4), (3,3) | [-38,38] × [-22,22] | Exact final [-2,2]²; 25 inputs checked |
| [-2,2] × [-1,1]; U,U,U⁻¹,U | (4,4), (6,5), (4,4), (6,5) | [-362,362] × [-209,209] | Exact final [-26,26] × [-15,15]; 15 inputs checked |
| [-2,2]²; U | (5,4) | [-10,10] × [-6,6] | Same as exact: no bound improvement |
| (2⁶³−1,0); U,U⁻¹ | (65,64), (64,1) | singleton final | Mathematical final fits; first SMUL refuses |

`reference_trace` uses the existing independent exact-tuple Gen-1 software
reference in `software/experiments/surd_cpu_stream.py`, with initialized
registers, denominator 1 and valid encodings. It stops the experimental trace at
first refusal; actual subsequent issuance depends on its controller. The `retire`
field is an assumed one-per-issued-instruction accounting based on the earlier
MATHSTATE-0 dispatch trace, not newly measured RTL. Safe fixtures compare all
points with arbitrary-precision evaluation and the tuple reference. The 65-bit
case returns status 2, no write and the unchanged tuple at the first operation;
an identity replacement would succeed without that refusal. For a small safe
cancellation, final tuple and status match an assumed identity, but the two
original writes and retirements are absent. Full dispatch-event equivalence is
therefore false even there. Nor does this study prove that no-op leaves a
nonzero prior status unchanged correctly: it assumes prior status zero.
MATHSTATE-0 documents the separate RTL trace and unresolved observer boundary.

The checker is a second algorithm in the same module, not a verified independent
implementation or external proof assistant. The test suite changes certificate
matrices, bounds, widths, interval data and operation signs and confirms rejection.
It checks JSON round-tripping. It does not prove checker correctness or validate
all malformed JSON. It cannot certify an optimization, architectural equivalence,
first-refusal equivalence for arbitrary inputs, intermediate reads, or preservation
of writes and retirements. The producer can emit an unsafe certificate; validity
means the bounds were checked, **not** that they fit the hardware.

## Exploratory optimized C++ baseline

`baseline.cpp` evaluates U followed by U⁻¹ against manually simplified identity
on the 25 input pairs, then makes one million calls per path. Inputs are always
small, so C++ signed overflow is excluded for these expressions; this is not a
finite-width refusal model. Each pair is checked before timing. GCC 11.4 and
Clang/LLVM 14, `-O3`, x86-64, one sample each:

| Compiler | eager function bytes | identity function bytes | eager ns | identity ns |
|---|---:|---:|---:|---:|
| GCC | 44 | 11 | 4,481,323 | 2,614,872 |
| Clang | 30 | 7 | 5,411,874 | 2,965,096 |

Disassembly shows eight arithmetic `lea`/`add`/`sub` instructions in each eager
function and none in the identity function; both have actual calls from the
benchmark loop. The loop makes one million calls per path, so this corresponds
to eight million versus zero **function-body arithmetic instructions**, not a
hardware performance counter or a total workload operation count. Calls, moves,
loop math and all other instructions are excluded. Sizes are function-symbol
sizes, including return and (GCC) entry instructions, not executable sizes.
Runtimes are single ordered samples on a shared host, include loop overhead and
are noisy. This manual transformation is not an architecturally legal rewrite
under the full dispatch observer, and these observations do not establish a
compiler or SPU speedup. The one-step fixture shows no bounds gain.

Clang initially selected an incomplete GCC 12 installation and failed to find
headers; specifying the installed GCC 11 headers and library path allowed the
comparison. This is a local toolchain workaround, not a tool installation.

## Reproduce

Observed Git HEAD `9fe2cee`; checkout had unrelated dirty/untracked work.
Python 3.10.12; x86-64 GCC 11.4.0 and Ubuntu clang 14.0.0. Per invocation:
30-second wall timeout, 1 GiB virtual memory. Scratch output below is disposable;
no network, FPGA tools or production source modifications.

```sh
mkdir -p /tmp/spu-bound-2-bench
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.spu_bound_2.test_certificate -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.spu_bound_2.certificate)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.spu_bound_2.certificate --emit > /tmp/spu-bound-2-bench/certificate.json)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.spu_bound_2.certificate --verify /tmp/spu-bound-2-bench/certificate.json)
(ulimit -v 1048576; timeout 30s g++ -O3 -std=c++17 research/spu_bound_2/baseline.cpp -o /tmp/spu-bound-2-bench/gcc)
(ulimit -v 1048576; timeout 30s clang++ -O3 -std=c++17 -nostdinc++ -isystem /usr/include/c++/11 -isystem /usr/include/x86_64-linux-gnu/c++/11 -isystem /usr/include/c++/11/backward -L/usr/lib/gcc/x86_64-linux-gnu/11 research/spu_bound_2/baseline.cpp -o /tmp/spu-bound-2-bench/clang)
(ulimit -v 1048576; timeout 30s /tmp/spu-bound-2-bench/gcc)
(ulimit -v 1048576; timeout 30s /tmp/spu-bound-2-bench/clang)
nm -S --size-sort /tmp/spu-bound-2-bench/gcc
nm -S --size-sort /tmp/spu-bound-2-bench/clang
objdump -d --disassemble=eager /tmp/spu-bound-2-bench/gcc
objdump -d --disassemble=algebraic /tmp/spu-bound-2-bench/gcc
objdump -d --disassemble=eager /tmp/spu-bound-2-bench/clang
objdump -d --disassemble=algebraic /tmp/spu-bound-2-bench/clang
```
