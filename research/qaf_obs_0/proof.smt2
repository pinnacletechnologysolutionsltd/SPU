; QF_LRA covers all real a,b and hence all rational coefficient pairs.
; Mathematical semantics only: unbounded exact arithmetic, no status/events.
(set-logic QF_LRA)
(declare-const a Real)
(declare-const b Real)
(define-fun c () Real (+ (* 2 a) (* 3 b)))
(define-fun d () Real (+ a (* 2 b)))
; A counterexample to U then inverse U reconstructing a,b.
(push)
(assert (or (not (= (- (* 2 c) (* 3 d)) a))
            (not (= (+ (- c) (* 2 d)) b))))
(check-sat)
(pop)
; Wrong inverse: use +c instead of -c; fails for some input.
(push)
(assert (not (= (+ c (* 2 d)) b)))
(check-sat)
(get-value (a b))
(pop)
