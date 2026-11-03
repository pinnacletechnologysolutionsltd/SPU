; Abstract version-binding model, not an encoding of the Python implementation.
; Feasible state: y=conj(old), register overwritten with a different value/version.
(set-logic QF_BV)
(declare-const old_a (_ BitVec 4))
(declare-const old_b (_ BitVec 4))
(declare-const new_a (_ BitVec 4))
(declare-const new_b (_ BitVec 4))
(declare-const old_id (_ BitVec 2))
(define-fun new_id () (_ BitVec 2) (bvadd old_id (_ bv1 2)))
(define-fun s ((x (_ BitVec 4))) (_ BitVec 8) ((_ sign_extend 4) x))
(assert (or (distinct old_a new_a) (distinct old_b new_b)))
; Show the assumptions admit a state.
(check-sat)
; Correct identity-based lookup cannot reuse the historical edge.
(push)
(assert (= old_id new_id))
(assert (or (distinct (s old_a) (s new_a))
            (distinct (bvneg (s old_b)) (bvneg (s new_b)))))
(check-sat)
(pop)
; Defective lookup keys only by unchanged register number: the stale edge is used.
(push)
(assert (or (distinct (s old_a) (s new_a))
            (distinct (bvneg (s old_b)) (bvneg (s new_b)))))
(check-sat)
(get-value (old_id new_id old_a old_b new_a new_b))
(pop)
