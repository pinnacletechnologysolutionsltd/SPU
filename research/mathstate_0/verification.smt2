; Exact integers: bounds |a|,|b| <= 16; intermediate u multiplication
; has |2a+3b| <= 80 and |a+2b| <= 48, within signed 64 bits.
(set-logic QF_LIA)
(declare-const a Int)
(declare-const b Int)
(define-fun aa () Int (+ (* 2 a) (* 3 b)))
(define-fun bb () Int (+ a (* 2 b)))
(assert (and (<= (- 16) a) (<= a 16) (<= (- 16) b) (<= b 16)))
(push)
(assert (or (< aa (- 80)) (> aa 80) (< bb (- 48)) (> bb 48)
            (distinct (- (* 2 aa) (* 3 bb)) a)
            (distinct (+ (- aa) (* 2 bb)) b)))
(check-sat)
(pop)
; Deliberately wrong inverse coefficient and tighter bound.
(push)
(assert (distinct (- (* 2 aa) (* 2 bb)) a))
(check-sat)
(get-value (a b aa bb))
(pop)
; Abstract final state of two successful writes versus no-op: initialized
; true and status 0 in both cases; numerical equality is checked above.
(push)
(assert (or (not true) (distinct 0 0)
            (distinct (- (* 2 aa) (* 3 bb)) a)
            (distinct (+ (- aa) (* 2 bb)) b)))
(check-sat)
(pop)
; An observer between operations can distinguish the updated tuple.
(push)
(assert (or (distinct aa a) (distinct bb b)))
(check-sat)
(get-value (a b aa bb))
(pop)
