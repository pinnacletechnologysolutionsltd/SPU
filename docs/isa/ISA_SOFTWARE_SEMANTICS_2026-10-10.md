# Scoped software ISA semantics

Date: 2026-10-10. Status: scoped software tranche qualification PASS; frozen snapshot closed.
Authority: [frozen repair contract](../../spu_strategy/contract_isa_software_semantics_2026-10-10.md).
This software repair leaves REGEN, Surd, WF, RTL and transports unchanged.

## Supported domains and classifications

| Concern | Frozen behavior | Classification / limit |
|---|---|---|
| Operand validation | Reuse existing grammar, supported legacy forms and source rejection before encoding/folding. | Matching for the existing 209 checks; no full ISA qualification implied. |
| Arithmetic | Python retains unbounded integer coefficients. C++ checks signed32 coefficients using signed128 intermediates. | Matching where C++ helper results fit; wider execution unsupported by C++ and signaled OVERFLOW. |
| Ordering / scalar norm | Exact comparisons and norm sign, including signed32 extrema. | Matching in tested domain; C++ widened arithmetic avoids signed64 overflow. |
| C++ failure | Restore scalar/QR banks and Pell steps, PC, retirement count, stack and SNAP counter; set halted and fault_kind; throw. | Matching preservation assertions; unsupported domain and opcode faults distinguished. |
| Scalar raw indices | Reject out-of-range operands on directly indexed scalar handlers before memory access. | Matching tested rejection; legacy wrapping on QR/QLOAD paths remains separate. No global reserved-bit policy change. |
| ROT | Destination-in-place one-step operation. Tracked Pell uses eight stored mantissas plus total step; untracked values multiply by 2+sqrt(3). | Shared coefficient/step representation; Python polarity unsupported in C++. Signed32 Pell-counter exhaustion faults in C++. |
| QROT / QNORM | QROT rotates each component then normalizes. QNORM subtracts the exact ordered Surd minimum. | Existing operation semantics retained; C++ checked helper-domain limits apply. |
| ROTC | Integer coefficients; nearest division with ties away from zero; wide C++ accumulators before final narrowing. | Matching for angles0..5 and fitting results, including aliases and negative thirds. Python angles6..35 unsupported by C++; angles36..63 unsupported by both. |
| Hardware rotor | TDM truncation and tagged deferred representation remain their own surfaces. | Conflicting on nondivisible thirds / distinct representation. No RTL repair or VM/RTL universal parity claim. |
| Fault status | Host fault_kind: UNSUPPORTED, OVERFLOW, INVALID_REGISTER. Reload clears it. | Software diagnostic interface; no hardware FLAGS bits allocated. Other Python extension faults are outside this new status subset. |
| SNAP | Common scalar stability check is nonhalting, preserves registers, counts one failing check and retires. | Matching with QR zero; Python SDF checks and periodic recovery unsupported in C++. |
| Completion | HALT retires once; unsupported and overflow faults do not retire; invalid/out-of-program fetch stops. | Common software behavior. Core instruction acknowledgment and fetch/stack faults remain separate. |
| Warm reload | Replace program and clear PC/steps/halted/fault; retain banks, metadata, stack and snap_failures. | Matching common state. Python-specific auxiliary resets remain existing behavior. |
| Cold reset | Construct a fresh SPUCore. Empty program/stack, zero banks, absent metadata, counters0 and no software fault. | Matching common state; no new reset API and no hardware hydration claim. |

The shared arithmetic subset is a value/metadata contract, not a promise that
every long Python program reproduces C++ state. Python's automatic gasket and
dispatch ticks can alter QR state; C++ does not implement that behavior. Python
polarity, QR tags, SDF, MIN4 and extended rotor catalog support are not inferred
from coefficient parity. JINV metadata differences remain outside this repair.

## Evidence

Before snapshots and SHA-256 hashes are recorded in
[preparation manifest](../../build/isa_software_semantics/preparation_01/before_manifest.json).
The reusable operand files were not modified by this repair. The before hashes
also bind the VM and assembler versions used for the earlier focused slice.

[Independent oracle](../../software/tests/isa_semantics_oracle.py) contains integer
formulas and literal rotor rows without importing implementation arithmetic or
encoders. [Boundary tests](../../software/tests/test_isa_software_semantics.py)
seed poisoned banks, signed32 extrema and alias shapes directly. The C++ harness
uses undefined-behavior sanitization with recovery disabled. Cases classified
unsupported still assert fault preservation; successful results use oracle
expectations rather than treating VM agreement alone as correctness.

Focused results: 76 semantics cases PASS, existing operand checks209 PASS,
literal ISA conformance PASS, folding PASS, canonical control PASS and Python
VM88/0 PASS. These are focused software results. Full qualification and the
mandatory separate Padé build passed for the isolated snapshot; no new silicon result.

One development fixture was corrected: its proposed positive Surd minimum was
invalid while a zero component remained present. Both VMs selected zero. The
replacement fixture removes zero and discriminates full Surd ordering from
real-coefficient-only ordering. Production semantics were not changed for it.

## Qualification closeout

The detached job has exactly one COMPLETE marker and exit 0, completing in
2,168 seconds against the frozen 7,200-second limit. All 18 gate records exit 0:
repository regression 243/0, scoped regression 75/0, focused checks, rotor
traces, mathematical oracles, documentation and the separate 25 MHz Artix-7
100T Padé build. Before/after source-identity gates passed; scoped source hashes
were checked again during review.

[Qualification review](../../build/isa_software_semantics/qualification_01/qualification_review.json)
records the evidence-manifest digest, tested source hashes, gate exits and
separate Padé result. [Runner result](../../build/isa_software_semantics/qualification_01/result.json)
and [Padé log](../../build/isa_software_semantics/qualification_01/gates/artix7.log)
remain distinct evidence. This closes the named software semantics repair for
the frozen snapshot, with the implementation-boundary table above retained as
the compatibility reference. Concurrent live-checkout changes are not qualified
by this result. No Surd/REGEN integrated image or silicon claim follows.
