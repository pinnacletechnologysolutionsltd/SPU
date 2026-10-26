# Scoped ISA conformance review disposition

Date: 2026-10-10. Input: independent engineering review supplied by the user
against the frozen repair packet, source fixtures and qualification snapshot.
This records its assessment; it does not extend its evidence scope.

The supplied review identifies no new concrete counterexample or contradictory
invariant in the scoped repairs. It assesses encoding, folding fixtures, C++
HALT/rejection, HEX source timing and historical lane mapping as matching within
their tested subsets. It retains the conflicting, unsupported and unverified
classifications for unresolved arithmetic and architectural semantics.

Accepted boundaries:

- Source agreement does not establish exhaustive execution correctness.
- Folding fixtures establish selected outputs and Pell metadata, not universal
  equivalence across automatic ticks, SNAP/SDF or all register write effects.
- HEX telemetry preserves 16-bit (B-D,A-D), separate from scalar VM outputs.
- Surd 70..77 are existing optional RTL/assembler instructions; both VMs reject
  them. No new Surd VM support, hardware flash or silicon observation occurred.
- The Padé build result does not qualify an ENABLE_SURD_CPU implementation.
- Overflow, rounding/representation, FLAGS/SNAP, ROT/QROT, MIN4, polynomial
  allocation, invalid indices, reload/reset, flash addresses and core control
  support retain separate policy/architecture decisions.

Two qualifications to the review text:

1. Its statement that directed Surd interpretation is pending is now resolved.
   The completed run reports PASS_DIRECTED_CPU_RTL: 39 failed-retirement
   preservation checks, 17 alias cases and 6 injected engine failures. Kernels
   were not executed; boot/reset, netlist verification and board operation are
   excluded. See [results](../../build/isa_conformance/qualification_01/surd/results.json).
2. C++ ROTC rejects decoded six-bit angles 6..63. Assemblers and execution mask
   the selector; an out-of-range source literal such as 64 can alias 0. The
   review's phrase “angle >=6” must not imply full-width literal validation.
   This remains the documented invalid-encoding policy gap.

The review's absence of an additional operand-count/type finding is not an
exhaustive proof that all malformed inputs are rejected.

Qualification has exactly one COMPLETE marker and all gate exit codes are 0.
Full regression: 243 passed, 0 failed. Scoped regression: 75 passed, 0 failed.
[Detached result](../../build/isa_conformance/qualification_01/result.json)
records 2032 seconds and the frozen 7200-second limit. The documentation audit
reports existing repository findings despite exit 0.

The [frozen review packet](../../build/isa_conformance/review_01/REVIEW_PACKET.md)
and [conformance record](ISA_CONFORMANCE_2026-10-10.md) preserve the supported
subsets and remaining decisions. No production repair beyond the scoped
contract is included in this disposition.
