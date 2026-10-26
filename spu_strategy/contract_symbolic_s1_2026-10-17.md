# Engineering Contract: symbolic register S1
Date: 2026-10-17
Status: ACTIVE — bounded software prototype requested by owner
Roles: current agent specifies, implements and audits sequentially.

## Commands and scope
1. Create only `research/symbolic_registers/` and this contract.
2. Store immutable typed VALUE and TRANSFORM objects with store-local handles;
   reserve CONSTRAINT and SOLUTION labels without implementing S2/S3.
3. VALUE is canonical rational Quadray vector. TRANSFORM is a bounded word over
   G3 generators R,r,H (r=R^-1); use execution order left to right.
   compose(a,b) means a after b and stores word(b)+word(a).
4. Reduce only adjacent inverse pairs Rr,rR,HH. Inversion reverses the word and
   inverts each symbol. Identity is the empty word. Do not assert complete
   semantic canonicalization; distinct reduced words can denote equal maps.
5. Implement eight software registers, immutable interned store (128 objects),
   max 64 reduced symbols and max 4096 bits per Fraction numerator/denominator.
   Check intermediate materialized coefficients; fail before destination writes.
   Store has no deletion; exhaustion is explicit. No garbage collector or ABI.
6. Implement load, compose, inverse, materialize and exact semantic equivalence.
   Composition/inversion must perform no coordinate or matrix evaluation.
7. Run `python3 -m unittest discover -s research/symbolic_registers -p 'test_*.py' -v`.
8. Run `python3 -m research.symbolic_registers.demo`.
9. Run `git diff --check -- research/symbolic_registers spu_strategy/contract_symbolic_s1_2026-10-17.md`.
10. Launch `bash research/symbolic_registers/check_repo.sh` via detached runner,
    one attempt, timeout 1800 seconds, new output directory. End turn at launch.

## Acceptance and boundaries
Check symbolic cancellation without evaluation; matrix equivalence and exact
materialization against eager Cartesian execution; noncommuting composition;
round-trips; residual semantic equality beyond syntactic reduction; foreign and
wrong-type handles, register bounds, object/word/bit limits and unchanged
register/store state on failure. Fixed limits are software resource guards,
not a hardware cost guarantee. Halt on failing checks or contradictions.
No binary descriptor allocation, new opcode, RTL, GPU, simulator, learning,
constraint networks or general symbolic algebra. Rational domain only; ROT60
and PELL are not imported across domains. Existing G3 gate COMPLETE/exit 0.
