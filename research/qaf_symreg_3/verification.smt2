; Abstract three-branch join and 3-bit coefficient model. No ISA implementation encoded.
(set-logic QF_BV)
(declare-const f1 Bool) (declare-const f2 Bool) (declare-const f3 Bool)
(declare-const p1 Bool) (declare-const p2 Bool) (declare-const p3 Bool)
(declare-const t1 Bool) (declare-const t2 Bool) (declare-const t3 Bool)
(define-fun universal () Bool
  (and (or f1 f2 f3) (or (not f1) p1) (or (not f2) p2) (or (not f3) p3)))
(define-fun false_on_feasible () Bool
  (or (and f1 (not t1)) (and f2 (not t2)) (and f3 (not t3))))
; Assumption: each branch proof is sound for that branch's proposition.
(assert (=> (and f1 p1) t1)) (assert (=> (and f2 p2) t2)) (assert (=> (and f3 p3) t3))
(assert universal) (assert false_on_feasible)
(check-sat)
; Defective existential join: A proven, B not proven and false.
(reset-assertions)
(assert f1) (assert f2) (assert (not f3)) (assert p1) (assert (not p2))
(assert t1) (assert (not t2))
(assert (or (and f1 p1) (and f2 p2) (and f3 p3)))
(assert false_on_feasible)
(check-sat)
(get-value (f1 f2 p1 p2 t1 t2))
; Different derivations of z=2*conj(x), with coefficients widened to 16 bits.
(reset-assertions)
(declare-const a (_ BitVec 3)) (declare-const b (_ BitVec 3))
(define-fun s ((x (_ BitVec 3))) (_ BitVec 16) ((_ sign_extend 13) x))
(assert (or (distinct (bvmul (_ bv2 16) (s a)) (bvmul (_ bv2 16) (s a)))
            (distinct (bvmul (_ bv2 16) (bvneg (s b))) (bvneg (bvmul (_ bv2 16) (s b))))))
(check-sat)
; Defective branch B omits conjugation: b=1 is a counterexample.
(reset-assertions)
(assert (= b #b001))
(assert (distinct (bvmul (_ bv2 16) (bvneg (s b))) (bvmul (_ bv2 16) (s b))))
(check-sat)
(get-value (b))
; Current binding must still match the identity bound into the historical proof.
(reset-assertions)
(declare-const old (_ BitVec 2))
(define-fun new () (_ BitVec 2) (bvadd old (_ bv1 2)))
(assert (= old new))
(check-sat)
; Defective register-number comparison ignores the changed identity.
(reset-assertions)
(assert (distinct old new))
(check-sat)
(get-value (old new))
